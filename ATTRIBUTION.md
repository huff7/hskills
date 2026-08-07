# 第三方 Skill 署名与许可（ATTRIBUTION）

本仓库在 `skills/` 下打包了部分**第三方开源 Skill**，供「时序 · AI 提效与搞钱」系列视频观众一键安装使用。
各 Skill 的版权与许可归**原作者所有**，本仓库仅做分发与中文说明，不主张其版权。

---

## 1. openclaw-video-toolkit

- **来源仓库**：[khushil/claude-code-video-toolkit](https://github.com/khushil/claude-code-video-toolkit)
- **上游 Skill 路径**：`skills/openclaw-video-toolkit/`
- **许可**：MIT License — Copyright (c) 2024 Digital Samba
- **对应视频能力**：智能粗剪、口播精修、批量处理、自动字幕、转码助手、品牌包装、动态片头（即 Day4 资料包中的 1–7 号）
- **使用前提**：该 Skill 是一个「指挥层」，本身不含工具二进制，需要先在本地按上游仓库说明装好完整 toolkit 工作区（默认路径 `~/.openclaw/workspace/claude-code-video-toolkit`），并具备 `node` / `python3` / `ffmpeg` / `npm`。语音、配图、音乐、数字人等依赖云端 GPU（Modal / RunPod）。
- **原许可文件**：请见上游仓库 `LICENSE`（MIT）。

## 2. claude-shorts

- **来源仓库**：[AgriciDaniel/claude-shorts](https://github.com/AgriciDaniel/claude-shorts)
- **上游 Skill 路径**：仓库根（已整体放入本仓库 `skills/claude-shorts/`）
- **许可**：MIT License — Copyright (c) 2026 Daniel Agrici
- **对应视频能力**：一键切片（即 Day4 资料包中的 8 号 ⭐）
- **使用前提**：需要 `node` / `python3` / `ffmpeg`，以及 Remotion 渲染环境（已随 Skill 内置 `remotion/`）。首次使用按 `install.sh` / `setup.sh` 安装依赖。
- **原许可文件**：本仓库 `skills/claude-shorts/LICENSE`（已随包带入，MIT）。

---

## 许可与署名要求

- 第三方 Skill 的 MIT 许可允许自由使用、修改、再分发（含闭源/商用），但**修改后分发须保留原始 LICENSE 与署名**。
- 本仓库根目录 `LICENSE` 为 Apache 2.0，仅适用于「个人 AI 工作台搭建流程」等**本仓库原创内容**；第三方 Skill 各自遵循其上游 MIT 许可。
- 使用前请务必阅读对应上游仓库的 `README` 与 `LICENSE`。
