# ffmpeg 命令速查（完整配方）

本文件是 `ffmpeg-usage` 技能的完整命令参考。每条都可直接复制使用，按需替换 `input.mp4` / `output.*` 等占位名。
所有命令默认已安装 `ffmpeg` 与 `ffprobe`（见 §0）。

---

## 0. 安装与版本

```bash
# 官网下载（含各平台静态构建）
# http://ffmpeg.org/download.html

# 包管理器安装
brew install ffmpeg                       # macOS
sudo apt update && sudo apt install ffmpeg  # Ubuntu / Debian
winget install Gyan.FFmpeg               # Windows (winget)
choco install ffmpeg                     # Windows (choco)

# 查看版本（确认可用）
ffmpeg -version
```

> 本文示例在 ffmpeg 3.x–7.x 通用。写作时常用稳定版如 `ffmpeg-3.1.5`；新版本命令完全兼容。

---

## 1. 信息查询（ffprobe）

```bash
# 最常用：输出 JSON 格式的全部信息（格式 + 每个流）
ffprobe -v quiet -print_format json -show_format -show_streams input.mp4

# 只看法频流分辨率/编码
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,codec_name,r_frame_rate -of csv=p=0 input.mp4

# 只看时长
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 input.mp4
```

---

## 2. 选项速查

### 2.1 基本语法

```
ffmpeg [options] [[infile options] -i infile]... {[outfile options] outfile}...
```

### 2.2 常用选项（信息类）

```bash
ffmpeg -version     # 显示版本信息
ffmpeg -formats     # 显示所有有效的封装格式
ffmpeg -decoders    # 显示所有有效解码器
ffmpeg -encoders    # 显示所有有效的编码器
ffmpeg -bsfs        # 显示有效的数据流滤镜（bitstream filters）
ffmpeg -pix_fmts    # 显示有效的像素格式
```

### 2.3 主要选项

```
-f fmt (input|output)      指定输入/输出文件格式（通常可凭扩展名自动识别）
-i filename (input)        指定输入文件
-y (global)                自动覆盖输出文件
-n (global)                不覆盖；输出已存在则立即退出
-t duration (input|output) 限制输入/输出的时长；hh:mm:ss[.xxx] 或秒数
                            -to 与 -t 互斥，-t 优先级更高
-to time_stop (output)     写入到 time_stop 时间点后停止
-fs limit_size (output)    输出文件大小上限（单位：字节）
-ss time_off (input|output) 指定开始位置（秒或 hh:mm:ss）
```

### 2.4 视频选项

```
-vframes number (output)   设置输出帧数
-r rate (input|output)     设置帧率（Hz）
-s size (input|output)     设置帧尺寸，格式 WxH
-aspect aspect (output)    显示宽高比，如 4:3 / 16:9 / 1.333
-vcodec codec (output)     设置视频编码器（如 libx264 / copy）
```

### 2.5 音频选项

```
-aframes number (output)   设置输出音频帧数
-ar rate (input|output)    设置音频采样率（Hz）
-aq quality (output)       设置音频品质（VBR）
-ac channels (input|output) 设置音频通道数
-af filtergraph (output)   对音频使用滤镜图
```

---

## 3. 截图与抽帧（含做封面）

```bash
# 指定时间点截一张图（第 1 秒，mjpeg 格式，指定尺寸）
ffmpeg -i input_file -y -f mjpeg -ss 1 -t 0.001 -s widthxheight output_file.jpg

# 每 1 秒截一张图（out1.jpg, out2.jpg ...）
ffmpeg -i input.mp4 -f image2 -vf fps=fps=1 out%d.jpg

# 每 20 秒截一张图
ffmpeg -i input.mp4 -f image2 -vf fps=fps=1/20 out%d.jpg

# 抽单帧做封面（第 3 秒，高质量 JPEG）
ffmpeg -ss 3 -i input.mp4 -frames:v 1 -q:v 2 cover.jpg

# 抽某时间点的精确帧（输出放 -i 后，逐帧解码更准）
ffmpeg -i input.mp4 -ss 00:00:03 -frames:v 1 -q:v 2 exact_frame.jpg

# 提取视频关键帧（I 帧）为小图
ffmpeg -i input.mp4 -vf select='eq(pict_type\,I)' -vsync 2 -s 160x90 -f image2 out-%02d.jpeg
```

---

## 4. GIF / 图片序列互转

```bash
# 将视频前 30 帧转成一张 GIF（会合并成动画）
ffmpeg -i input.mp4 -vframes 30 -y -f gif output.gif

# 截取视频某 10 秒生成 GIF
ffmpeg -i input.mp4 -t 10 -pix_fmt rgb24 output.gif

# 控制尺寸与帧率（GIF 体积优化）
ffmpeg -i input.mp4 -t 6 -vf "scale=480:-1,fps=15" -pix_fmt rgb24 output.gif

# 视频转成每帧一张图
ffmpeg -i input.mp4 out%d.jpg

# 图片序列合成视频（25fps）
ffmpeg -f image2 -i out%d.jpg -r 25 video.mp4
```

---

## 5. 音视频分离 / 提取 / 替换

```bash
# 分离视频流（去掉声音）
ffmpeg -i input_file -vcodec copy -an output_file_video

# 分离音频流（去掉画面）
ffmpeg -i input_file -vcodec copy -vn output_file_audio

# 提取音频为 mp3（高质量）
ffmpeg -i input.mp4 -vn -c:a libmp3lame -q:a 2 audio.mp3

# 提取音频为 aac / m4a
ffmpeg -i input.mp4 -vn -c:a aac -b:a 192k audio.m4a

# 去掉原声（静音输出）
ffmpeg -i input.mp4 -an -c:v copy silent.mp4

# 用新音频替换原音（视频不动）
ffmpeg -i input.mp4 -i new_audio.m4a -c:v copy -map 0:v:0 -map 1:a:0 -shortest replaced.mp4
```

---

## 6. 转码 / 封装 / 格式转换

```bash
# 转码为裸码流（h264 视频，无音频，用于二次封装）
ffmpeg -i input.mp4 -vcodec h264 -an -f m4v test.264

# 封装：把视频文件和音频文件合成一个（不重编码，快）
ffmpeg -i video_file -i audio_file -vcodec copy -acodec copy output_file

# mp4 → mov
ffmpeg -i input.mp4 -c copy output.mov

# mp4 → webm（VP9 + Opus，网页友好）
ffmpeg -i input.mp4 -c:v libvpx-vp9 -crf 30 -b:v 0 -c:a libopus output.webm

# 限制输出文件大小（如 10MB = 10485760 字节）
ffmpeg -i input.mp4 -fs 10485760 -c:v libx264 -crf 23 output_limited.mp4
```

---

## 7. 缩放 / 裁剪 / 旋转

```bash
# 缩放到 1280 宽，高度按比例自动
ffmpeg -i input.mp4 -vf "scale=1280:-1" out.mp4

# 缩放到精确 1920x1080（可能变形）
ffmpeg -i input.mp4 -vf "scale=1920:1080" out.mp4

# 等比缩放到 1080p 内（用 force_original_aspect_ratio 加黑边避免变形）
ffmpeg -i input.mp4 -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2" out.mp4

# 中心裁剪为 1080x1080 正方形
ffmpeg -i input.mp4 -vf "crop=1080:1080" out.mp4

# 从 (x=100,y=50) 裁出 800x600
ffmpeg -i input.mp4 -vf "crop=800:600:100:50" out.mp4

# 旋转 90°（顺时针，需重编码）
ffmpeg -i input.mp4 -vf "transpose=1" rotated.mp4

# 上下翻转 / 左右翻转
ffmpeg -i input.mp4 -vf "vflip" flip_v.mp4
ffmpeg -i input.mp4 -vf "hflip" flip_h.mp4
```

---

## 8. 拼接多段

```bash
# 方式 A：concat 解封装器（要求各段参数完全一致，最快、无损）
# 先写 list.txt：
#   file 'seg1.mp4'
#   file 'seg2.mp4'
#   file 'seg3.mp4'
ffmpeg -f concat -safe 0 -i list.txt -c copy merged.mp4

# 方式 B：concat 滤镜（参数可不同，会重编码，更稳）
ffmpeg -i seg1.mp4 -i seg2.mp4 -i seg3.mp4 \
  -filter_complex "[0:v][0:a][1:v][1:a][2:v][2:a]concat=n=3:v=1:a=1[v][a]" \
  -map "[v]" -map "[a]" -c:v libx264 -c:a aac merged.mp4
```

---

## 9. 加字幕 / 水印 / 边框

```bash
# 烧录硬字幕（需 .srt，ffmpeg 带 libass）
ffmpeg -i input.mp4 -vf "subtitles=sub.zh.srt" -c:a copy out.mp4

# 烧录带样式（指定字体/字号/描边）
ffmpeg -i input.mp4 -vf "subtitles=sub.zh.srt:force_style='FontSize=28,PrimaryColour=&H00FFFFFF&,OutlineColour=&H00000000&,Outline=2'" out.mp4

# 叠加水印 Logo（右上角，留 10px 边距）
ffmpeg -i input.mp4 -i logo.png -filter_complex "overlay=W-w-10:10" -c:a copy out.mp4

# 加纯色边框（如星辰灰蓝底，外扩 20px 再叠原画面）
ffmpeg -i input.mp4 -vf "pad=iw+40:ih+40:20:20:color=#0D1117" -c:a copy bordered.mp4

# 加角落 HUD 装饰：用 drawbox 画角标
ffmpeg -i input.mp4 -vf "drawbox=x=20:y=20:w=80:h=4:color=#2D7FF9:t=fill,drawbox=x=20:y=20:w=4:h=80:color=#2D7FF9:t=fill" -c:a copy hud.mp4
```

---

## 10. 变速 / 静音 / 混音 / 音量

```bash
# 视频 2 倍速（画面 + 声音同步）
ffmpeg -i input.mp4 -filter_complex "[0:v]setpts=0.5*PTS[v];[0:a]atempo=2.0[a]" -map "[v]" -map "[a]" out.mp4

# 仅画面加速（声音不变速，可能音画不同步）
ffmpeg -i input.mp4 -vf "setpts=0.5*PTS" -c:a copy out.mp4

# 静音整段
ffmpeg -i input.mp4 -af "volume=0" -c:v copy muted.mp4

# 音量减半 / 翻倍
ffmpeg -i input.mp4 -af "volume=0.5" -c:v copy quieter.mp4
ffmpeg -i input.mp4 -af "volume=2.0" -c:v copy louder.mp4

# 混入背景音乐（原声 1.0 + BGM 0.3，自动对齐最短）
ffmpeg -i input.mp4 -i bgm.mp3 -filter_complex "[0:a]volume=1.0[a1];[1:a]volume=0.3[a2];[a1][a2]amix=inputs=2:dropout_transition=0[a]" -map 0:v -map "[a]" -c:v copy mixed.mp4
```

---

## 11. 录制（RTSP / 摄像头）

```bash
# 录制 RTSP 流（直接拷贝，不重编码）
ffmpeg -i rtsp://hostname/stream -vcodec copy output.avi

# macOS 通过摄像头录制（avfoundation）
ffmpeg -f avfoundation -framerate 30 -i "0" -f mpeg1video -b 500k -r 20 -vf scale=640:360 output.avi

# 录制桌面（macOS，屏幕索引通常为 1）
ffmpeg -f avfoundation -framerate 30 -i "1" -c:v libx264 -preset ultrafast screen.mp4

# 录制并同时保存（边录边存，用 -t 限制时长，如 30 秒）
ffmpeg -f avfoundation -framerate 30 -i "1" -t 30 -c:v libx264 screen30s.mp4
```

---

## 12. 实战组合配方

```bash
# A) 用真实视频帧生成横版封面（第 8 秒，1080p 内的高质量 JPEG）
ffmpeg -ss 8 -i input.mp4 -frames:v 1 -q:v 2 -s 1920x1080 cover_h.jpg

# B) 导出通用 1080p 横屏成片（浏览器/手机全兼容）
ffmpeg -i input.mp4 -vf scale=1920:1080 -c:v libx264 -preset slow -crf 18 -c:a aac -b:a 192k -pix_fmt yuv420p out_1080p.mp4

# C) 无损剪出一段高光（不重编码，秒级）
ffmpeg -ss 00:00:10 -to 00:00:30 -i input.mp4 -c copy highlight.mp4

# D) 给成片加硬字幕 + 水印（一步到位）
ffmpeg -i input.mp4 -i logo.png -filter_complex "[0:v]subtitles=sub.zh.srt[vm];[vm][1:v]overlay=W-w-20:20[v]" -map "[v]" -map 0:a -c:v libx264 -c:a aac final.mp4

# E) 把长视频按章节拆成多段（无损，先准备好 list 或直接按时间点）
ffmpeg -ss 00:00:00 -to 00:01:00 -i input.mp4 -c copy part1.mp4
ffmpeg -ss 00:01:00 -to 00:02:00 -i input.mp4 -c copy part2.mp4

# F) 生成竖版 9:16 预览（含黑边居中，适合手机封面预览）
ffmpeg -i input.mp4 -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black" -c:a copy vertical.mp4
```
