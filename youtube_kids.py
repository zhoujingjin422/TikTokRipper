"""
YouTube Kids 视频下载 + 字幕烧录工具
整合自 youtubekids 项目
"""
import os
import sys
import subprocess
import glob
import re
import shutil

# 尝试导入 yt_dlp
try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False


# ─────────────────────────────────────────────
# 依赖检查
# ─────────────────────────────────────────────

FFMPEG_KNOWN_PATH = r"D:\openclaw\workspace\video-downloader\bin\ffmpeg-7.1-essentials_build\bin\ffmpeg.exe"

def get_ffmpeg_path():
    """获取 FFmpeg 路径"""
    if shutil.which("ffmpeg"):
        return shutil.which("ffmpeg")
    if os.path.isfile(FFMPEG_KNOWN_PATH):
        return FFMPEG_KNOWN_PATH
    return "ffmpeg"  # 默认尝试系统 PATH


def check_dependencies():
    """检查依赖是否满足"""
    errors = []
    
    if not YTDLP_AVAILABLE:
        errors.append("yt-dlp 未安装 → pip install yt-dlp")
    
    ffmpeg = get_ffmpeg_path()
    if not ffmpeg:
        errors.append("ffmpeg 未安装 → https://ffmpeg.org/download.html")
    
    return errors


# ─────────────────────────────────────────────
# 下载核心
# ─────────────────────────────────────────────

def build_ydl_opts(output_dir, language, quality, cookies=None, cookies_from_browser=None):
    """构建 yt-dlp 配置"""
    
    # tv 客户端：对 Kids 内容友好
    PLAYER_CLIENTS = ["tv", "web"]
    
    ffmpeg_path = get_ffmpeg_path()
    
    format_map = {
        "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best",
        "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best[height<=1080]",
        "720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]",
        "480p": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best[height<=480]",
    }
    
    lang_list = [l.strip() for l in language.split(",")]
    
    opts = {
        "format": format_map.get(quality, format_map["best"]),
        "merge_output_format": "mp4",
        # 指定 ffmpeg 路径（确保是目录）
        "ffmpeg_location": os.path.dirname(ffmpeg_path) if ffmpeg_path and os.path.isfile(ffmpeg_path) else (ffmpeg_path if ffmpeg_path else "."),
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        # 添加 merger 后处理器确保合并
        "postprocessors": [{
            "key": "FFmpegMerger",
            "preferedformat": "mp4",
        }],
        
        # 字幕
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": lang_list,
        "subtitlesformat": "srt/vtt/best",
        
        "extractor_args": {
            "youtube": {
                "player_client": PLAYER_CLIENTS,
            }
        },
        
        "age_limit": None,
        "retries": 5,
        "fragment_retries": 5,
        "ignoreerrors": True,
        "noplaylist": False,
        "windowsfilenames": True,
    }
    
    if cookies:
        opts["cookiefile"] = cookies
    elif cookies_from_browser:
        opts["cookiesfrombrowser"] = (cookies_from_browser, None, None, None)
    
    return opts


def _progress_hook(d):
    """下载进度回调"""
    if d["status"] == "downloading":
        pct = d.get("_percent_str", "?%").strip()
        speed = d.get("_speed_str", "?").strip()
        eta = d.get("_eta_str", "?").strip()
        print(f"\r  ⬇️  {pct}  速度: {speed}  剩余: {eta}    ", end="", flush=True)
    elif d["status"] == "finished":
        print(f"\r  ✅ 下载完成{'':30}")


def download_video_and_subtitles(url, output_dir, language, quality,
                                 cookies=None, cookies_from_browser=None):
    """下载视频和字幕"""
    
    if not YTDLP_AVAILABLE:
        print("❌ yt-dlp 未安装")
        return []
    
    os.makedirs(output_dir, exist_ok=True)
    opts = build_ydl_opts(output_dir, language, quality, cookies, cookies_from_browser)
    opts["progress_hooks"] = [_progress_hook]
    
    downloaded = []
    print(f"\n📥 开始下载: {url}\n")
    
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
        except Exception as e:
            print(f"\n❌ 下载失败: {e}")
            return []
    
    if info is None:
        return []
    
    entries = info.get("entries") or [info]
    
    for entry in entries:
        if entry is None:
            continue
        title = sanitize_filename(entry.get("title", "unknown"))
        video_path = find_file(output_dir, title, [".mp4", ".mkv", ".webm"])
        subtitle_files = find_subtitles(output_dir, title)
        
        downloaded.append({
            "title": title,
            "video": video_path,
            "subtitles": subtitle_files,
        })
        
        print(f"\n✅ {title}")
        if subtitle_files:
            for sf in subtitle_files:
                print(f"   📄 {os.path.basename(sf)}")
        else:
            print("   ⚠️  未找到字幕")
    
    return downloaded


# ─────────────────────────────────────────────
# 字幕处理
# ─────────────────────────────────────────────

def convert_vtt_to_srt(vtt_path):
    """VTT 转 SRT"""
    srt_path = re.sub(r"\.vtt$", ".srt", vtt_path)
    with open(vtt_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    lines = content.split("\n")
    srt_lines = []
    index = 1
    i = 0
    
    while i < len(lines) and "-->" not in lines[i]:
        i += 1
    
    while i < len(lines):
        line = lines[i].strip()
        if "-->" in line:
            time_line = line.replace(".", ",", 2)
            time_line = re.split(r"\s+(align|position|line|size):", time_line)[0]
            srt_lines.append(str(index))
            srt_lines.append(time_line)
            index += 1
            i += 1
            texts = []
            while i < len(lines) and lines[i].strip():
                txt = re.sub(r"<[^>]+>", "", lines[i].strip())
                if txt:
                    texts.append(txt)
                i += 1
            if texts:
                srt_lines.extend(texts)
                srt_lines.append("")
        else:
            i += 1
    
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))
    return srt_path


def select_best_subtitle(files, preferred_langs):
    """选择最佳字幕"""
    if not files:
        return None
    for lang in preferred_langs:
        for f in files:
            if f".{lang}." in f or f".{lang.lower()}." in f:
                return f
    return files[0]


# ─────────────────────────────────────────────
# 字幕翻译 & 双语合并
# ─────────────────────────────────────────────

def _parse_srt(srt_path):
    """解析 SRT 文件"""
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    blocks = []
    raw = re.split(r"\n\s*\n", content.strip())
    for block in raw:
        lines = block.strip().splitlines()
        if len(lines) < 2:
            continue
        idx = lines[0].strip()
        time_line = lines[1].strip()
        text_lines = [l.strip() for l in lines[2:] if l.strip()]
        if "-->" in time_line and text_lines:
            blocks.append({"index": idx, "time": time_line, "lines": text_lines})
    return blocks


def _translate_google_single(text, target="zh-CN"):
    """翻译单条文本"""
    import urllib.request
    import urllib.parse
    import json
    
    params = urllib.parse.urlencode({
        "client": "gtx", "sl": "auto", "tl": target, "dt": "t", "q": text,
    })
    url = f"https://translate.googleapis.com/translate_a/single?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return "".join(item[0] for item in data[0] if item[0]).strip()
    except Exception:
        return text


def _translate_google(texts, target="zh-CN", batch_size=30):
    """批量翻译"""
    import urllib.request
    import urllib.parse
    import json
    import time
    
    SEPARATOR = " ||| "
    results = []
    i = 0
    
    while i < len(texts):
        batch = texts[i:i + batch_size]
        joined = SEPARATOR.join(batch)
        
        success = False
        for attempt in range(3):
            try:
                params = urllib.parse.urlencode({
                    "client": "gtx", "sl": "auto", "tl": target, "dt": "t", "q": joined,
                })
                url = f"https://translate.googleapis.com/translate_a/single?{params}"
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                translated = "".join(item[0] for item in data[0] if item[0])
                parts = translated.split(SEPARATOR)
                
                if len(parts) == len(batch):
                    results.extend(p.strip() for p in parts)
                    success = True
                    break
                else:
                    while len(parts) < len(batch):
                        parts.append("")
                    results.extend(p.strip() for p in parts[:len(batch)])
                    success = True
                    break
            except Exception:
                if attempt < 2:
                    time.sleep(1 + attempt)
        
        if not success:
            for text in batch:
                zh = _translate_google_single(text, target)
                results.append(zh)
                time.sleep(0.2)
        
        i += batch_size
        if i < len(texts):
            time.sleep(0.5)
    
    return results


def translate_subtitle_to_bilingual(srt_path, target_lang="zh-CN"):
    """将字幕翻译为中英双语"""
    print(f"\n🌐 翻译字幕为中英双语...")
    blocks = _parse_srt(srt_path)
    
    if not blocks:
        print("  ⚠️ 字幕解析失败")
        return srt_path
    
    en_texts = [" ".join(b["lines"]) for b in blocks]
    print(f"  📝 共 {len(en_texts)} 条字幕，正在翻译...")
    
    zh_texts = _translate_google(en_texts, target=target_lang)
    print(f"  ✅ 翻译完成")
    
    # 生成双语 SRT
    out_lines = []
    for i, (block, zh) in enumerate(zip(blocks, zh_texts), 1):
        out_lines.append(str(i))
        out_lines.append(block["time"])
        out_lines.extend(block["lines"])
        if zh and zh != " ".join(block["lines"]):
            out_lines.append(zh)
        out_lines.append("")
    
    bilingual_path = re.sub(r"\.srt$", ".bilingual.srt", srt_path)
    with open(bilingual_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines))
    
    print(f"  💾 双语字幕已保存: {os.path.basename(bilingual_path)}")
    return bilingual_path


# ─────────────────────────────────────────────
# 字幕烧录
# ─────────────────────────────────────────────

def burn_subtitles(video_path, subtitle_path, output_path,
                   font_size=24, font_color="white", position="bottom"):
    """烧录字幕进视频"""
    
    if not os.path.exists(video_path):
        print(f"❌ 视频不存在: {video_path}")
        return False
    if not os.path.exists(subtitle_path):
        print(f"❌ 字幕不存在: {subtitle_path}")
        return False
    
    # VTT → SRT
    if subtitle_path.endswith(".vtt"):
        print("  🔄 VTT → SRT 转换...")
        subtitle_path = convert_vtt_to_srt(subtitle_path)
    
    color_map = {
        "white": "&HFFFFFF&",
        "yellow": "&H00FFFF&",
        "cyan": "&HFFFF00&",
    }
    fc = color_map.get(font_color.lower(), "&HFFFFFF&")
    margin_v = {"bottom": "15", "top": "-15", "center": "0"}.get(position, "15")
    
    sub_escaped = subtitle_path.replace("\\", "/")
    if re.match(r"^[A-Za-z]:", sub_escaped):
        sub_escaped = sub_escaped.replace(":", "\\:", 1)
    
    vf = (
        f"subtitles='{sub_escaped}'"
        f":force_style='FontSize={font_size}"
        f",PrimaryColour={fc}"
        f",OutlineColour=&H000000&"
        f",Outline=2"
        f",Shadow=1"
        f",MarginV={margin_v}'"
    )
    
    ffmpeg = get_ffmpeg_path() or "ffmpeg"
    cmd = [
        ffmpeg, "-y",
        "-i", video_path,
        "-vf", vf,
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "medium",
        "-c:a", "copy",
        output_path,
    ]
    
    print(f"\n🔥 烧录字幕...")
    print(f"   输入: {os.path.basename(video_path)}")
    print(f"   字幕: {os.path.basename(subtitle_path)}")
    print(f"   输出: {os.path.basename(output_path)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode == 0:
        size_mb = os.path.getsize(output_path) / 1024 / 1024
        print(f"   ✅ 完成！文件大小: {size_mb:.1f} MB")
        return True
    else:
        print(f"   ❌ ffmpeg 错误:\n{result.stderr[-1000:]}")
        return False


# ─────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()


def find_file(directory, title, exts):
    # 首先精确匹配
    for ext in exts:
        path = os.path.join(directory, f"{title}{ext}")
        if os.path.exists(path):
            return path
    
    # 尝试模糊匹配（可能文件名有变化）
    title_clean = title.replace(" ", "").replace("-", "")
    for ext in exts:
        for f in os.listdir(directory):
            if f.endswith(ext):
                # 检查标题是否包含在文件名中
                f_clean = f.replace(" ", "").replace("-", "").replace("_", "")
                if title_clean.lower() in f_clean.lower() or f.lower().startswith(title.split()[0].lower()):
                    return os.path.join(directory, f)
    
    # 最后找最新的 mp4 文件
    for ext in exts:
        matches = glob.glob(os.path.join(directory, f"*{ext}"))
        if matches:
            # 排除分段文件
            for m in matches:
                if "part" not in m.lower() and "fragment" not in m.lower():
                    return m
            return matches[0]
    return None


def find_subtitles(directory, title):
    files = []
    for pat in ["*.srt", "*.vtt", "*.ass"]:
        files.extend(glob.glob(os.path.join(directory, f"{title}.{pat}")))
    return files


# ─────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────

def process_video(url, output_dir, language="zh-Hans,zh,en", quality="720p",
                  cookies=None, cookies_from_browser=None,
                  burn_subtitle=False, bilingual=False,
                  font_size=24, font_color="white", position="bottom"):
    """
    下载并处理视频
    
    Args:
        url: YouTube URL
        output_dir: 输出目录
        language: 字幕语言
        quality: 视频质量
        cookies: cookies.txt 文件路径
        cookies_from_browser: 从浏览器读取 cookie (chrome/firefox/edge)
        burn_subtitle: 是否烧录字幕
        bilingual: 是否翻译为双语字幕
        font_size: 字幕大小
        font_color: 字幕颜色
        position: 字幕位置
    
    Returns:
        list: 下载/处理结果
    """
    # 检查依赖
    errors = check_dependencies()
    if errors:
        print("❌ 依赖检查失败:")
        for e in errors:
            print(f"   {e}")
        return []
    
    downloaded = download_video_and_subtitles(
        url=url,
        output_dir=output_dir,
        language=language,
        quality=quality,
        cookies=cookies,
        cookies_from_browser=cookies_from_browser,
    )
    
    if not downloaded:
        print("❌ 没有下载到任何视频")
        return []
    
    if not burn_subtitle:
        return downloaded
    
    # 烧录字幕
    lang_list = [l.strip() for l in language.split(",")]
    ok = 0
    
    for item in downloaded:
        title = item["title"]
        video = item["video"]
        subs = item["subtitles"]
        
        print(f"\n{'─'*60}")
        print(f"📹 {title}")
        
        if not video or not os.path.exists(video):
            print("   ⚠️ 找不到视频文件，跳过")
            continue
        
        sub = select_best_subtitle(subs, lang_list)
        if not sub:
            print("   ⚠️ 无字幕，跳过烧录")
            continue
        
        # VTT → SRT
        if sub.endswith(".vtt"):
            sub = convert_vtt_to_srt(sub)
        
        # 翻译为双语
        if bilingual:
            sub = translate_subtitle_to_bilingual(sub, target_lang="zh-CN")
        
        out = os.path.join(output_dir, f"{title}_字幕烧录.mp4")
        success = burn_subtitles(
            video_path=video,
            subtitle_path=sub,
            output_path=out,
            font_size=font_size,
            font_color=font_color,
            position=position,
        )
        if success:
            ok += 1
    
    print(f"\n{'═'*60}")
    print(f"🎉 完成！成功烧录 {ok}/{len(downloaded)} 个视频")
    print(f"📁 输出目录: {os.path.abspath(output_dir)}")
    
    return downloaded
