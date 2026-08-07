---
name: ffmpeg-usage
description: "ffmpeg / ffprobe 音视频处理命令速查与实战配方。覆盖：信息查询、截图与抽帧、GIF、音视频分离/提取/替换、转码封装、缩放裁剪旋转、拼接、加字幕/水印/边框、变速混音、录屏录制。当用户需要对视频或音频做命令行处理（截图、抽帧做封面、提取音频、格式转换、剪裁、合并、加字幕、生成 GIF、转码）时使用；适用于 Claude Code / Codex / WorkBuddy 等任意对话式 Agent。技能本身不含二进制，仅提供命令配方与选型指引。"
agent_created: true
license: Apache-2.0
author: huff7
---

# ffmpeg 音视频处理技能

给对话式 Agent（Claude Code / Codex / WorkBuddy 等）用的 ffmpeg 命令配方库。
你不需要替用户记住参数，按任务在 `references/ffmpeg-cheatsheet.md` 里找对应配方即可。

## 何时使用

- 用户要「截图 / 抽帧 / 做封面 / 导出某个时间点画面」
- 用户要「把视频转成 GIF / 图片序列 / 图片合成视频」
- 用户要「提取音频 / 去掉声音 / 替换背景音乐 / 混音」
- 用户要「转码 / 换格式（mp4→mov/webm/...）/ 封装合并音视频」
- 用户要「缩放 / 裁剪 / 旋转 / 加黑边」
- 用户要「把几段视频拼成一段 / 把长视频按段落合并」
- 用户要「加字幕（烧录）/ 加水印 Logo / 加边框角标」
- 用户要「变速 / 静音 / 调音量 / 录制摄像头或 RTSP 流」
- 用户问「ffmpeg 怎么装 / 某个参数什么意思」

## 前置：确认环境

```bash
ffmpeg -version && ffprobe -version
```

未安装时：

```bash
# macOS
brew install ffmpeg
# Ubuntu / Debian
sudo apt update && sudo apt install ffmpeg
# Windows (winget)
winget install Gyan.FFmpeg
# Windows (choco)
choco install ffmpeg
```

> 版本差异：本技能配方在 ffmpeg 3.x–7.x 通用；个别滤镜（如 `subtitles`）需编译时带 `--enable-libass`，主流发行版默认已带。

## 使用约定（务必遵守，避免静默失败）

1. **先 `ffprobe` 看参数再处理**：不知道分辨率/码率/编码时，先用信息查询配方拿到真实数值，再填命令。
2. **`-y` 直接覆盖、`-n` 不覆盖**：批量脚本里默认用 `-y`（但会无声覆盖旧文件，注意备份）。
3. **无损用 `-c copy`；加滤镜必须重编码**：`-vf` / `-af` / `scale` / `crop` / `overlay` 等任意滤镜都会触发重编码，需指定 `-c:v libx264`（视频）与 `-c:a aac`（音频）。
4. **`-ss` 位置影响速度与精度**：
   - 放在 `-i` **之前**（输入选项）→ 快速定位（seek），适合抽帧/裁剪起点，但精确帧可能略偏；
   - 放在 `-i` **之后**（输出选项）→ 逐帧解码到该点，精确但慢。
5. **路径含空格必须加引号**：`"my video.mp4"`。
6. **拼接前片段参数必须一致**（分辨率、编码、帧率、像素格式），否则 `concat` 失败或花屏。
7. **缩放保持比例用 `-1`**：`-vf scale=1280:-1`（宽 1280，高自动）。
8. **导出通用成片**：`-c:v libx264 -preset slow -crf 18 -c:a aac -b:a 192k -pix_fmt yuv420p`（`-pix_fmt yuv420p` 保证浏览器/手机兼容）。

## 命令配方索引

完整命令 + 注释见 **`references/ffmpeg-cheatsheet.md`**，按任务取用：

| 任务 | 章节 |
|------|------|
| 装 ffmpeg / 查版本 | §0 |
| 查视频信息（ffprobe） | §1 |
| 选项速查（-i/-ss/-t/-s/-vcodec…） | §2 |
| 截图 / 抽帧 / 做封面 | §3 |
| GIF / 图片序列互转 | §4 |
| 分离 / 提取 / 替换 音视频 | §5 |
| 转码 / 封装 / 格式转换 | §6 |
| 缩放 / 裁剪 / 旋转 | §7 |
| 拼接多段 | §8 |
| 加字幕 / 水印 / 边框 | §9 |
| 变速 / 静音 / 混音 / 音量 | §10 |
| 录制 RTSP / 摄像头 | §11 |
| 实战组合（封面生成、1080p 导出等） | §12 |

## 最小可用配方（直接给，不用翻文档）

```bash
# 1) 抽一帧做封面（第 3 秒，高质量）
ffmpeg -ss 3 -i input.mp4 -frames:v 1 -q:v 2 cover.jpg

# 2) 提取音频为 mp3
ffmpeg -i input.mp4 -vn -c:a libmp3lame -q:a 2 audio.mp3

# 3) 转成 1080p 横屏成片（通用兼容）
ffmpeg -i input.mp4 -vf scale=1920:1080 -c:v libx264 -preset slow -crf 18 -c:a aac -b:a 192k -pix_fmt yuv420p out.mp4

# 4) 无损剪一段（不重编码，快）
ffmpeg -ss 00:00:10 -to 00:00:30 -i input.mp4 -c copy clip.mp4

# 5) 加硬字幕（烧录，需 .srt）
ffmpeg -i input.mp4 -vf "subtitles=sub.zh.srt" -c:a copy out.mp4
```

## 常见坑

- **抽帧画面糊/偏色**：加 `-q:v 2`（低值=高质量 JPEG）；指定像素格式 `-pix_fmt yuv420p`。
- **`-c copy` 和 `-vf` 不能同用**：要滤镜就必须重编码（去掉 `-c copy`）。
- **拼接报错 `moov atom not found` / 花屏**：输入片段编码不一致，先统一转成相同参数再拼。
- **GIF 太大/太卡**：限制尺寸与帧率：`scale=480:-1,fps=15`，或先降分辨率。
- **字幕中文乱码**：确保 `.srt` 为 UTF-8，且 ffmpeg 编译带 `libass`；特殊字体需指定 `subtitles=sub.srt:force_style='FontName=Noto Sans CJK SC'`。
- **`-ss` 在 `-i` 前后差异**：见上方「使用约定 4」。
