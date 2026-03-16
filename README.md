# TikTok Ripper 🚀

YouTube 视频搬运工具 - 下载、处理、一键发布到抖音

## 功能特点

- 🔍 搜索 YouTube 视频
- ⬇️  下载 YouTube 视频 (最高 1080p)
- ✂️  自动切片 (长视频 -> 多个短 clip)
- 🔄  去重处理 (调速、加字幕)
- 📱  抖音尺寸适配 (竖版 1080x1920)
- 🎬  **自动字幕** (Whisper 语音识别)
- ✨  **AI 标题/描述生成**
- 🚀  一键搬运 (下载+处理)

## 环境要求

1. **Python 3.8+**
2. **FFmpeg** - 必须安装并添加到 PATH
   - 下载: https://ffmpeg.org/download.html
3. **yt-dlp** - YouTube 下载器
   - 安装: `pip install yt-dlp`

## 安装

```bash
# 1. 安装 Python 依赖
pip install yt-dlp

# 2. 安装 FFmpeg
# Windows: 下载 ffmpeg.exe 并放到 PATH 中
# Mac: brew install ffmpeg
# Linux: sudo apt install ffmpeg

# 3. 验证安装
ffmpeg -version
yt-dlp --version
```

## 使用方法

### 方式一: 命令行运行

```bash
cd tiktok-ripper
python main.py
```

### 方式二: 导入使用

```python
import downloader
import processor

# 下载视频
url = "https://www.youtube.com/watch?v=xxx"
filepath = downloader.download_video(url, "downloads", "1080p")

# 处理视频
output = processor.process_video(
    filepath,
    output_dir="output",
    add_subtitles=True,
    change_speed_dedup=True,
    target_width=1080,
    target_height=1920
)
```

## 配置

修改 `config.py` 文件:

```python
# 目录配置
DOWNLOAD_DIR = "downloads"
OUTPUT_DIR = "output"

# AI 配置 (生成标题/描述)
OPENAI_API_KEY = "sk-xxx"  # 或设置环境变量
# MINIMAX_API_KEY = "xxx"

# YouTube 画质
YOUTUBE_QUALITY = "1080p"  # 2160p, 1080p, 720p, 480p

# TikTok 尺寸 (竖版)
TIKTOK_WIDTH = 1080
TIKTOK_HEIGHT = 1920

# 切片设置
TIKTOK_DURATION = 30       # 片段时长
TIKTOK_MIN_DURATION = 15   # 最短
TIKTOK_MAX_DURATION = 60   # 最长

# 去重设置
ADD_SUBTITLE = True        # 添加字幕
CHANGE_SPEED = True        # 调速去重
```

## 工作流程

```
YouTube URL
    │
    ▼
┌─────────────┐
│  下载视频   │  downloader.py
└─────────────┘
    │
    ▼
┌─────────────┐
│  转码 H264  │  processor.py
└─────────────┘
    │
    ├──> 切片 (15-60s)
    │    │
    │    ├──> 调速去重 (0.9x-1.1x)
    │    │
    │    ├──> 添加字幕
    │    │
    │    └──> 调整尺寸 (1080x1920)
    │
    └──> 输出到 output/
            │
            ▼
         抖音发布
```

## 新增功能: 自动字幕 + AI 生成

### 🎬 自动字幕 (Whisper)

在主菜单选择 `7. 自动字幕` 可以:
1. **生成字幕** - 使用 Whisper 语音识别生成 SRT 文件
2. **烧录字幕** - 将字幕烧录到视频中 (硬字幕)
3. **一步到位** - 生成+烧录一次完成

支持语言: 自动检测或手动指定 (en/zh)

### ✨ AI 生成标题/描述

在主菜单选择 `8. AI 生成标题/描述` 可以:
- 根据视频内容生成抖音风格的爆款标题
- 自动生成描述文案
- 生成相关标签

需要配置 LLM API:
- 方式1: 在 `config.py` 中设置 `OPENAI_API_KEY`
- 方式2: 设置环境变量 `OPENAI_API_KEY` 或 `MINIMAX_API_KEY`

## 注意事项

1. **版权** - 搬运视频可能涉及版权问题，建议:
   - 修改视频内容（剪辑、调速、加字幕）
   - 注明来源
   - 使用原创或可搬运内容

2. **去重** - 抖音会检测搬运:
   - 调速是最简单的去重方式
   - 添加字幕/水印可以提高原创度
   - 手动剪辑效果最好

3. **画质** - YouTube 下载高清视频需要 JavaScript 运行时:
   - 安装 Node.js 可下载更高画质
   - 或者使用 yt-dlp 的默认画质

## 常见问题

**Q: 下载失败怎么办?**
A: 
- 检查网络连接
- 尝试使用 `--no-check-certificate` 参数
- 更新 yt-dlp: `pip install -U yt-dlp`

**Q: FFmpeg 找不到?**
A: 
- 确认 FFmpeg 已安装
- 添加到系统 PATH
- 或在 config.py 中指定完整路径

**Q: 视频太大?**
A: 
- 降低 CRF 值 (如 23)
- 或在处理后压缩

## 目录结构

```
tiktok-ripper/
├── config.py        # 配置文件
├── downloader.py    # YouTube 下载器
├── processor.py     # 视频处理器
├── main.py          # 主程序 (CLI)
├── downloads/      # 下载的视频
├── output/          # 处理后的视频
└── temp/            # 临时文件
```

---

Made with ❤️ for content creators
