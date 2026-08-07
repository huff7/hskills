# AI 视频技能合集 · 完整对照表

8 个「用 AI 做视频」的开源 Skill 一览。安装命令见 `SKILL.md`；这里补充每个能力的**原属仓库、跟 Agent 说的话、上游 skill 文件夹路径（兜底用）、许可**。

| # | 能力 | 来源仓库（点开看原仓库） | 安装命令 | 跟 Agent 说这句话 | 上游 skill 路径（兜底 `git clone` 后复制此文件夹） | 许可 |
|---|------|------------------------|----------|------------------|------------------------------------------|------|
| 1 | 智能粗剪（自动找镜头、剪片段）| [browser-use/video-use](https://github.com/browser-use/video-use) | `npx skills add browser-use/video-use` | "帮我把这段视频自动粗剪，去掉停顿和废话" | 仓库根 `SKILL.md`（注册式）| MIT |
| 2 | 口播精修（去口头禅、调节奏）| [Vibetool/talking-head-video](https://github.com/Vibetool/talking-head-video) | `npx skills add Vibetool/talking-head-video` | "精修这段口播，去掉 um/啊，节奏调快一点" | 仓库根 `SKILL.md` | MIT |
| 3 | 批量处理（一堆视频统一规则粗剪）| [amywork777/video-editing-pipeline](https://github.com/amywork777/video-editing-pipeline) | `npx skills add amywork777/video-editing-pipeline` | "把 inbox 里所有 mp4 按统一规则粗剪" | `skills/video-editing-pipeline/skill.md` | 未声明（默认保留所有权利，分发/商用前确认）|
| 4 | 自动字幕（语音 → 带样式字幕）| [kwindla/skill-caption-clip](https://github.com/kwindla/skill-caption-clip) | `npx skills add kwindla/skill-caption-clip` | "给这个视频加中文字幕，粗体描边" | 仓库根 `SKILL.md` | MIT |
| 5 | 转码助手（合并/转码/抽帧，ffmpeg）| [huff7/hskills · ffmpeg-usage](https://github.com/huff7/hskills)（**本仓库原创**）| `git clone https://github.com/huff7/hskills /tmp/hskills && cp -R /tmp/hskills/skills/hskill-ffmpeg-usage ~/.workbuddy/skills/` | "用 ffmpeg 把 a、b 横屏并排拼成一段" | `skills/hskill-ffmpeg-usage/` | Apache 2.0（原创）|
| 6 | 品牌包装（边框/角标/花字）| [op7418/Video-Wrapper-Skills](https://github.com/op7418/Video-Wrapper-Skills) | `npx skills add op7418/Video-Wrapper-Skills` | "加星辰灰蓝边框 + 右上角 Logo + 花字" | 仓库根 `SKILL.md` | MIT |
| 7 | 动态片头（片头片尾/特效）| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) + [remotion-dev/skills](https://github.com/remotion-dev/skills) | `npx skills add heygen-com/hyperframes --full-depth` 和 `npx skills add remotion-dev/skills` | "做个 3 秒科技感片头，中间出 Logo" | hyperframes 仓库根 `SKILL.md`；remotion-dev/skills 内含多个 skill 文件夹 | 见上游仓库 |
| 8 | 一键切片 ⭐（长视频拆成短视频）| [AgriciDaniel/claude-shorts](https://github.com/AgriciDaniel/claude-shorts) | `npx skills add AgriciDaniel/claude-shorts` | "把我的长视频拆成 3 条抖音短视频" | 仓库根 `SKILL.md` | MIT |

> 标 ⭐ 的 `一键切片` 最实用——拍一条长视频，自动帮你拆成好几条能发平台的短视频。

## 使用前提小抄

- **ffmpeg / ffprobe**：能力 1–8 大多依赖本地已装 `ffmpeg`。装法见 `ffmpeg-usage` 技能的 `references/ffmpeg-cheatsheet.md` §0。
- **API Key**：能力 4（字幕）常需 Deepgram Key；能力 1（粗剪转写）可能需 ElevenLabs Key。缺 Key 时该 Skill 装得上、用不了，属"需手动"，去上游 README 申请即可。
- **路径差异**：WorkBuddy 用 `~/.workbuddy/skills/`；Claude Code 用 `~/.claude/skills/`。兜底复制时按工具选对应目录。
