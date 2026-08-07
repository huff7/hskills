---
name: ai-video-skills-collection
description: 一站式安装并管理「用 AI 做视频」所需的 8 个开源 Skill（智能粗剪 / 口播精修 / 批量处理 / 自动字幕 / 转码助手 / 品牌包装 / 动态片头 / 一键切片）。当用户说"帮我装好做视频的 AI 技能""搭建视频剪辑 Agent 工具链""我要做短视频需要哪些 Skill""把那 8 个剪辑 Skill 装上"时使用。触发后逐个安装并汇报每个的安装状态。
agent_created: true
---

# AI 视频技能合集（一键安装 + 速查）

你是一个**安装编排器**。当用户想搭建"用 AI 做视频"的工具链时，按下面的清单帮他**逐个装好这 8 个开源 Skill**，并汇报每一个的安装结果。你**不自己实现**剪辑功能，只负责把正确的 Skill 装到用户的 Agent 里，并告诉他怎么用。

## 适用前提

- 用户已装有某个 Agent 工具（**WorkBuddy / Claude Code / Codex** 均可），你本人也是其中一个。
- 本地建议已装 `ffmpeg` + `ffprobe`（`ffmpeg-usage` 技能里有安装指引；多个 Skill 运行时也依赖它）。
- 少数 Skill 需要 API Key（如 Deepgram / ElevenLabs）。安装时若提示缺 Key，告诉用户去对应上游仓库 README 申请，**不要卡住其余安装**——把缺 Key 的标成"需手动"继续往下装。

## 你的安装清单（逐个执行，装完立即汇报 成功 / 失败 / 需手动）

1. `npx skills add browser-use/video-use` — ① 智能粗剪
2. `npx skills add Vibetool/talking-head-video` — ② 口播精修
3. `npx skills add amywork777/video-editing-pipeline` — ③ 批量处理
4. `npx skills add kwindla/skill-caption-clip` — ④ 自动字幕
5. 安装 `ffmpeg-usage`（**本仓库原创，只能从 hskills 获取**）：
   ```bash
   git clone https://github.com/huff7/hskills /tmp/hskills && cp -R /tmp/hskills/skills/ffmpeg-usage <你的skills目录>
   ```
   - WorkBuddy 的 skills 目录：`~/.workbuddy/skills/`
   - Claude Code 的 skills 目录：`~/.claude/skills/`
6. `npx skills add op7418/Video-Wrapper-Skills` — ⑥ 品牌包装
7. `npx skills add heygen-com/hyperframes --full-depth` — ⑦ 动态片头（特效 / 动效层）
   `npx skills add remotion-dev/skills` — ⑦ 动态片头（片头片尾 / 数据动效）
8. `npx skills add AgriciDaniel/claude-shorts` — ⑧ 一键切片 ⭐

## 兜底规则（某个 `npx skills add` 装不上时）

`git clone https://github.com/<owner>/<repo>`，把仓库里的 skill 文件夹复制到 Agent 的 skills 目录。各仓库里 skill 文件夹的具体路径见 `references/skills-catalog.md` 的「上游 skill 路径」列。

## 完成后必须做

- 输出一张**状态表**：技能名 / 来源仓库 / 安装状态 / 备注（缺什么 Key、要不要手动）。
- 给一张**速查表**，让用户知道"想做 X 就跟 Agent 说哪句话"——见 `references/skills-catalog.md` 的「跟 Agent 说这句话」列。
- 提醒用户：这 8 个外部 Skill 的许可归**原作者**，使用前读对应上游 LICENSE；本仓库**不捆绑**它们的源码，全部由用户各自的 Agent 从上游安装。

## 不要做的事

- **不要**把外部 Skill 的源码复制进 `huff7/hskills` 仓库（保持仓库只放原创内容 + 本安装编排 Skill）。
- **不要**替用户瞎改系统配置；装不上就如实汇报 + 给兜底命令。

## 参考资料

- `references/skills-catalog.md` — 8 个技能的完整对照表（能力 / 仓库 / 安装命令 / 跟 Agent 说的话 / 上游 skill 路径 / 许可）。
- `references/install-prompt.txt` — 一段可直接复制给用户、让其粘贴给任意 Agent 的**一键安装 Prompt**。
