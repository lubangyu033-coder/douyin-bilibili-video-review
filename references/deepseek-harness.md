# DeepSeek Harness 技能配置

核查日期：2026-10-20。依据下列官方上游文档；实际支持范围取决于安装版本、当前 profile 和启用的插件。普通 DeepSeek 网页/手机端不等同于 Harness。

## 发现路径与覆盖

本技能保持标准 name / description 两个 frontmatter 字段。新版 filesystem 提供方识别技能根目录直接子项：<name>/SKILL.md 或 <name>.md；不会递归查找多层嵌套的 SKILL.md。

同一作用域层内，同名技能按以下顺序优先（靠前者覆盖靠后者）；不同 preset 层还可能有各自覆盖：

1. <projectRoot>/.dsh/skills
2. <projectRoot>/.agents/skills
3. 提供方配置 customSkillDirs
4. <dshHome>/skills，默认 $DSH_HOME 或 ~/.dsh 下的 skills
5. <agentsHome>/skills，默认 $DSH_AGENTS_HOME 或 ~/.agents 下的 skills
6. 已配置的 bundledSkillDir

projectRoot 是最近的 .git 祖先目录；没有 .git 时使用会话 cwd。仓库子目录不一定是项目根。复制后找不到或仍读到旧版时，检查是否存在同名的高优先级副本。

## 加载与调用

当前官方实现由技能注册表 dsh-skill、本地提供方 dsh-skill-filesystem 和加载消费者 dsh-tool-skill 配合工作。部署/当前 profile 必须实际启用相应能力；单独复制文件不替代插件配置。

用户输入中的 `/douyin-bilibili-video-review` 在技能可供用户调用时，可由宿主注入其正文。模型可见目录仅含允许模型调用的技能，再由 skill 工具加载正文；名字出现在列表不等于模型已经加载或执行。

| 可选 frontmatter | 用途 | 本包选择 |
|---|---|---|
| whenToUse | 额外路由说明 | 不填写，description 已说明用途 |
| metadata | 可选对象元数据 | 不要求 |
| disable-model-invocation: true | 从模型目录/加载工具中隐藏 | 不填写，默认允许模型调用 |
| user-invocable: false | 关闭用户调用入口 | 不填写，默认允许用户调用 |

调用开关使用精确的 kebab-case 键与 YAML 布尔值 true / false，避免旧驼峰字段。无效值可能使整个技能被跳过并只在宿主日志中警告。这里的 Harness 扩展不被当作所有宿主通用的设置。

## 高级提供方配置

一般用户使用默认路径即可；以下属于 Harness 宿主/插件配置，不是写进本技能 frontmatter 的参数。配置入口与保存格式依发行版/profile 而异，按当前应用的插件设置或官方配置目录操作。

| 字段 | 官方默认/作用 |
|---|---|
| includeDefaultRoots | true；false 时默认项目/用户根不再扫描 |
| customSkillDirs | []；追加自定义技能根目录 |
| dshHome | $DSH_HOME 或 ~/.dsh |
| agentsHome | $DSH_AGENTS_HOME 或 ~/.agents |
| watch | true；监听技能目录变化 |
| bundledSkillDir | 可选，部署提供的技能根 |
| catalogDescriptionMaxLength | 加载器目录描述长度上限，默认 500 |

当前提供方监听新增、删除、重命名及 manifest 变动，并在后续模型步骤更新目录；正文重新加载时重新读文件。references / scripts / assets 内修改不属于目录变化事件。旧版或禁用 watch 的部署可能需要重新加载或新建会话；以实际目录与加载结果确认。

## 与视频审查相关的新功能

官方 v0.2.1-rc.2（预发布，2026-10-17）加入 DeepSeek Search 与 Fetch API 适配，可在网页搜索设置开启。这对取得页面文字有帮助，不能据此宣称能够读取视频帧、音轨或在所有账号/地区正常播放。技能加载、网页读取、本地解码与 ASR 是独立能力，分别检查。

## 官方来源

- [Filesystem 提供方](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.md)
- [技能目录与加载器](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/tool-skill/README.md)
- [技能子系统](https://deepseek-harness.github.io/deepseek-harness/en/reference/subsystems/skills)
- [v0.2.1-rc.2 发布说明](https://github.com/deepseek-ai/deepseek-harness/releases/tag/dsh-v0.2.1-rc.2)
