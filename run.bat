@echo off
chcp 65001 >nul
title TikTok Ripper

echo.
echo ╔═══════════════════════════════════════╗
echo ║       TikTok Ripper v1.0              ║
echo ║   YouTube -> TikTok 搬运工具          ║
echo ╚═══════════════════════════════════════╝
echo.

cd /d "%~dp0"

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未安装，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 检查 yt-dlp
pip show yt-dlp >nul 2>&1
if errorlevel 1 (
    echo 📦 正在安装 yt-dlp...
    pip install yt-dlp
)

REM 检查 FFmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  FFmpeg 未找到，请安装 FFmpeg 并添加到 PATH
    echo    下载地址: https://ffmpeg.org/download.html
    echo.
    pause
)

REM 创建目录
if not exist "downloads" mkdir downloads
if not exist "output" mkdir output
if not exist "temp" mkdir temp

REM 运行主程序
python main.py

pause
