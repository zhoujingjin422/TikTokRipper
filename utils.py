"""
跨平台工具模块
支持 Windows、macOS、Linux
"""
import os
import sys
import platform
import subprocess
import shutil
import pathlib


def get_system():
    """获取当前操作系统"""
    return platform.system().lower()  # 'windows', 'darwin', 'linux'


def is_windows():
    return get_system() == 'windows'


def is_mac():
    return get_system() == 'darwin'


def is_linux():
    return get_system() == 'linux'


def get_home_dir():
    """获取用户主目录"""
    return str(pathlib.Path.home())


def get_config_dir():
    """获取配置文件目录"""
    if is_windows():
        return os.path.join(os.environ.get('APPDATA', ''), 'tiktok-ripper')
    elif is_mac():
        return os.path.expanduser('~/Library/Application Support/tiktok-ripper')
    else:  # Linux
        return os.path.expanduser('~/.config/tiktok-ripper')


def get_ffmpeg_path():
    """
    获取 FFmpeg 路径 - 跨平台自动检测
    """
    # 1. 检查系统 PATH
    ffmpeg = shutil.which('ffmpeg')
    if ffmpeg:
        return ffmpeg
    
    # 2. Windows 常见路径
    if is_windows():
        windows_paths = [
            r"D:\openclaw\workspace\video-downloader\bin\ffmpeg-7.1-essentials_build\bin\ffmpeg.exe",
            r"D:\openclaw\workspace\video-downloader\bin\ffmpeg-6.1-essentials_build\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\tools\ffmpeg\bin\ffmpeg.exe",
            os.path.expanduser(r"~\scoop\shims\ffmpeg.exe"),
            os.path.expanduser(r"~\Downloads\ffmpeg\bin\ffmpeg.exe"),
        ]
        for p in windows_paths:
            if os.path.isfile(p):
                return p
    
    # 3. macOS 常见路径
    elif is_mac():
        mac_paths = [
            "/usr/local/bin/ffmpeg",
            "/opt/homebrew/bin/ffmpeg",
            "/opt/local/bin/ffmpeg",
        ]
        for p in mac_paths:
            if os.path.isfile(p):
                return p
    
    # 4. Linux 常见路径
    elif is_linux():
        linux_paths = [
            "/usr/bin/ffmpeg",
            "/usr/local/bin/ffmpeg",
        ]
        for p in linux_paths:
            if os.path.isfile(p):
                return p
    
    # 5. 返回命令名，让系统 PATH 处理
    return "ffmpeg"


def get_ffprobe_path():
    """获取 FFprobe 路径"""
    # 先检查系统 PATH
    ffprobe = shutil.which('ffprobe')
    if ffprobe:
        return ffprobe
    
    ffmpeg_dir = os.path.dirname(get_ffmpeg_path())
    if ffmpeg_dir:
        ffprobe_path = os.path.join(ffmpeg_dir, 'ffprobe' + ('.exe' if is_windows() else ''))
        if os.path.isfile(ffprobe_path):
            return ffprobe_path
    
    return "ffprobe"


def get_python_path():
    """获取 Python 路径"""
    return sys.executable


def get_browser_cookie_support():
    """获取支持的浏览器列表"""
    if is_windows():
        return ["chrome", "edge", "firefox", "brave", "opera"]
    elif is_mac():
        return ["safari", "chrome", "firefox", "brave", "opera"]
    else:  # Linux
        return ["chrome", "firefox", "brave", "opera"]


def get_default_proxy():
    """获取默认代理地址"""
    if is_windows():
        # Windows 常用代理
        return "http://127.0.0.1:7897"
    elif is_mac():
        # Mac 常用代理 (ClashX, Surge 等)
        return "http://127.0.0.1:7890"
    else:
        # Linux 常用代理
        return "http://127.0.0.1:7890"


def get_default_cookie_path():
    """获取默认 Cookie 文件路径"""
    if is_windows():
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.txt")
    elif is_mac():
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.txt")
    else:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.txt")


def ensure_dir(path):
    """确保目录存在"""
    os.makedirs(path, exist_ok=True)
    return path


def get_video_downloader_dir():
    """获取 video-downloader 目录"""
    # 尝试多个可能的位置
    home = get_home_dir()
    
    possible_paths = [
        os.path.join(home, "workspace", "video-downloader"),
        os.path.join(home, "projects", "video-downloader"),
        r"D:\openclaw\workspace\video-downloader",
        "/opt/video-downloader",
    ]
    
    for p in possible_paths:
        if os.path.isdir(p):
            return p
    
    return None


def get_ffmpeg_in_video_downloader():
    """从 video-downloader 目录获取 FFmpeg"""
    viddl_dir = get_video_downloader_dir()
    if viddl_dir:
        if is_windows():
            ffmpeg_path = os.path.join(viddl_dir, "bin", "ffmpeg-7.1-essentials_build", "bin", "ffmpeg.exe")
            if os.path.isfile(ffmpeg_path):
                return ffmpeg_path
        elif is_mac() or is_linux():
            ffmpeg_path = os.path.join(viddl_dir, "bin", "ffmpeg", "bin", "ffmpeg")
            if os.path.isfile(ffmpeg_path):
                return ffmpeg_path
    
    return None


def print_system_info():
    """打印系统信息"""
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"架构: {platform.machine()}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"FFmpeg: {get_ffmpeg_path()}")
    print(f"支持浏览器: {', '.join(get_browser_cookie_support())}")
