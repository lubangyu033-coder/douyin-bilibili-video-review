# 安装与可选依赖

## 1. 安装技能文件

从 GitHub 下载仓库 ZIP 并解压，或复制整个仓库目录。将最内层直接包含 SKILL.md 的目录命名为 douyin-bilibili-video-review，放入下列任一技能根目录。不要再套一层同名文件夹。

~~~text
<技能根目录>/
  douyin-bilibili-video-review/
    SKILL.md
    scripts/vread.py
    references/local-processing.md
    references/deepseek-harness.md
    ...
~~~

| 宿主与范围 | Windows | macOS/Linux |
|---|---|---|
| Codex 个人级 | %CODEX_HOME%\skills；未设置则 %USERPROFILE%\.codex\skills | $CODEX_HOME/skills；未设置则 ~/.codex/skills |
| Codex 项目级 | <项目>\.agents\skills | <项目>/.agents/skills |
| Harness 个人级 | %DSH_HOME%\skills；未设置则 %USERPROFILE%\.dsh\skills | $DSH_HOME/skills；未设置则 ~/.dsh/skills |
| Harness 项目级 | <项目根>\.dsh\skills 或 .agents\skills | <项目根>/.dsh/skills 或 .agents/skills |

Harness 还支持共享 ~/.agents/skills、自定义目录和同名技能覆盖；详见 [Harness 配置](references/deepseek-harness.md)。不要把“技能已被发现”与“浏览器/音视频工具已准备好”混为一谈。

Codex 使用 `$douyin-bilibili-video-review`，Harness 使用 `/douyin-bilibili-video-review`。若没出现，先检查目录深度、frontmatter 和当前项目；Harness 还要检查当前 profile 的技能提供方与加载器。

## 2. 选择需要的配置

| 用途 | 必需 | 不必安装 |
|---|---|---|
| 页面审查 | 当前会话已有的网页/浏览器/媒体能力 | Python、本地 ASR 模型 |
| 本地探测与字幕墙 | Python 3.11+；requirements-core.txt 中的包 | ASR 模型、单独的 ffmpeg 命令行 |
| 本地 ASR | 上述依赖、requirements-asr.txt、本地 CT2 模型目录 | GPU、CUDA、API 密钥 |
| 获取或合并远程媒体 | 当前宿主允许且已授权的获取工具；工具自身可能需要 ffmpeg | 本包不自动提供获取服务 |

本地 helper 使用 PyAV 的解码库，不调用 ffmpeg CLI。yt-dlp 合并等外部流程可能另外需要 ffmpeg；两者不能混淆。

## 3. 可选：建立本地 Python 环境

以下是用户自行选择安装本地工具时执行的命令；仅安装页面技能无需执行。先进入下载的仓库目录，确认使用自己的 Python 3.11+。

Windows PowerShell：

~~~powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-core.txt
.\.venv\Scripts\python.exe scripts/vread.py doctor
~~~

macOS/Linux：

~~~sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-core.txt
.venv/bin/python scripts/vread.py doctor
~~~

需要 ASR 时，用同一解释器将 requirements-core.txt 换成 requirements-asr.txt 再安装。依赖会联网下载；不要求更改系统执行策略、管理员权限或全局 Python。缺少 python 命令时先选择/安装自己的 Python，避免借用文档作者机器的路径。

## 4. 可选：准备本地 ASR 模型

使用 faster-whisper 兼容的 CTranslate2 模型目录，至少包含 config.json、model.bin、tokenizer.json。该 helper 通过 --model-dir 显式读取，并设置 local_files_only；缺少模型时直接报错。

如决定从网络准备模型，先核对模型来源、许可证、所需空间和版本。上游提供 [Systran/faster-whisper-small](https://huggingface.co/Systran/faster-whisper-small)；可由用户自行下载，或明确授权后用环境已有下载工具获取。ModelScope 社区转换版与上游不是同一发布来源；速度与可用性随网络变化。记录所选仓库、revision 和文件哈希，不使用通用的“最快镜像”承诺。

完整命令、输出与故障排查见 [本地处理说明](references/local-processing.md)。
