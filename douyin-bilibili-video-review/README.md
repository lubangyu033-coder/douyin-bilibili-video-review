# 抖音与 B 站视频审查 / Douyin & Bilibili Video Review

用于 Codex 和 DeepSeek Harness 的可移植技能：审查用户给出的视频链接或本地媒体，提取带时间点的资料，并说明画面、字幕、口播各自覆盖到哪里。

**v2 补齐了可选本地处理脚本、依赖、参数、模型路径、失败处理和 Harness 配置说明。** 页面审查安装后即可使用现有工具；本地处理需要另行准备 Python 依赖和可选 ASR 模型。

- [中文使用说明](中文使用说明.md)：怎样提问、选择范围、读懂结果。
- [安装指南](INSTALL.md)：复制位置、目录结构、可选本地依赖。
- [本地处理与参数](references/local-processing.md)：doctor / check / subs / asr / all。
- [DeepSeek Harness 配置](references/deepseek-harness.md)：发现目录、优先级、调用开关和近期 Search/Fetch 更新。
- [能力与验证记录](capabilities.md)：本次验证与 DSH 提供的单机报告边界。

## 能做什么

| 当前环境 | 可进行的工作 | 需要说明的边界 |
|---|---|---|
| 网页搜索 / Fetch | 页面实际可读的标题、简介、字幕或摘要 | 成功取网页不代表取到视频/音轨 |
| 浏览器 / 截图 / 媒体预览 | 播放器关键帧、屏幕文字和可访问音频 | 工具、账号、地区、平台都会影响可读范围 |
| 已准备好的本地 Python 环境 | 媒体探测、候选字幕带、带时间点字幕墙 | 字幕墙不是 OCR，也不证明每条字幕被保留 |
| 本地 CTranslate2 Whisper 模型 | CPU int8 ASR 与时间段候选 | 转写可能出错，不证明完成画面审查 |

## 快速开始

将仓库内容放进技能根目录下的 douyin-bilibili-video-review 文件夹，确保直接包含 SKILL.md。完整路径见 [安装指南](INSTALL.md)。

Codex 可引用 `$douyin-bilibili-video-review`；已启用技能子系统的 Harness 可输入 `/douyin-bilibili-video-review`，随后贴链接并说明希望提取什么。

本地工具先运行（将 python 换成已准备好的解释器路径）：

~~~sh
python scripts/vread.py doctor
python scripts/vread.py check "/path/to/video.mp4"
~~~

工具只处理现有本地文件，不联网取视频、安装依赖或下载模型。宿主允许且用户授权的媒体获取可使用该环境已有工具；相关权限仍由当前宿主决定。

## 包含与不包含

包含技能指令、可选本地处理源码、依赖声明及说明。未包含用户视频、逐字稿、cookie、API 密钥、Python 环境、模型权重或下载二进制。普通 DeepSeek 网页版/手机 App 不能仅靠复制这些文件获得 Harness 的本地能力。

尚未选择许可证；第三方依赖和模型分别受各自许可证约束。

A portable review workflow with an optional offline media helper. It records actual evidence coverage instead of assuming every host has the same video tools.
