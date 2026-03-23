# TikTok Ripper 配置 - 跨平台版本

import os
import utils

## 目录配置
DOWNLOAD_DIR = "downloads"      # 下载目录
OUTPUT_DIR = "output"           # 处理后输出目录
TEMP_DIR = "temp"               # 临时文件目录

## YouTube 配置
YOUTUBE_QUALITY = "1080P"      # 固定 1080P
COOKIE_FILE = ""                # Cookie 文件路径 (留空则不使用)
YOUTUBE_PROXY = ""              # 代理地址 (留空自动检测)
YOUTUBE_USE_EJS = True          # 使用远程组件绕过JS验证
YOUTUBE_JS_RUNTIME = "node:node"  # JavaScript 运行时

# 自动检测代理
if not YOUTUBE_PROXY:
    YOUTUBE_PROXY = utils.get_default_proxy()

## TikTok/抖音 配置
TIKTOK_DURATION = 40            # 切片时长 (秒)
TIKTOK_MIN_DURATION = 30       # 最短片段 (30秒最佳)
TIKTOK_MAX_DURATION = 45        # 最长片段 (45秒最佳)

## 抖音尺寸
TIKTOK_WIDTH = 1080
TIKTOK_HEIGHT = 1920            # 竖版
# TIKTOK_WIDTH = 1920
# TIKTOK_HEIGHT = 1080           # 横版

## 转码设置
VIDEO_CODEC = "libx264"          # H264 编码
AUDIO_CODEC = "aac"              # AAC 音频
PRESET = "ultrafast"             # 转码速度
CRF = 28                         # 质量 (越低越好)

## 去重处理
ADD_SUBTITLE = True              # 添加字幕
CHANGE_SPEED = True              # 调整速度 (0.9x-1.1x)
CROP_VIDEO = True                # 裁剪画面
ADD_WATERMARK = False            # 添加水印

## FFmpeg 路径 (自动检测)
FFMPEG_PATH = utils.get_ffmpeg_path()
FFPROBE_PATH = utils.get_ffprobe_path()

## AI 配置 (用于生成标题/描述)
# 设置环境变量或直接填写 API Key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")

## YouTube Kids 配置
YOUTUBE_KIDS_QUALITY = "720p"   # 默认画质
YOUTUBE_KIDS_LANGUAGE = "zh-Hans,zh-Hant,zh,en"  # 字幕语言
YOUTUBE_KIDS_OUTPUT = "downloads/youtube_kids"  # 输出目录
