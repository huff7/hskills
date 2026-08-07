# 第三方 Skill 署名与许可（ATTRIBUTION）

本仓库在 `skills/` 下打包了部分**第三方开源 Skill**，供「时序 · AI 提效与搞钱」系列视频观众一键安装使用。
各 Skill 的版权与许可归**原作者所有**，本仓库仅做分发与中文说明，不主张其版权。

---

## 1. openclaw-video-toolkit

- **来源仓库**：[digitalsamba/claude-code-video-toolkit](https://github.com/digitalsamba/claude-code-video-toolkit)（原 owner 为 `khushil`，仓库已迁移/更名，旧地址仍可 clone）
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

## 3. ffmpeg-usage

- **来源**：本仓库原创（huff7）
- **上游 Skill 路径**：`skills/ffmpeg-usage/`
- **许可**：Apache License 2.0（与仓库根 `LICENSE` 一致）
- **内容说明**：ffmpeg / ffprobe 音视频处理命令配方库（安装、信息查询、截图抽帧、GIF、音视频分离/提取/替换、转码封装、缩放裁剪旋转、拼接、加字幕/水印/边框、变速混音、录制，及实战组合配方）。基础命令整理自 ffmpeg 官方文档（ffmpeg.org）与公开教程，实战配方为本仓库二次编排。
- **对应视频能力**：转码助手（Day4 资料包 5 号）的底层命令层，亦可作为 1–8 号能力的通用命令支撑。
- **使用前提**：需本地已安装 `ffmpeg` 与 `ffprobe`（见 `references/ffmpeg-cheatsheet.md` §0 安装指引）。技能本身不含二进制，仅提供命令配方。

---

## 许可与署名要求

- 第三方 Skill 的 MIT 许可允许自由使用、修改、再分发（含闭源/商用），但**修改后分发须保留原始 LICENSE 与署名**。
- 本仓库根目录 `LICENSE` 为 Apache 2.0，仅适用于「个人 AI 工作台搭建流程」等**本仓库原创内容**；第三方 Skill 各自遵循其上游 MIT 许可。
- 使用前请务必阅读对应上游仓库的 `README` 与 `LICENSE`。
