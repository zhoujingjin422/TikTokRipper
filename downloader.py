"""
YouTube 视频下载器 - 简化为只下载 1080P
"""
import os
import sys
import subprocess
import json
from config import YOUTUBE_PROXY, YOUTUBE_USE_EJS, YOUTUBE_JS_RUNTIME

# 设置 UTF-8 输出
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


def get_ffmpeg_path():
    """获取 FFmpeg 路径"""
    # 优先使用 video-downloader 项目的 FFmpeg
    bundled = r"D:\openclaw\workspace\video-downloader\bin\ffmpeg-7.1-essentials_build\bin\ffmpeg.exe"
    if os.path.exists(bundled):
        return bundled
    
    # 检查系统 PATH
    for prog in ['ffmpeg', 'ffmpeg.exe']:
        try:
            result = subprocess.run([prog, '-version'], capture_output=True, text=True)
            if result.returncode == 0:
                return prog
        except:
            pass
    
    return None


def get_video_info(url, cookie_file=None):
    """获取视频信息"""
    print(f"[INFO] 获取视频信息: {url}")
    
    cmd = ["yt-dlp", "--dump-json", "--no-download", url, "--no-warnings"]
    
    # Cookie
    if cookie_file and os.path.exists(cookie_file):
        cmd.extend(['--cookies', cookie_file])
    
    # 添加代理
    if YOUTUBE_PROXY:
        cmd.extend(['--proxy', YOUTUBE_PROXY])
    
    # EJS 远程组件 (如果启用)
    if YOUTUBE_USE_EJS:
        cmd.extend(['--remote-components', 'ejs:github'])
    
    # JS 运行时 (如果配置)
    if YOUTUBE_JS_RUNTIME:
        cmd.extend(['--js-runtimes', YOUTUBE_JS_RUNTIME])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        
        if result.returncode != 0:
            print(f"[ERROR] {result.stderr}")
            return None
        
        data = json.loads(result.stdout)
        
        info = {
            'title': data.get('title', 'Unknown'),
            'duration': data.get('duration', 0),
            'uploader': data.get('uploader', 'Unknown'),
            'id': data.get('id', ''),
        }
        
        print(f"[INFO] 标题: {info['title']}, 时长: {info['duration']}秒")
        return info
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return None


def download_video(url, output_dir="downloads", cookie_file=None, max_retries=3, download_subtitle=True, quality=None):
    """
    下载 YouTube 视频
    
    Args:
        url: YouTube URL
        output_dir: 输出目录
        cookie_file: Cookie 文件路径
        max_retries: 最大重试次数
        download_subtitle: 是否下载字幕
        quality: 视频清晰度 "1080p" / "720p" 或 None (默认最佳)
    
    Returns:
        str: 下载的文件路径
    """
    # 获取格式参数 (不区分大小写)
    quality_lower = quality.lower() if quality else ""
    if quality_lower == "1080p":
        format_spec = 'bestvideo[height<=1080]+bestaudio[ext=m4a]/best[height<=1080]/best'
    elif quality_lower == "720p":
        format_spec = 'bestvideo[height<=720]+bestaudio[ext=m4a]/best[height<=720]/best'
    else:
        # 默认使用最灵活的格式
        format_spec = 'bestvideo+bestaudio/best'
    
    if quality:
        print(f"[INFO] 目标清晰度: {quality}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取视频 ID
    video_id = ""
    if "v=" in url:
        video_id = url.split("v=")[1].split("&")[0]
    safe_title = f"video_{video_id}"
    output_path = os.path.join(output_dir, f"{safe_title}.mp4")
    
    # 字幕输出路径
    subtitle_path = os.path.join(output_dir, f"{safe_title}.srt")
    
    # 添加 --merge-output-format mp4 确保输出是 mp4 格式
    # 这样可以避免 webm 格式导致的问题
    
    # FFmpeg 位置
    ffmpeg_path = get_ffmpeg_path()
    ffmpeg_dir = os.path.dirname(ffmpeg_path) if ffmpeg_path else None
    
    # Cookie
    use_cookie = cookie_file and os.path.exists(cookie_file)
    
    # 跟踪字幕下载状态
    subtitle_failed = False
    
    # 重试下载
    for attempt in range(1, max_retries + 1):
        print(f"\n[INFO] 开始下载 (尝试 {attempt}/{max_retries}): {url}")
        
        # 如果是重试，删除可能存在的部分文件
        if attempt > 1 and os.path.exists(output_path):
            try:
                os.remove(output_path)
                print(f"[INFO] 删除上次未完成的文件")
            except:
                pass
        
        # 构建命令 - 使用更好的进度输出
        cmd = [
            'yt-dlp',
            '--output', output_path,
            '--progress',
            '--no-warnings',
            '--no-playlist',
            '-c',          # 断点续传
            '--continue',  # 继续下载部分文件
            '--newline',   # 换行输出进度
        ]
        
        # 添加格式参数 (保持原格式)
        if format_spec:
            cmd.extend(['--format', format_spec])
        
        # 字幕下载选项 - 只有在需要且未失败时才添加
        # 注意：字幕和视频一起下载容易被限流，这里简化处理
        # 字幕下载失败不影响视频下载结果
        if download_subtitle and not subtitle_failed:
            # 下载srt字幕，尝试多种中文/英文语言
            cmd.extend([
                '--write-sub',
                '--write-auto-sub',  # YouTube 自动字幕
                '--sub-lang', 'en-US,en,zh-CN,zh-Hans,zh-Hant,zh',  # 英文优先，中文备用
                '--sub-format', 'srt',
                '--convert-subs', 'srt',
            ])
        
        # FFmpeg 位置
        if ffmpeg_dir:
            cmd.extend(['--ffmpeg-location', ffmpeg_dir])
        
        # Cookie
        if use_cookie:
            cmd.extend(['--cookies', cookie_file])
            print(f"[INFO] 使用 Cookie")
        
        # 代理
        if YOUTUBE_PROXY:
            cmd.extend(['--proxy', YOUTUBE_PROXY])
            print(f"[INFO] 使用代理: {YOUTUBE_PROXY}")
        
        # EJS 远程组件 (如果启用)
        if YOUTUBE_USE_EJS:
            cmd.extend(['--remote-components', 'ejs:github'])
        
        # JS 运行时 (如果配置)
        if YOUTUBE_JS_RUNTIME:
            cmd.extend(['--js-runtimes', YOUTUBE_JS_RUNTIME])
        
        # 合并输出为 mp4 格式（避免 webm 格式问题）
        cmd.extend(['--merge-output-format', 'mp4'])
        
        cmd.append(url)
        
        print(f"[CMD] yt-dlp ...")
        
        try:
            # 超时 30 分钟 (大视频可能需要更久)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
            
            # 打印输出（包含进度信息）
            if result.stdout:
                for line in result.stdout.split('\n'):
                    # 过滤掉冗余信息，只保留进度
                    if '%' in line or 'Downloading' in line or ' ETA' in line or 'M' in line or 'K' in line:
                        print(line)
            
            if result.returncode != 0:
                error_msg = result.stderr
                print(f"[ERROR] 下载失败: {error_msg}")
                
                # 检测字幕下载失败错误 (HTTP 429)
                if 'subtitles' in error_msg.lower() and ('429' in error_msg or 'too many requests' in error_msg.lower()):
                    print("[WARN] 字幕下载被限流 (429)，跳过字幕下载重试...")
                    subtitle_failed = True
                    # 视频已下载成功，字幕失败不重试整个下载
                    # 继续检查视频文件是否存在
                    if os.path.exists(output_path):
                        size = os.path.getsize(output_path) / (1024*1024)
                        print(f"[SUCCESS] 视频下载完成: {size:.1f} MB (字幕被限流)")
                        return output_path
                    continue
                
                # 检测其他字幕错误 - 视频可能已下载成功
                if 'subtitles' in error_msg.lower():
                    print("[WARN] 字幕下载失败，检查视频是否已下载...")
                    if os.path.exists(output_path):
                        size = os.path.getsize(output_path) / (1024*1024)
                        print(f"[SUCCESS] 视频下载完成: {size:.1f} MB")
                        return output_path
                
                # 如果是账户/权限问题，不再重试
                if 'HTTP Error 403' in error_msg or 'Login required' in error_msg:
                    print("[ERROR] Cookie 可能已失效，请更新 Cookie")
                    return None
                
                # 检测格式不可用错误，尝试更灵活的格式
                if 'format is not available' in error_msg.lower() or 'requested format' in error_msg.lower():
                    print("[WARN] 指定格式不可用，尝试更灵活的格式...")
                    # 使用最简单的格式重试
                    cmd = [c for c in cmd if c != '--format' and c != format_spec]
                    cmd.extend(['--format', 'best/bestvideo+bestaudio'])
                    attempt -= 1  # 这次不计入重试次数
                    continue
                
                # 检测 Android 客户端失败，回退到 web 客户端
                if 'video is not available' in error_msg.lower() or 'this video is not available' in error_msg.lower():
                    print("[WARN] Android 客户端失败，回退到 web 客户端...")
                    # 移除 Android 客户端配置，使用默认 web 客户端
                    cmd = [c for c in cmd if '--extractor-args' not in c]
                    cmd = [c for c in cmd if 'youtube:player_client' not in c]
                    # 使用浏览器 User-Agent
                    cmd = [c if c != '--user-agent' else '--user-agent' for c in cmd]
                    # 重新构建命令，使用 web 客户端
                    new_cmd = []
                    skip_next = False
                    for i, c in enumerate(cmd):
                        if skip_next:
                            skip_next = False
                            continue
                        if c == '--user-agent' and 'Android' in str(cmd[i+1] if i+1 < len(cmd) else ''):
                            new_cmd.append('--user-agent')
                            new_cmd.append('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                            skip_next = True
                            continue
                        new_cmd.append(c)
                    cmd = new_cmd
                    # 重新添加 EJS 和 JS 运行时
                    if YOUTUBE_USE_EJS:
                        cmd.extend(['--remote-components', 'ejs:github'])
                    if YOUTUBE_JS_RUNTIME:
                        cmd.extend(['--js-runtimes', YOUTUBE_JS_RUNTIME])
                    attempt -= 1  # 这次不计入重试次数
                    continue
                
                # 继续重试
                if attempt < max_retries:
                    wait_time = attempt * 30
                    print(f"[INFO] {wait_time}秒后重试...")
                    import time
                    time.sleep(wait_time)
                    continue
                else:
                    return None
            
            # 检查输出文件
            if os.path.exists(output_path):
                size = os.path.getsize(output_path) / (1024*1024)
                print(f"[SUCCESS] 下载完成: {size:.1f} MB")
            
            # 检查字幕文件 (下载了独立字幕文件)
            if download_subtitle and not subtitle_failed:
                # 查找下载的字幕文件
                subtitle_found = None
                for f in os.listdir(output_dir):
                    if f.startswith(safe_title) and f.endswith('.srt'):
                        subtitle_found = os.path.join(output_dir, f)
                        break
                
                if subtitle_found:
                    # 重命名为标准名称
                    if subtitle_found != subtitle_path:
                        try:
                            import shutil
                            shutil.move(subtitle_found, subtitle_path)
                            print(f"[INFO] 字幕文件: {os.path.basename(subtitle_path)}")
                        except:
                            print(f"[INFO] 字幕文件: {os.path.basename(subtitle_found)}")
                else:
                    # 没有找到字幕文件（可能视频本身就没有字幕）
                    print("[INFO] 未找到字幕文件（视频可能没有字幕）")
            elif subtitle_failed:
                print("[INFO] 已跳过字幕下载（被限流）")
            
            # 检查输出文件
            if os.path.exists(output_path):
                size = os.path.getsize(output_path) / (1024*1024)
                print(f"[SUCCESS] 视频下载完成: {size:.1f} MB")
                
                # 视频下载成功后，尝试单独下载字幕（如果之前失败）
                if subtitle_failed:
                    print("\n[INFO] 视频下载成功，尝试单独下载字幕...")
                    subtitle_result = download_subtitles_only(
                        url, 
                        output_dir, 
                        cookie_file,
                        max_retries=2
                    )
                    if subtitle_result:
                        print(f"[SUCCESS] 字幕下载成功: {os.path.basename(subtitle_result)}")
                
                return output_path
            
            # 如果指定的 mp4 不存在，尝试找其他格式
            for f in os.listdir(output_dir):
                if video_id in f and f.endswith(('.mp4', '.webm', '.mkv', '.flv')):
                    filepath = os.path.join(output_dir, f)
                    size = os.path.getsize(filepath) / (1024*1024)
                    print(f"[SUCCESS] 视频下载完成: {size:.1f} MB")
                    
                    # 尝试单独下载字幕（如果之前失败）
                    if download_subtitle and subtitle_failed:
                        print("\n[INFO] 视频下载成功，尝试单独下载字幕...")
                        download_subtitles_only(url, output_dir, cookie_file, max_retries=2)
                    
                    # 重命名为 mp4（如果需要）
                    if not filepath.endswith('.mp4'):
                        new_path = filepath.rsplit('.', 1)[0] + '.mp4'
                        try:
                            import shutil
                            shutil.move(filepath, new_path)
                            print(f"[INFO] 转换为 mp4 格式")
                            return new_path
                        except:
                            return filepath
                    return filepath
            
            print(f"[WARN] 输出文件不存在")
            return None
                    
        except subprocess.TimeoutExpired:
            print(f"[ERROR] 下载超时 (30分钟)，尝试 {attempt + 1}/{max_retries}")
            if attempt < max_retries:
                import time
                time.sleep(30)
                continue
        except Exception as e:
            print(f"[ERROR] 下载异常: {e}")
            if attempt < max_retries:
                import time
                time.sleep(30)
                continue
    
    return None


def download_subtitles_only(url, output_dir="downloads", cookie_file=None, max_retries=3):
    """
    单独下载字幕（视频下载失败后可以使用）
    
    Args:
        url: YouTube URL
        output_dir: 输出目录
        cookie_file: Cookie 文件路径
        max_retries: 最大重试次数
    
    Returns:
        str: 下载的字幕文件路径，如果没有则返回 None
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取视频 ID
    video_id = ""
    if "v=" in url:
        video_id = url.split("v=")[1].split("&")[0]
    safe_title = f"video_{video_id}"
    subtitle_path = os.path.join(output_dir, f"{safe_title}.srt")
    
    # 检查字幕是否已存在
    if os.path.exists(subtitle_path):
        print(f"[INFO] 字幕已存在: {os.path.basename(subtitle_path)}")
        return subtitle_path
    
    # FFmpeg 位置
    ffmpeg_path = get_ffmpeg_path()
    ffmpeg_dir = os.path.dirname(ffmpeg_path) if ffmpeg_path else None
    
    # Cookie
    use_cookie = cookie_file and os.path.exists(cookie_file)
    
    for attempt in range(1, max_retries + 1):
        print(f"\n[INFO] 尝试下载字幕 (尝试 {attempt}/{max_retries}): {url}")
        
        # 构建命令 - 只下载字幕，不下载视频
        cmd = [
            'yt-dlp',
            '--write-sub',
            '--write-auto-sub',
            '--skip-download',  # 不下载视频
            '--sub-lang', 'en-US,en',  # 只下载英文字幕
            '--sub-format', 'srt',
            '--convert-subs', 'srt',
            '--output', os.path.join(output_dir, f'{safe_title}.%(ext)s'),
            '--no-warnings',
        ]
        
        if ffmpeg_dir:
            cmd.extend(['--ffmpeg-location', ffmpeg_dir])
        
        if use_cookie:
            cmd.extend(['--cookies', cookie_file])
        
        if YOUTUBE_PROXY:
            cmd.extend(['--proxy', YOUTUBE_PROXY])
        
        if YOUTUBE_USE_EJS:
            cmd.extend(['--remote-components', 'ejs:github'])
        
        if YOUTUBE_JS_RUNTIME:
            cmd.extend(['--js-runtimes', YOUTUBE_JS_RUNTIME])
        
        cmd.append(url)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            # 打印输出
            if result.stdout:
                for line in result.stdout.split('\n'):
                    if 'subtitle' in line.lower() or 'skipping' in line.lower():
                        print(line)
            
            if result.returncode != 0:
                error_msg = result.stderr
                print(f"[WARN] 字幕下载失败: {error_msg[:200]}")
                
                # 被限流，等待后重试
                if '429' in error_msg or 'too many requests' in error_msg.lower():
                    wait_time = attempt * 10
                    print(f"[INFO] 被限流，{wait_time}秒后重试...")
                    import time
                    time.sleep(wait_time)
                    continue
            else:
                # 查找字幕文件
                for f in os.listdir(output_dir):
                    if f.startswith(safe_title) and f.endswith('.srt'):
                        subtitle_found = os.path.join(output_dir, f)
                        # 重命名为标准名称
                        if subtitle_found != subtitle_path:
                            try:
                                import shutil
                                shutil.move(subtitle_found, subtitle_path)
                            except:
                                pass
                        print(f"[SUCCESS] 字幕下载完成: {os.path.basename(subtitle_path)}")
                        return subtitle_path
                
                print("[WARN] 字幕命令执行成功但未找到字幕文件")
                
        except subprocess.TimeoutExpired:
            print(f"[ERROR] 字幕下载超时")
        except Exception as e:
            print(f"[ERROR] 字幕下载异常: {e}")
        
        if attempt < max_retries:
            import time
            time.sleep(5)
    
    print("[ERROR] 字幕下载失败")
    return None


def get_video_size_estimate(url, cookie_file=None):
    """
    获取视频大小估算 (在下载前)
    """
    # 使用更灵活的格式，避免 "format is not available" 错误
    cmd = [
        'yt-dlp',
        '--format', 'best/bestvideo+bestaudio',
        '--print', '%(filesize,filesize_approx)s',
        '--no-download',
        '--no-warnings',
    ]
    
    if cookie_file and os.path.exists(cookie_file):
        cmd.extend(['--cookies', cookie_file])
    
    if YOUTUBE_PROXY:
        cmd.extend(['--proxy', YOUTUBE_PROXY])
    
    if YOUTUBE_USE_EJS:
        cmd.extend(['--remote-components', 'ejs:github'])
    
    if YOUTUBE_JS_RUNTIME:
        cmd.extend(['--js-runtimes', YOUTUBE_JS_RUNTIME])
    
    cmd.append(url)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0 and result.stdout.strip():
            size_bytes = int(result.stdout.strip())
            if size_bytes > 0:
                size_mb = size_bytes / (1024 * 1024)
                return size_mb
    except:
        pass
    
    return None


def download_playlist(url, output_dir="downloads", limit=10, cookie_file=None, quality=None):
    """
    下载 YouTube 播放列表
    
    Args:
        url: YouTube 播放列表 URL
        output_dir: 输出目录
        limit: 最大下载数量
        cookie_file: Cookie 文件路径
        quality: 视频清晰度 "1080p" / "720p" 或 None
    
    Returns:
        list: 下载成功的文件路径列表
    """
    if quality:
        print(f"[INFO] 目标清晰度: {quality}")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"[INFO] 开始下载播放列表...")
    print(f"[INFO] URL: {url}")
    print(f"[INFO] 最大数量: {limit}")
    
    # Cookie
    use_cookie = cookie_file and os.path.exists(cookie_file)
    
    # 先获取播放列表信息 - 使用更可靠的方法
    print("[INFO] 获取播放列表信息...")
    
    list_cmd = [
        'yt-dlp',
        '--flat-playlist',
        '--print', '%(id)s|%(title)s',
        '--no-warnings',
        '--playlist-end', str(limit) if limit else '100',
    ]
    
    if use_cookie:
        list_cmd.extend(['--cookies', cookie_file])
    
    if YOUTUBE_PROXY:
        list_cmd.extend(['--proxy', YOUTUBE_PROXY])
    
    if YOUTUBE_USE_EJS:
        list_cmd.extend(['--remote-components', 'ejs:github'])
    
    if YOUTUBE_JS_RUNTIME:
        list_cmd.extend(['--js-runtimes', YOUTUBE_JS_RUNTIME])
    
    list_cmd.append(url)
    
    try:
        result = subprocess.run(list_cmd, capture_output=True, text=True, timeout=120, encoding='utf-8', errors='ignore')
        
        if result.returncode != 0:
            print(f"[ERROR] 获取播放列表失败: {result.stderr}")
            return []
        
        # 解析视频列表
        videos = []
        for line in result.stdout.strip().split('\n'):
            line = line.strip()
            if '|' in line:
                parts = line.split('|', 1)
                if len(parts) == 2:
                    videos.append({
                        'id': parts[0].strip(),
                        'title': parts[1].strip()
                    })
        
        if not videos:
            print("[ERROR] 未找到播放列表中的视频")
            return []
        
        print(f"[INFO] 播放列表共有 {len(videos)} 个视频")
        
        # 限制数量
        if limit and limit > 0:
            videos = videos[:limit]
        
        print(f"[INFO] 将下载前 {len(videos)} 个视频")
        
    except Exception as e:
        print(f"[ERROR] 获取播放列表失败: {e}")
        return []
    
    # 下载每个视频
    downloaded = []
    failed = []
    skipped = []
    
    for i, video in enumerate(videos, 1):
        video_url = f"https://www.youtube.com/watch?v={video['id']}"
        print(f"\n[{i}/{len(videos)}] 准备下载: {video['title'][:50]}...")
        
        # 使用与单视频下载相同的方式
        filepath = download_video(
            url=video_url,
            output_dir=output_dir,
            cookie_file=cookie_file,
            max_retries=1,  # 播放列表中减少重试次数，加快速度
            download_subtitle=False,
            quality=quality
        )
        
        if filepath and os.path.exists(filepath):
            downloaded.append(filepath)
            print(f"   ✅ 下载成功: {os.path.basename(filepath)}")
        elif os.path.exists(os.path.join(output_dir, f"video_{video['id']}.mp4")):
            # 文件已存在（可能是之前下载的）
            filepath = os.path.join(output_dir, f"video_{video['id']}.mp4")
            downloaded.append(filepath)
            print(f"   ✅ 文件已存在: {os.path.basename(filepath)}")
        else:
            # 检查是否是可跳过的错误（地区限制、私有视频等）
            print(f"   ⚠️ 跳过该视频（可能地区限制或私有）")
            skipped.append(video['title'])
    
    # 总结
    print(f"\n{'='*50}")
    print(f"下载完成!")
    print(f"   成功: {len(downloaded)} 个")
    print(f"   跳过: {len(skipped)} 个")
    
    if skipped:
        print(f"\n跳过的视频:")
        for title in skipped[:10]:  # 最多显示10个
            print(f"   - {title[:60]}")
        if len(skipped) > 10:
            print(f"   ... 还有 {len(skipped) - 10} 个")
    
    return downloaded


def search_youtube(query, max_results=10):
    """搜索 YouTube"""
    cmd = ["yt-dlp", "--dump-json", "--no-download", "--playlist-end", str(max_results), f"ytsearch{max_results}:{query}"]
    
    if YOUTUBE_PROXY:
        cmd.extend(['--proxy', YOUTUBE_PROXY])
    
    if YOUTUBE_USE_EJS:
        cmd.extend(['--remote-components', 'ejs:github'])
    
    if YOUTUBE_JS_RUNTIME:
        cmd.extend(['--js-runtimes', YOUTUBE_JS_RUNTIME])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            return []
        
        videos = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    videos.append({
                        'id': data.get('id', ''),
                        'title': data.get('title', ''),
                        'duration': data.get('duration', 0),
                        'url': f"https://www.youtube.com/watch?v={data.get('id', '')}"
                    })
                except:
                    pass
        
        return videos
        
    except:
        return []
