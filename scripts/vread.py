"""Portable local-media helper, adapted from the user's DSH vread.py candidate.
No network retrieval, model download, browser automation, or import-time writes.
"""
import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import sys
import time

VERSION = "2.0.0"

def dump(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def doctor():
    packages = {}
    for package in ("av", "numpy", "Pillow", "faster-whisper", "ctranslate2"):
        try:
            packages[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            packages[package] = None
    return {"helper_version": VERSION, "python": platform.python_version(),
            "packages": packages, "network": "not used"}

def open_media(path):
    import av
    return av.open(str(path), options={"protocol_whitelist": "file,pipe"})

def probe(path):
    import av
    with open_media(path) as c:
        v = c.streams.video[0] if c.streams.video else None
        origin = (float(v.start_time * v.time_base)
                  if v and v.start_time is not None and v.time_base
                  else float(c.start_time or 0) / 1e6)
        duration = (float(v.duration * v.time_base)
                    if v and v.duration is not None and v.time_base
                    else float(c.duration or 0) / 1e6)
        return {"width": v.codec_context.width if v else 0,
                "height": v.codec_context.height if v else 0,
                "fps": float(v.average_rate) if v and v.average_rate else None,
                "duration_s": duration, "duration": duration,
                "timeline_origin_s": origin,
                "has_audio": bool(c.streams.audio),
                "size_bytes": Path(path).stat().st_size}

def detect_band(path, n=32):
    """定位烧录字幕带。

    判据 = 「跨帧变化大」×「行内边缘密度高」（文字比画面更"碎"），
    并且只在画面下方 22% 内搜索；这是候选启发式，顶部/移动字幕需人工指定。
    """
    import av, numpy as np
    info = probe(path)
    H, W = info["height"], info["width"]
    dur = max(info["duration"], 1.0)
    y_start = int(H * 0.78)
    x0, x1 = int(W * 0.18), int(W * 0.82)          # 只取画面中段：烧录字幕居中
    frames = []
    with open_media(path) as c:
        for i in range(n):
            t = info["timeline_origin_s"] + dur * (i + 0.5) / n
            try:
                c.seek(int(t * 1_000_000))
            except Exception:
                continue
            for f in c.decode(video=0):
                if f.time is None or float(f.time) < t:
                    continue
                img = f.to_ndarray(format="gray")[y_start:H, x0:x1]
                frames.append(img[:, ::3].astype(np.float32))
                break
    if len(frames) < 3:
        return int(H * 0.86), int(H * 0.97)
    stack = np.stack(frames)                       # (n, h, w)
    time_std = stack.std(axis=(0, 2))              # 每行跨帧波动
    edge = np.abs(np.diff(stack, axis=2)).mean(axis=(0, 2))   # 每行水平梯度
    ks = np.ones(5) / 5.0
    e_s = np.convolve(edge, ks, mode="same")
    t_s = np.convolve(time_std, ks, mode="same")
    if e_s.max() <= 1e-6:
        return int(H * 0.86), int(H * 0.97)

    # 把「有文字的行」聚成块，块的**高度**是区分字幕与界面小字的关键：
    # 本机样本的字幕字高约 40–120px、界面小字约 20–30px；非通用范围。
    mask = e_s > 0.45 * e_s.max()
    blocks, i = [], 0
    while i < len(mask):
        if mask[i]:
            j = i
            gap = 0
            k = i
            while k + 1 < len(mask):
                if mask[k + 1]:
                    j = k + 1
                    gap = 0
                else:
                    gap += 1
                    if gap > 6:
                        break
                k += 1
            if j - i >= 12:                        # 太薄的行段直接丢弃
                blocks.append((i, j))
            i = k + 1
        else:
            i += 1

    def score(b):
        a, c = b
        hgt = c - a + 1
        cy = (a + c) / 2.0 + y_start
        return hgt * (float(t_s[a:c + 1].mean()) ** 0.5) * (1.0 + 0.6 * cy / H)

    if not blocks:
        return int(H * 0.86), int(H * 0.97)
    a, b = max(blocks, key=score)
    y0 = y_start + a - 12
    y1 = y_start + b + 13
    max_h = int(H * 0.20)
    if y1 - y0 > max_h:
        c0 = (y0 + y1) // 2
        y0, y1 = c0 - max_h // 2, c0 + max_h // 2
    height = max(y1 - y0, int(H * 0.10))           # 留足行高，避免切掉字的上下边缘
    c0 = (y0 + y1) // 2
    y0, y1 = c0 - height // 2 - 6, c0 + height // 2 + 6
    return max(0, y0), min(H, y1)



def preview(path, outdir, band):
    import av
    from PIL import ImageDraw
    with open_media(path) as c:
        frame = next(c.decode(video=0))
        image = frame.to_image()
    ImageDraw.Draw(image).rectangle((0, band[0], image.width - 1, band[1] - 1),
                                    outline="red", width=max(2, image.width // 300))
    image.thumbnail((1280, 1280))
    image.save(outdir / "band-preview.jpg")
    # A single preview is only a crop aid; inspect other positions when layout changes.

def sheets(path, outdir, info, band, args):
    import av
    import numpy as np
    from PIL import Image, ImageDraw
    directory = outdir / "subs"
    directory.mkdir()
    chunk, previous, last_keep = [], None, -float("inf")
    records, frame_count, missing_pts, sheet_count = [], 0, 0, 0
    first, last = None, None
    y0, y1 = band

    def flush():
        nonlocal sheet_count
        if not chunk:
            return
        sheet_count += 1
        w, h = chunk[0][1].size
        sheet = Image.new("RGB", (w + 90, h * len(chunk)), "black")
        draw = ImageDraw.Draw(sheet)
        for row, (t, image) in enumerate(chunk):
            sheet.paste(image, (90, row * h))
            draw.text((4, row * h + 4), f"{int(t//60):02}:{t%60:05.2f}", fill="red")
        sheet.save(directory / f"sheet_{sheet_count:04}.png")
        chunk.clear()

    with open_media(path) as c:
        for frame in c.decode(video=0):
            frame_count += 1
            if frame.time is None:
                missing_pts += 1
                continue
            t = float(frame.time) - info["timeline_origin_s"]
            first = t if first is None else first
            last = t
            if t - last_keep < args.min_gap:
                continue
            image = frame.to_image().crop((0, y0, info["width"], y1))
            gray = np.asarray(image.convert("L").resize((128, 48)), dtype=np.float32)
            if previous is not None and float(np.abs(gray - previous).mean()) < args.mad:
                continue
            previous, last_keep = gray, t
            image.thumbnail((args.sheet_width, max(1, y1-y0)))
            records.append({"t": round(t, 3), "sheet": sheet_count + 1,
                            "row": len(chunk) + 1})
            chunk.append((t, image))
            if len(chunk) >= args.rows:
                flush()
    flush()
    dump(directory / "rows.json", records)
    return {"status": "completed", "decoded_frames": frame_count,
            "frames_without_timestamps": missing_pts, "decoded_to_eof": True,
            "first_frame_s": first, "last_frame_s": last,
            "retained_strips": len(records), "sheets": sheet_count,
            "meaning": "visual-change candidates, not OCR or confirmed subtitle sentences",
            "human_visual_review": "not performed by this script"}

def load_audio(path, origin):
    import av
    import numpy as np
    resampler = av.audio.resampler.AudioResampler(format="s16", layout="mono", rate=16000)
    chunks, offset, expected = [], None, None

    def append(frame):
        nonlocal offset, expected
        if frame.time is None:
            raise ValueError("Audio timestamps unavailable; alignment cannot be established.")
        t = float(frame.time)
        if offset is None:
            offset = t - origin
        if expected is not None and abs(t - expected) > 0.1:
            raise ValueError("Discontinuous audio timestamps; use a timeline-aware decoder.")
        chunks.append(frame.to_ndarray().reshape(-1))
        expected = t + frame.samples / 16000.0

    with open_media(path) as c:
        if not c.streams.audio:
            raise ValueError("No audio stream.")
        for frame in c.decode(c.streams.audio[0]):
            for output in resampler.resample(frame):
                append(output)
        for output in resampler.resample(None):
            append(output)
    if not chunks:
        raise ValueError("No decoded audio samples.")
    return np.concatenate(chunks).astype(np.float32) / 32768.0, offset

def asr(path, outdir, info, args):
    from faster_whisper import WhisperModel
    audio, offset = load_audio(path, info["timeline_origin_s"])
    model = WhisperModel(str(Path(args.model_dir).resolve()), device="cpu",
                         compute_type="int8", cpu_threads=args.threads,
                         local_files_only=True)
    started = time.monotonic()
    segments, language = model.transcribe(
        audio, language=None if args.lang == "auto" else args.lang,
        beam_size=args.beam, initial_prompt=args.prompt or None,
        condition_on_previous_text=False, vad_filter=args.vad)
    directory = outdir / "asr"
    directory.mkdir()
    records = []
    with (directory / "segments.jsonl").open("w", encoding="utf-8") as stream:
        for segment in segments:
            row = {"start": round(segment.start + offset, 3),
                   "end": round(segment.end + offset, 3),
                   "text": segment.text.strip()}
            records.append(row)
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
            stream.flush()
    dump(directory / "segments.json", records)
    (directory / "transcript.md").write_text(
        "# Local ASR draft — unverified recognition\n\n" +
        "\n".join(f'[{s["start"]:.3f}–{s["end"]:.3f}s] {s["text"]}' for s in records),
        encoding="utf-8")
    return {"status": "completed", "audio_decoded_s": len(audio) / 16000,
            "audio_offset_s": offset, "elapsed_s": time.monotonic() - started,
            "segments": len(records), "language": language.language,
            "recognition_accuracy": "not independently verified",
            "visual_coverage": "none established by ASR"}

def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("doctor", "check", "subs", "asr", "all"))
    parser.add_argument("src", nargs="?", help="Existing local media file; URLs are rejected")
    parser.add_argument("-o", "--outdir", help="New or empty output directory")
    parser.add_argument("--band", help="Manual vertical crop y0,y1 in source pixels")
    parser.add_argument("--rows", type=int, default=10)
    parser.add_argument("--mad", type=float, default=3.0)
    parser.add_argument("--min-gap", type=float, default=0.35)
    parser.add_argument("--sheet-width", type=int, default=1280)
    parser.add_argument("--model-dir", help="Existing CTranslate2 model directory; never fetched")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--beam", type=int, default=5)
    parser.add_argument("--lang", default="zh", help="Language code or auto")
    parser.add_argument("--prompt", default="", help="Domain terms only; no guessed transcript")
    parser.add_argument("--vad", action="store_true", help="Enable VAD; may omit quiet speech")
    args = parser.parse_args()
    if args.mode == "doctor":
        print(json.dumps(doctor(), ensure_ascii=False, indent=2))
        return
    if not args.src or "://" in args.src:
        parser.error("Provide an existing local file. URL retrieval is not part of this helper.")
    path = Path(args.src).expanduser().resolve()
    if not path.is_file():
        parser.error("Input file does not exist.")
    if not 1 <= args.rows <= 50 or not 320 <= args.sheet_width <= 4096:
        parser.error("rows must be 1..50; sheet-width must be 320..4096.")
    if (not math.isfinite(args.mad) or not math.isfinite(args.min_gap)
            or args.mad <= 0 or args.min_gap <= 0 or args.threads < 1 or args.beam < 1):
        parser.error("mad, min-gap, threads, and beam must be positive.")
    if args.mode == "asr" and not args.model_dir:
        parser.error("asr requires --model-dir pointing to a preinstalled model.")
    if args.model_dir:
        model = Path(args.model_dir).expanduser().resolve()
        if not all((model / f).is_file() for f in ("config.json", "model.bin", "tokenizer.json")):
            parser.error("Model directory needs config.json, model.bin, tokenizer.json.")
        args.model_dir = str(model)
    if args.mode != "check" and not args.outdir:
        parser.error("Processing requires -o with a new or empty output directory.")
    outdir = Path(args.outdir).expanduser().resolve() if args.outdir else None
    if outdir and outdir.exists() and (not outdir.is_dir() or any(outdir.iterdir())):
        parser.error("Output must be a new or empty directory; existing results are not overwritten.")

    manifest = {"helper_version": VERSION, "status": "running", "environment": doctor(),
                "parameters": vars(args), "source_name": path.name,
                "source_sha256": None, "stages": {}}
    try:
        info = probe(path)
        band = None
        if args.band:
            values = args.band.split(",")
            if len(values) != 2:
                raise ValueError("band must contain exactly y0,y1.")
            band = tuple(map(int, values))
            if not (0 <= band[0] < band[1] <= info["height"]):
                raise ValueError("band must satisfy 0 <= y0 < y1 <= source height.")
        if args.mode in ("subs", "all") and not info["width"]:
            raise ValueError("Subtitle-sheet processing requires a video stream.")
        if info["width"] and args.mode in ("check", "subs", "all"):
            band = band or detect_band(str(path))
        manifest["media"] = info
        manifest["candidate_band"] = band
        if outdir:
            outdir.mkdir(parents=True, exist_ok=True)
            with path.open("rb") as source:
                manifest["source_sha256"] = hashlib.file_digest(source, "sha256").hexdigest()
            dump(outdir / "manifest.json", manifest)
            if band:
                preview(path, outdir, band)
        if args.mode in ("subs", "all"):
            manifest["stages"]["subtitles"] = {"status": "running"}
            dump(outdir / "manifest.json", manifest)
            manifest["stages"]["subtitles"] = sheets(path, outdir, info, band, args)
        if args.mode in ("asr", "all"):
            if not info["has_audio"] or not args.model_dir:
                manifest["stages"]["asr"] = {
                    "status": "skipped", "reason": "no audio" if not info["has_audio"] else "no model-dir"}
            else:
                manifest["stages"]["asr"] = {"status": "running"}
                dump(outdir / "manifest.json", manifest)
                manifest["stages"]["asr"] = asr(path, outdir, info, args)
        manifest["status"] = "completed"
        if outdir:
            dump(outdir / "manifest.json", manifest)
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
    except Exception as error:
        manifest["status"] = "failed"
        manifest["error"] = f"{type(error).__name__}: {error}"
        for stage in manifest["stages"].values():
            if stage.get("status") == "running":
                stage["status"] = "failed"
        if outdir and outdir.is_dir():
            dump(outdir / "manifest.json", manifest)
        print(manifest["error"], file=sys.stderr)
        raise SystemExit(1)

if __name__ == "__main__":
    main()
