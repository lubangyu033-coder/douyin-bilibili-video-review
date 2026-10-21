# 可选本地媒体处理

本页适用于已有、可合法使用的本地媒体。随包脚本改编自 DSH 提供的 vread.py；所有路径由参数指定，不依赖作者的盘符、账号或 Harness 私有运行时。脚本自身不获取远程视频。

## 开始前

按 [INSTALL.md](../INSTALL.md) 建立可选环境。将下文 python 替换为所建环境的解释器路径；从技能文件夹执行，或为 scripts/vread.py 提供绝对路径。没有 shell/文件能力的宿主仍可使用页面审查。

~~~sh
python scripts/vread.py doctor
python scripts/vread.py check "/path/to/video.mp4"
python scripts/vread.py check "/path/to/video.mp4" -o "/path/to/new-check"
python scripts/vread.py subs "/path/to/video.mp4" -o "/path/to/new-subs" --band 800,1050 --rows 10
python scripts/vread.py asr "/path/to/video.mp4" -o "/path/to/new-asr" --model-dir "/path/to/models/small" --threads 4 --lang zh --prompt "Zotero, CSV"
python scripts/vread.py all "/path/to/video.mp4" -o "/path/to/new-all" --model-dir "/path/to/models/small"
~~~

所有模式仅接受本地文件。check 可不输出文件；带 -o 时保存候选字幕带预览和 manifest。subs / asr / all 必须使用新的或空输出目录，保护已有结果。all 没给 --model-dir 时只做字幕墙，manifest 明确标注 ASR skipped。

## 参数

| 参数 | 默认 | 含义 |
|---|---|---|
| mode | 必填 | doctor 环境；check 探测；subs 字幕墙；asr 转写；all 两者 |
| src | 本地路径 | 可含空格/中文；doctor 无需输入 |
| -o / --outdir | 处理时必填 | 新的或空输出目录 |
| --band y0,y1 | 启发式自动候选 | 原始像素纵向裁剪范围，0 ≤ y0 < y1 ≤ 高度 |
| --rows | 10 | 每页字幕墙条数，1–50 |
| --mad | 3.0 | 缩小灰度条的平均绝对差阈值；调高减少条目，可能漏字幕 |
| --min-gap | 0.35 秒 | 候选条目最小间隔；短于此的变化可能被漏掉 |
| --sheet-width | 1280 | 单条最大宽度，320–4096，避免高分辨率墙占用过多内存 |
| --model-dir | 无 | 已有本地 CT2 模型目录；不自动下载、不按模型名回退 |
| --threads | 4 | CPU 转写线程数；依据本机资源调整 |
| --beam | 5 | ASR 束搜索宽度；增加不保证准确率提高 |
| --lang | zh | 识别语言；auto 自动判断 |
| --prompt | 空 | 领域术语提示，不填猜测的整段台词 |
| --vad | 关闭 | 启用语音活动过滤，可能漏掉轻声或背景中的语音 |

## 结果与覆盖

~~~text
out/
  manifest.json
  band-preview.jpg          # 有视频且执行字幕探测时
  subs/sheet_0001.png       # 图像；未执行 OCR
  subs/rows.json            # 候选条目时间、页号、行号
  asr/segments.jsonl        # 逐段写入；失败时可能只有部分
  asr/segments.json         # 转写完成后
  asr/transcript.md         # 本地识别草稿
~~~

manifest 记录输入 SHA-256、环境版本、参数、处理状态和各阶段完成/跳过/失败。字幕扫描可记录解码到 EOF 及保留条目；这不证明字幕识别完整，更不证明人工完整看过视频。ASR 时间以媒体视频起点为参考，包含实际解码的音频偏移；转码、片头或非连续音轨可能导致与网页播放器时间不一致，引用前抽查对齐。

字幕带使用原候选的下方区域、边缘与时间变化启发式。固定 40–120px 字高、0.78H 搜索带不能保证覆盖所有分辨率或版式。先看 band-preview.jpg，再抽查 2–3 页字幕墙（不足则全查）及其对应原帧，覆盖开头/中间/末尾；检查字幕上下边缘是否截字或混入界面小字。截字时加宽，混入界面时调整范围/位置，必要时手动 --band 重跑；记录最终带值、页数和实际读过的页数。字幕在顶部、两处同时出现或位置变化时，手动指定范围或分段另处理。动画背景会产生假条目；墙内文字仍需视觉模型或人工读取，并回查原帧。

## 故障处理

- No module named av/numpy/PIL：检查正在执行的解释器与 pip 是否属于同一环境，运行 doctor。
- 模型路径报错：指向真正的 CT2 文件夹，而不是原始 Whisper 权重或只有下载链接的目录。
- metadata_errors 异常：DSH 报告 faster-whisper 1.2.1 与 PyAV 19.0.1 的字符串路径解码出现此问题。helper 直接重采样后传 float32 数组，并 flush 重采样尾部；不据此断言所有版本均有同一故障。
- 没音轨：manifest 标明 ASR 跳过；不能补猜口播。
- 音频时间戳不连续：停止并报告，改用可保留间隙的解码流程，不静默拼接成错误时间轴。
- 行数暴涨/漏行：检查裁剪预览、调整 --mad / --min-gap / --band；阈值是取舍，不是准确率保证。
- 中途失败：读取 manifest 和保留下来的阶段产物，只报告真正完成的部分；重新运行使用新目录。
- 模型慢/内存紧：先用较小的已准备模型、较少线程。字幕墙按页写盘；ASR 仍会把单条音轨解码为内存数组，长片宜由用户选定区间另处理。

## 媒体获取的边界

可使用用户提供的文件；如任务另有合法且符合宿主规则的获取通道，先核对目标 ID、作者与时长。下载成功、文件带音轨或位率最高，都不证明拿到了目标片或最佳识别素材。页面展示与本地媒体处理分别记录覆盖；来源只记录稳定页面 URL、取得时间与必要的脱敏字段，不留存短期签名媒体地址、cookie 或完整原始接口响应。

DSH 提供的抖音实验是本机 Edge 正常页面响应中取得目标条目并下载；其代码写死路径、记录原始响应/短期 URL，且浏览器行为依赖平台。该路线没有作为通用获取脚本随包发布。接口失败时停止，不承诺“唯一有效路线”，不自动换凭据、签名或规避工具访问限制。

上游方法参考：[faster-whisper](https://github.com/SYSTRAN/faster-whisper)、[PyAV AudioResampler](https://pyav.org/docs/stable/api/audio.html)。
