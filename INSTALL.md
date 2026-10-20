# 安装到 Codex 或 DeepSeek Harness

本包不依赖 API 密钥或额外脚本。安装时保留目录名 `douyin-bilibili-video-review`，确保 `SKILL.md` 位于该目录根部。此文件使用 `name` 和 `description` YAML frontmatter，可供 Codex 和 DeepSeek Harness 的本地 skill 目录发现。

## Codex

- **个人级（推荐）：** 将整个 `douyin-bilibili-video-review` 文件夹复制到 `%CODEX_HOME%\skills\`；若目标机器没有设置 `CODEX_HOME`，复制到 `%USERPROFILE%\.codex\skills\`。
- **项目级：** 将整个文件夹复制到目标项目的 `.agents\skills\` 目录。项目级安装只对该项目生效。

## DeepSeek Harness

- **用户级：** 将整个文件夹复制到 `%DSH_HOME%\skills\`；若未设置 `DSH_HOME`，使用 `%USERPROFILE%\.dsh\skills\`。
- **项目级：** 将整个文件夹复制到目标项目的 `.dsh\skills\`，或 `.agents\skills\`。
- Harness 的本地 skill 提供方启用时会监视这些目录；在对话中可用 `/douyin-bilibili-video-review` 调用。若技能未出现在列表中，检查当前 Harness profile 是否启用了 filesystem skill provider 和模型 skill 工具。

macOS/Linux 下对应用户目录通常为 `$CODEX_HOME/skills/`、`~/.codex/skills/` 或 `~/.dsh/skills/`；项目级目录为 `<project>/.agents/skills/` 或 `<project>/.dsh/skills/`。

本 skill 只提供审查流程，不会安装浏览器、视频解码器或视频模型。DeepSeek API 文档说明了图像输入以及网页 Search/Fetch 接口；这不代表 Harness 当前会话一定能读取视频流或视频帧。若 Harness 无法播放视频或查看视频帧，就请用户提供字幕、逐字稿或截图，不能声称完成了视频内容识别。参见 [Vision](https://api-docs.deepseek.com/guides/vision/) 与 [Search & Fetch](https://api-docs.deepseek.com/guides/search/)。

