# 第三方 Skill 署名与许可（ATTRIBUTION）

本仓库**只打包原创内容**（`hskill-personal-ai-workbench-builder`、`hskill-ffmpeg-usage`、`hskill-ai-video-skills-collection`）。

「用 AI 做视频」系列视频中提到的 8 个视频剪辑 Skill **不复制进本仓库**——它们由用户各自的 Agent
通过 `npx skills add` / `git clone` 从**原作者仓库**安装，由一个原创编排 Skill
`ai-video-skills-collection` 统一驱动。这样做是为了：保持仓库轻量、始终从上游拉取最新版、并尊重各作者的许可。

> 各外部 Skill 的版权与许可归**原作者所有**，使用前请阅读对应上游仓库的 `README` 与 `LICENSE`。

---

## 一、本仓库原创内容

### 1.1 hskill-ffmpeg-usage（转码助手底层命令层）
- **来源**：本仓库原创（huff7）
- **许可**：Apache License 2.0（与仓库根 `LICENSE` 一致）
- **内容**：ffmpeg / ffprobe 音视频处理命令配方库（安装、信息查询、截图抽帧、GIF、音视频分离/提取/替换、转码封装、缩放裁剪旋转、拼接、加字幕/水印/边框、变速混音、录制，及实战组合配方）。基础命令整理自 ffmpeg 官方文档（ffmpeg.org）与公开教程，实战配方为本仓库二次编排。
- **对应能力**：转码助手（视频能力 5 号）的底层命令层，亦可作为 1–8 号能力的通用命令支撑。
- **使用前提**：需本地已安装 `ffmpeg` 与 `ffprobe`（见 `references/ffmpeg-cheatsheet.md` §0）。

### 1.2 hskill-ai-video-skills-collection（安装编排器）
- **来源**：本仓库原创（huff7）
- **许可**：Apache License 2.0
- **内容**：一个"安装编排" Skill。触发后逐个安装「用 AI 做视频」所需的 8 个开源 Skill（见下表），并汇报每个的安装状态；附完整速查表与一键安装 Prompt（`references/`）。
- **性质**：**不捆绑任何外部 Skill 源码**，仅引用上游仓库地址与安装命令。

---

## 二、引用的外部视频 Skill（未捆绑，由用户各自从上游安装）

| # | 能力 | 来源仓库 | 许可 | 安装命令 |
|---|------|---------|------|----------|
| 1 | 智能粗剪 | [browser-use/video-use](https://github.com/browser-use/video-use) | MIT（Browser Use）| `npx skills add browser-use/video-use` |
| 2 | 口播精修 | [Vibetool/talking-head-video](https://github.com/Vibetool/talking-head-video) | MIT（Vibetool）| `npx skills add Vibetool/talking-head-video` |
| 3 | 批量处理 | [amywork777/video-editing-pipeline](https://github.com/amywork777/video-editing-pipeline) | **未声明**（默认保留所有权利，分发/商用前需联系原作者 `amywork777` 确认）| `npx skills add amywork777/video-editing-pipeline` |
| 4 | 自动字幕 | [kwindla/skill-caption-clip](https://github.com/kwindla/skill-caption-clip) | MIT（kwindla）| `npx skills add kwindla/skill-caption-clip` |
| 6 | 品牌包装 | [op7418/Video-Wrapper-Skills](https://github.com/op7418/Video-Wrapper-Skills) | MIT（op7418）| `npx skills add op7418/Video-Wrapper-Skills` |
| 7 | 动态片头 | [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) + [remotion-dev/skills](https://github.com/remotion-dev/skills) | 见上游仓库 | `npx skills add heygen-com/hyperframes --full-depth` / `npx skills add remotion-dev/skills` |
| 8 | 一键切片 ⭐ | [AgriciDaniel/claude-shorts](https://github.com/AgriciDaniel/claude-shorts) | MIT（Daniel Agrici）| `npx skills add AgriciDaniel/claude-shorts` |

> 完整对照（含「跟 Agent 说这句话」话术与 `git clone` 兜底路径）见 `hskill-ai-video-skills-collection/references/skills-catalog.md`。

---

## 三、许可与署名要求

- 本仓库根目录 `LICENSE` 为 **Apache 2.0**，仅适用于「hskill-personal-ai-workbench-builder」「hskill-ffmpeg-usage」「hskill-ai-video-skills-collection」等**本仓库原创内容**。
- 引用的外部 Skill 各自遵循其上游许可（多为 MIT）。MIT 允许自由使用、修改、再分发（含闭源/商用），但**修改后分发须保留原始 LICENSE 与署名**。
- `video-editing-pipeline` 无显式许可，**再分发/商用前须取得原作者授权**。
- 使用前请务必阅读对应上游仓库的 `README` 与 `LICENSE`。
