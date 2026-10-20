# Douyin & Bilibili Video Review

A portable local skill for Codex and DeepSeek Harness. It reviews publicly accessible Douyin and Bilibili video pages through the browser and media tools available in the current environment.

本 Skill 帮助 Codex 从抖音、哔哩哔哩页面提取可复核的内容摘要和资料要点，并记录来源类型、时间点与验证边界。

## Features

- Records page-visible title, creator, date, duration, and access status.
- Summarizes content visible in sampled frames and readable captions, with timestamps.
- Separates creator captions, automatic captions, platform-generated summaries, page text, comments, direct observations, and inference.
- Flags claims about speed, accuracy, income, acceptance rates, and other outcomes as unverified unless checked against reliable sources.
- States when audio, captions, or parts of the page could not be reviewed.

## Requirements and limits

The skill uses only browser, computer-control, or media-preview capabilities available to the target Codex or Harness session. Platform access and playback can vary by account, region, browser, and device.

It does not download remote videos, bypass login or access controls, or claim a complete review when it only sampled selected timestamps. When the player is muted or audio is unavailable, spoken content is left unverified. A platform-generated chapter summary is labeled as such, not presented as a transcript.

## Install

Copy the whole `douyin-bilibili-video-review` directory into one of these locations:

- Codex personal skills: `%CODEX_HOME%\skills\` or `%USERPROFILE%\.codex\skills\`
- Codex project skills: `<project>/.agents/skills/`
- DeepSeek Harness user skills: `%DSH_HOME%\skills\` or `%USERPROFILE%\.dsh\skills\`; on other supported systems, `~/.dsh/skills/`

For detailed steps and macOS/Linux paths, see [INSTALL.md](INSTALL.md).

## Use

Provide one or more Douyin or Bilibili links and ask the assistant to inspect the videos and extract the key points. In Codex, invoke `$douyin-bilibili-video-review`; in DeepSeek Harness, invoke `/douyin-bilibili-video-review` when local skills are supported.

The skill supplies review instructions only. It does not add a browser, screenshot, audio, or video-parsing tool. Results depend on the tools and page access available in that session.

## Repository contents

- `SKILL.md` — shared skill instructions and evidence-handling rules.
- `INSTALL.md` — installation steps for another Codex environment.
- `README.md` — project overview and usage.

To make a standalone GitHub repository, use the contents of this directory as the repository root. Review the selected files and repository visibility before publishing.

## License

No license is included yet. Choose and add a license before publishing if you want to grant reuse rights. Publishing this skill does not grant rights to videos or other third-party material it may review.

