"""
TikTok Ripper - YouTube 视频搬运工具
主程序入口
跨平台支持: Windows, macOS, Linux
"""
import os
import sys
import argparse
import math
import platform
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import downloader
import processor
import auto_subtitle
import ai_generator
import config
import youtube_kids
import utils

# 尝试导入翻译模块，如果失败则禁用翻译功能
try:
    import translate_srt
    TRANSLATE_SRT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 翻译模块不可用: {e}")
    print("   请运行: pip install deep-translator")
    TRANSLATE_SRT_AVAILABLE = False


def print_banner():
    """打印欢迎信息"""
    system = utils.get_system()
    emoji = {"windows": "🪟", "darwin": "🍎", "linux": "🐧"}.get(system, "💻")
    
    banner = f"""
    ╔═══════════════════════════════════════╗
    ║       TikTok Ripper v1.0              ║
    ║   YouTube -> TikTok 搬运工具          ║
    ║   跨平台: Windows / macOS / Linux    ║
    ╚═══════════════════════════════════════╝
    {emoji} 当前系统: {platform.system()} {platform.release()}
    """
    print(banner)


def menu():
    """主菜单"""
    while True:
        print("\n" + "="*50)
        print("📺 TikTok Ripper - 主菜单")
        print("="*50)
        print("1. 🔍 搜索 YouTube 视频")
        print("2. ⬇️  下载单个视频")
        print("3. 📂 下载播放列表")
        print("4. ✂️  切片视频 (长视频 -> 多个短片)")
        print("5. 🔄 处理单个视频 (转码+去重+尺寸)")
        print("6. 🚀 一键搬运 (下载+处理)")
        print("7. 🎬 自动字幕 (Whisper)")
        print("8. ✨ AI 生成标题/描述")
        print("9. ⚙️  查看/修改配置")
        print("10. 📝 翻译字幕 (英译中 -> 中英双语)")
        print("11. 📥 下载 YouTube 字幕")
        print("12. 🧒 YouTube Kids 下载 (儿童视频)")
        print("0. ❌ 退出")
        print("="*50)
        
        choice = input("请选择: ").strip()
        
        if choice == "1":
            search_videos()
        elif choice == "2":
            download_single()
        elif choice == "3":
            download_playlist()
        elif choice == "4":
            slice_video()
        elif choice == "5":
            process_single()
        elif choice == "6":
            one_click_rip()
        elif choice == "7":
            auto_subtitle_menu()
        elif choice == "8":
            ai_generate_menu()
        elif choice == "9":
            show_config()
        elif choice == "10":
            translate_subtitle_menu()
        elif choice == "11":
            download_subtitle_only()
        elif choice == "12":
            download_youtube_kids()
        elif choice == "0":
            print("👋 再见!")
            break
        else:
            print("❌ 无效选择")


def search_videos():
    """搜索视频"""
    print("\n--- 搜索 YouTube ---")
    query = input("输入搜索关键词: ").strip()
    
    if not query:
        print("❌ 关键词不能为空")
        return
    
    videos = downloader.search_youtube(query, max_results=10)
    
    if videos:
        print("\n搜索结果:")
        for i, v in enumerate(videos):
            print(f"{i+1}. {v['title']}")
            print(f"   时长: {v['duration']}秒 | 作者: {v['uploader']}")
            print(f"   链接: {v['url']}")
            print()
        
        # 选择下载
        try:
            idx = int(input("选择要下载的视频编号 (0=返回): "))
            if 1 <= idx <= len(videos):
                url = videos[idx-1]['url']
                filepath = downloader.download_video(
                    url, 
                    config.DOWNLOAD_DIR
                )
                if filepath:
                    print(f"✅ 下载完成: {filepath}")
        except ValueError:
            pass
    else:
        print("❌ 未找到视频")


def download_single():
    """下载单个视频"""
    print("\n--- 下载单个视频 ---")
    url = input("输入 YouTube URL: ").strip()
    
    if not url:
        print("❌ URL 不能为空")
        return
    
    # Cookie
    cookie_file = None
    if hasattr(config, 'COOKIE_FILE') and config.COOKIE_FILE:
        cookie_path = config.COOKIE_FILE
        if os.path.exists(cookie_path):
            cookie_file = cookie_path
    
    # 获取视频信息
    info = downloader.get_video_info(url, cookie_file=cookie_file)
    if not info:
        print("❌ 无法获取视频信息")
        return
    
    print(f"   标题: {info['title']}")
    print(f"   时长: {info['duration']}秒")
    
    # 估算视频大小
    est_size = downloader.get_video_size_estimate(url, cookie_file=cookie_file)
    if est_size:
        print(f"   预估大小: ~{est_size:.1f} MB")
    
    # 选择清晰度
    print("\n请选择视频清晰度:")
    print("1. 🔥 1080P (高清)")
    print("2. 📱 720P (流畅)")
    print("3. ⭐ 默认 (最佳质量)")
    
    quality_choice = input("选择 (1/2/3，默认3): ").strip()
    if quality_choice == "1":
        quality = "1080p"
    elif quality_choice == "2":
        quality = "720p"
    else:
        quality = None
    
    if quality:
        print(f"   已选择: {quality}")
    
    # 下载
    print("\n开始下载...")
    filepath = downloader.download_video(
        url, 
        config.DOWNLOAD_DIR,
        cookie_file,
        quality=quality
    )
    
    if filepath:
        print(f"\n✅ 下载完成!")
        print(f"   文件: {filepath}")
        
        # 询问是否处理
        ask = input("\n是否处理这个视频? (y/n): ").strip().lower()
        if ask == 'y':
            output = processor.process_video(
                filepath,
                config.OUTPUT_DIR,
                add_subtitles=config.ADD_SUBTITLE,
                change_speed_dedup=config.CHANGE_SPEED,
                target_width=config.TIKTOK_WIDTH,
                target_height=config.TIKTOK_HEIGHT
            )
            if output:
                print(f"✅ 处理完成: {output}")


def download_subtitle_only():
    """单独下载字幕"""
    print("\n--- 📥 下载 YouTube 字幕 ---")
    url = input("输入 YouTube URL: ").strip()
    
    if not url:
        print("❌ URL 不能为空")
        return
    
    # Cookie
    cookie_file = None
    if hasattr(config, 'COOKIE_FILE') and config.COOKIE_FILE:
        cookie_path = config.COOKIE_FILE
        if os.path.exists(cookie_path):
            cookie_file = cookie_path
    
    # 获取视频信息
    info = downloader.get_video_info(url, cookie_file=cookie_file)
    if info:
        print(f"   标题: {info['title']}")
        print(f"   时长: {info['duration']}秒")
    
    # 单独下载字幕
    print("\n开始下载字幕...")
    subtitle_path = downloader.download_subtitles_only(
        url, 
        config.DOWNLOAD_DIR,
        cookie_file,
        max_retries=3
    )
    
    if subtitle_path:
        print(f"\n✅ 字幕下载完成!")
        print(f"   文件: {subtitle_path}")
    else:
        print("❌ 字幕下载失败")


def download_playlist():
    """下载播放列表"""
    print("\n--- 下载播放列表 ---")
    url = input("输入 YouTube 播放列表 URL: ").strip()
    
    if not url:
        print("❌ URL 不能为空")
        return
    
    limit = input("最大下载数量 (默认10): ").strip()
    limit = int(limit) if limit.isdigit() else 10
    
    # 选择清晰度
    print("\n请选择视频清晰度:")
    print("1. 🔥 1080P (高清)")
    print("2. 📱 720P (流畅)")
    print("3. ⭐ 默认 (最佳质量)")
    
    quality_choice = input("选择 (1/2/3，默认3): ").strip()
    if quality_choice == "1":
        quality = "1080p"
    elif quality_choice == "2":
        quality = "720p"
    else:
        quality = None
    
    # Cookie
    cookie_file = None
    if hasattr(config, 'COOKIE_FILE') and config.COOKIE_FILE:
        cookie_path = config.COOKIE_FILE
        if os.path.exists(cookie_path):
            cookie_file = cookie_path
    
    videos = downloader.download_playlist(
        url,
        config.DOWNLOAD_DIR,
        limit,
        cookie_file,
        quality
    )
    
    if videos:
        print(f"\n✅ 下载完成，共 {len(videos)} 个视频")
        print(f"   保存位置: {os.path.abspath(config.DOWNLOAD_DIR)}")


def slice_video():
    """切片视频"""
    print("\n--- 视频切片 ---")
    
    # 列出下载目录的视频
    if not os.path.exists(config.DOWNLOAD_DIR):
        print("❌ 下载目录为空，请先下载视频")
        return
    
    videos = [f for f in os.listdir(config.DOWNLOAD_DIR) 
              if f.endswith(('.mp4', '.webm', '.mkv'))]
    
    if not videos:
        print("❌ 下载目录中没有视频文件")
        return
    
    print("可用视频:")
    for i, v in enumerate(videos):
        print(f"{i+1}. {v}")
    
    try:
        idx = int(input("\n选择要切片的视频编号: "))
        if 1 <= idx <= len(videos):
            input_file = os.path.join(config.DOWNLOAD_DIR, videos[idx-1])
            
            # 获取视频信息
            info = processor.get_video_info(input_file)
            if info:
                duration = info['duration']
                print(f"视频时长: {duration}秒")
                
                # 计算推荐的切片数量
                if duration <= 45:
                    recommended = 1
                elif duration <= 90:
                    recommended = 2
                elif duration <= 135:
                    recommended = 3
                else:
                    recommended = max(math.ceil(duration / 40), 1)
                
                print(f"推荐切片: {recommended} 段 (每段约 {duration/recommended:.1f} 秒)")
            
            # 询问切片数量
            num_clips_input = input("\n输入切片数量 (直接回车使用自动计算): ").strip()
            num_clips = None
            if num_clips_input:
                try:
                    num_clips = int(num_clips_input)
                    print(f"将视频切成 {num_clips} 段")
                except ValueError:
                    print("无效输入，将使用自动计算")
            
            # 切片
            clips = processor.auto_slice_video(
                input_file,
                config.OUTPUT_DIR,
                min_duration=config.TIKTOK_MIN_DURATION,
                max_duration=config.TIKTOK_MAX_DURATION,
                target_width=config.TIKTOK_WIDTH,
                target_height=config.TIKTOK_HEIGHT,
                num_clips=num_clips
            )
            
            if clips:
                print(f"\n✅ 切片完成! 共 {len(clips)} 个片段")
                print(f"   保存位置: {os.path.abspath(config.OUTPUT_DIR)}")
    except ValueError:
        print("❌ 无效选择")


def process_single():
    """处理单个视频"""
    print("\n--- 处理单个视频 ---")
    
    # 列出可用视频
    search_dirs = [config.DOWNLOAD_DIR, config.OUTPUT_DIR, "."]
    videos = []
    
    for d in search_dirs:
        if os.path.exists(d):
            for f in os.listdir(d):
                if f.endswith(('.mp4', '.webm', '.mkv')):
                    videos.append(os.path.join(d, f))
    
    if not videos:
        print("❌ 没有可处理的视频")
        return
    
    print("可用视频:")
    for i, v in enumerate(videos):
        print(f"{i+1}. {v}")
    
    try:
        idx = int(input("\n选择要处理的视频编号: "))
        if 1 <= idx <= len(videos):
            input_file = videos[idx-1]
            
            output = processor.process_video(
                input_file,
                config.OUTPUT_DIR,
                add_subtitles=config.ADD_SUBTITLE,
                change_speed_dedup=config.CHANGE_SPEED,
                target_width=config.TIKTOK_WIDTH,
                target_height=config.TIKTOK_HEIGHT
            )
            
            if output:
                print(f"\n✅ 处理完成: {output}")
    except ValueError:
        print("❌ 无效选择")


def one_click_rip():
    """一键搬运"""
    print("\n--- 一键搬运 ---")
    url = input("输入 YouTube URL: ").strip()
    
    if not url:
        print("❌ URL 不能为空")
        return
    
    # Cookie
    cookie_file = None
    if hasattr(config, 'COOKIE_FILE') and config.COOKIE_FILE:
        cookie_path = config.COOKIE_FILE
        if os.path.exists(cookie_path):
            cookie_file = cookie_path
    
    # 获取视频信息
    info = downloader.get_video_info(url, cookie_file=cookie_file)
    if info:
        print(f"   标题: {info['title']}")
        print(f"   时长: {info['duration']}秒")
        
        # 估算大小
        est_size = downloader.get_video_size_estimate(url, cookie_file=cookie_file)
        if est_size:
            print(f"   预估大小: ~{est_size:.1f} MB")
    
    # 选择清晰度
    print("\n请选择视频清晰度:")
    print("1. 🔥 1080P (高清)")
    print("2. 📱 720P (流畅)")
    print("3. ⭐ 默认 (最佳质量)")
    
    quality_choice = input("选择 (1/2/3，默认3): ").strip()
    if quality_choice == "1":
        quality = "1080p"
    elif quality_choice == "2":
        quality = "720p"
    else:
        quality = None
    
    if quality:
        print(f"   已选择: {quality}")
    
    if cookie_file:
        print(f"[INFO] 使用 Cookie: {cookie_file}")
    
    # 1. 下载
    print("\n[1/3] 下载视频...")
    filepath = downloader.download_video(
        url,
        config.DOWNLOAD_DIR,
        cookie_file,
        quality=quality
    )
    
    if not filepath:
        print("❌ 下载失败")
        return
    
    # 2. 切片
    print("\n[2/3] 切片处理...")
    clips = processor.auto_slice_video(
        filepath,
        config.OUTPUT_DIR,
        min_duration=config.TIKTOK_MIN_DURATION,
        max_duration=config.TIKTOK_MAX_DURATION,
        target_width=config.TIKTOK_WIDTH,
        target_height=config.TIKTOK_HEIGHT
    )
    
    if not clips:
        print("⚠️ 切片失败，尝试处理整个视频...")
        output = processor.process_video(
            filepath,
            config.OUTPUT_DIR,
            add_subtitles=config.ADD_SUBTITLE,
            change_speed_dedup=config.CHANGE_SPEED,
            target_width=config.TIKTOK_WIDTH,
            target_height=config.TIKTOK_HEIGHT
        )
        if output:
            clips = [output]
    
    # 3. 完成
    print("\n[3/3] 完成!")
    if clips:
        print(f"\n✅ 搬运成功! 共 {len(clips)} 个视频")
        print(f"   保存位置: {os.path.abspath(config.OUTPUT_DIR)}")
        
        # 显示文件列表
        print("\n生成的文件:")
        for c in clips:
            print(f"   📹 {os.path.basename(c)}")
    else:
        print("❌ 处理失败")


def auto_subtitle_menu():
    """自动字幕生成"""
    print("\n--- 🎬 自动字幕生成 (Whisper) ---")
    
    # 列出可用视频
    search_dirs = [config.DOWNLOAD_DIR, config.OUTPUT_DIR, "."]
    videos = []
    
    for d in search_dirs:
        if os.path.exists(d):
            for f in os.listdir(d):
                if f.endswith(('.mp4', '.webm', '.mkv')):
                    videos.append(os.path.join(d, f))
    
    if not videos:
        print("❌ 没有可处理的视频")
        return
    
    print("可用视频:")
    for i, v in enumerate(videos):
        print(f"{i+1}. {os.path.basename(v)}")
    
    try:
        idx = int(input("\n选择视频编号: "))
        if 1 <= idx <= len(videos):
            input_file = videos[idx-1]
            
            print("\n请选择字幕类型:")
            print("1. 🇺🇸 英文字幕")
            print("2. 🇨🇳 中文字幕")  
            print("3. 🇨🇳+🇺🇸 中英双字幕")
            
            subtitle_type = input("选择: ").strip()
            
            print("\n请选择操作:")
            print("1. 🎤 生成字幕 (仅生成 SRT 文件)")
            print("2. 🔥 烧录字幕 (烧录到视频中)")
            print("3. 📝 生成+烧录 (一步到位)")
            
            op = input("选择: ").strip()
            
            # 确定语言
            if subtitle_type == "1":
                lang = "en"
                print("已选择: 英文字幕")
            elif subtitle_type == "2":
                lang = "zh"
                print("已选择: 中文字幕")
            elif subtitle_type == "3":
                lang = "en"  # 先生成英文字幕，再翻译
                print("已选择: 中英双字幕")
            else:
                lang = None
                print("默认: 自动检测语言")
            
            if op == "1":
                # 仅生成字幕
                srt_file = auto_subtitle.generate_subtitles(input_file, language=lang)
                if srt_file:
                    print(f"\n✅ 字幕生成完成: {srt_file}")
                    
            elif op == "2":
                # 烧录字幕 - 让用户选择字幕文件
                print("\n请选择字幕文件:")
                
                # 搜索可能的字幕文件位置
                search_dirs = [config.DOWNLOAD_DIR, config.OUTPUT_DIR, "."]
                srt_files = []
                
                for d in search_dirs:
                    if os.path.exists(d):
                        for f in os.listdir(d):
                            if f.endswith('.srt'):
                                srt_files.append(os.path.join(d, f))
                
                if not srt_files:
                    print("❌ 未找到任何 .srt 字幕文件，请先生成字幕")
                    return
                
                print("可用字幕文件:")
                for i, s in enumerate(srt_files):
                    print(f"{i+1}. {os.path.basename(s)}")
                
                print(f"{len(srt_files)+1}. 🔍 自定义路径 (手动输入)")
                
                try:
                    srt_idx = int(input("\n选择字幕文件编号: "))
                    if 1 <= srt_idx <= len(srt_files):
                        srt_file = srt_files[srt_idx - 1]
                    elif srt_idx == len(srt_files) + 1:
                        # 自定义路径
                        custom_path = input("输入字幕文件完整路径: ").strip().strip('"')
                        if os.path.exists(custom_path) and custom_path.endswith('.srt'):
                            srt_file = custom_path
                        else:
                            print("❌ 文件不存在或不是 SRT 文件")
                            return
                    else:
                        print("❌ 无效选择")
                        return
                    
                    print(f"已选择字幕: {os.path.basename(srt_file)}")
                    
                    output_file = input_file.replace('.mp4', '_subtitled.mp4')
                    result = auto_subtitle.burn_subtitles(input_file, srt_file, output_file)
                    if result:
                        print(f"\n✅ 字幕烧录完成: {result}")
                except ValueError:
                    print("❌ 无效选择")
                    return
                    
            elif op == "3":
                # 一步到位 - 支持中英双字幕
                if subtitle_type == "3":
                    # 中英双字幕
                    print("\n⏳ 步骤1: 生成英文字幕...")
                    srt_en = auto_subtitle.generate_subtitles(input_file, language="en")
                    
                    if srt_en:
                        print("⏳ 步骤2: 生成中文字幕...")
                        srt_zh = auto_subtitle.generate_subtitles(input_file, language="zh")
                        
                        if srt_zh:
                            print("⏳ 步骤3: 合并中英字幕...")
                            srt_bilingual = auto_subtitle.merge_subtitles(srt_en, srt_zh)
                            
                            if srt_bilingual:
                                print("⏳ 步骤4: 烧录到视频...")
                                output_file = input_file.replace('.mp4', '_bilingual.mp4')
                                result = auto_subtitle.burn_subtitles(input_file, srt_bilingual, output_file)
                                if result:
                                    print(f"\n✅ 中英双字幕烧录完成: {result}")
                            else:
                                print("❌ 字幕合并失败")
                        else:
                            print("❌ 中文字幕生成失败")
                    else:
                        print("❌ 英文字幕生成失败")
                else:
                    # 单字幕
                    srt_file = auto_subtitle.generate_subtitles(input_file, language=lang)
                    
                    if srt_file:
                        print("⏳ 正在烧录字幕...")
                        output_file = input_file.replace('.mp4', '_subtitled.mp4')
                        result = auto_subtitle.burn_subtitles(input_file, srt_file, output_file)
                        if result:
                            print(f"\n✅ 完成! 视频已保存: {result}")
            else:
                print("❌ 无效选择")
                
    except ValueError:
        print("❌ 无效选择")


def ai_generate_menu():
    """AI 生成标题和描述"""
    print("\n--- AI 生成标题/描述 ---")
    
    # 列出可用视频
    search_dirs = [config.DOWNLOAD_DIR, config.OUTPUT_DIR, "."]
    videos = []
    
    for d in search_dirs:
        if os.path.exists(d):
            for f in os.listdir(d):
                if f.endswith(('.mp4', '.webm', '.mkv')):
                    videos.append(os.path.join(d, f))
    
    if not videos:
        print("❌ 没有可处理的视频")
        return
    
    print("可用视频:")
    for i, v in enumerate(videos):
        print(f"{i+1}. {os.path.basename(v)}")
    
    try:
        idx = int(input("\n选择视频编号: "))
        if 1 <= idx <= len(videos):
            input_file = videos[idx-1]
            
            # 获取视频信息
            info = processor.get_video_info(input_file)
            duration = info['duration'] if info else 60
            
            # 获取视频标题 (从文件名)
            title = os.path.basename(input_file).split('.')[0]
            
            # 生成标题和描述
            result = ai_generator.generate_title_and_description(
                video_title=title,
                video_duration=duration
            )
            
            print("\n" + "="*50)
            print("📝 生成的标题:")
            for i, t in enumerate(result.get('titles', [result['title']])):
                print(f"   {i+1}. {t}")
            
            print(f"\n📄 描述:\n{result['description']}")
            
            print(f"\n🏷️ 标签: {', '.join(result['tags'])}")
            print("="*50)
            
    except ValueError:
        print("❌ 无效选择")


def show_config():
    """显示/修改配置"""
    print("\n--- 当前配置 ---")
    print(f"下载目录: {config.DOWNLOAD_DIR}")
    print(f"输出目录: {config.OUTPUT_DIR}")
    print(f"YouTube 画质: {config.YOUTUBE_QUALITY}")
    print(f"抖音尺寸: {config.TIKTOK_WIDTH}x{config.TIKTOK_HEIGHT}")
    print(f"切片时长: {config.TIKTOK_MIN_DURATION}-{config.TIKTOK_MAX_DURATION}秒")
    print(f"添加字幕: {config.ADD_SUBTITLE}")
    print(f"去重调速: {config.CHANGE_SPEED}")
    print(f"转码质量 CRF: {config.CRF}")
    
    print("\n配置说明:")
    print("- 修改 config.py 文件可以更改配置")
    print("- 抖音竖版: 1080x1920")
    print("- 抖音横版: 1920x1080")
    print("- 画质可选: 2160p, 1080p, 720p, 480p")


def translate_subtitle_menu():
    """翻译字幕 - 英译中生成中英双语字幕"""
    if not TRANSLATE_SRT_AVAILABLE:
        print("\n❌ 翻译功能不可用")
        print("   请先安装依赖: pip install deep-translator")
        return
    
    print("\n--- 📝 翻译字幕 (英译中 -> 中英双语) ---")
    
    # 搜索字幕文件
    search_dirs = [config.DOWNLOAD_DIR, config.OUTPUT_DIR, "."]
    srt_files = []
    
    for d in search_dirs:
        if os.path.exists(d):
            for f in os.listdir(d):
                if f.endswith('.srt'):
                    srt_files.append(os.path.join(d, f))
    
    if not srt_files:
        print("❌ 未找到任何 .srt 字幕文件")
        return
    
    print("可用字幕文件:")
    for i, s in enumerate(srt_files):
        print(f"{i+1}. {os.path.basename(s)}")
    
    print(f"{len(srt_files)+1}. 🔍 自定义路径 (手动输入)")
    
    try:
        srt_idx = int(input("\n选择要翻译的字幕文件编号: "))
        if 1 <= srt_idx <= len(srt_files):
            input_srt = srt_files[srt_idx - 1]
        elif srt_idx == len(srt_files) + 1:
            custom_path = input("输入字幕文件完整路径: ").strip().strip('"')
            if os.path.exists(custom_path) and custom_path.endswith('.srt'):
                input_srt = custom_path
            else:
                print("❌ 文件不存在或不是 SRT 文件")
                return
        else:
            print("❌ 无效选择")
            return
        
        print(f"\n已选择: {os.path.basename(input_srt)}")
        
        # 解析字幕
        print("解析字幕文件...")
        subtitles = translate_srt.parse_srt(input_srt)
        print(f"共 {len(subtitles)} 条字幕")
        
        # 生成输出路径
        output_srt = input_srt.replace('.srt', '_bilingual.srt')
        
        # 确认覆盖
        if os.path.exists(output_srt):
            confirm = input(f"输出文件已存在: {os.path.basename(output_srt)}，是否覆盖? (y/n): ").strip().lower()
            if confirm != 'y':
                print("已取消")
                return
        
        # 开始翻译
        print("\n开始翻译...")
        print("(每10条暂停1秒，避免API限流)")
        
        count = translate_srt.create_bilingual_srt(subtitles, output_srt)
        
        print(f"\n✅ 翻译完成! 双语字幕已保存: {output_srt}")
        print(f"   共处理 {count} 条字幕")
        
    except ValueError:
        print("❌ 无效选择")


def download_youtube_kids():
    """YouTube Kids 视频下载 - 支持字幕烧录"""
    print("\n" + "="*50)
    print("🧒 YouTube Kids 视频下载")
    print("="*50)
    
    # 检查依赖
    errors = youtube_kids.check_dependencies()
    if errors:
        print("\n❌ 依赖检查失败:")
        for e in errors:
            print(f"   - {e}")
        print("\n请先安装依赖:")
        print("   pip install yt-dlp")
        print("   下载 ffmpeg: https://ffmpeg.org/download.html")
        return
    
    # 输入 URL
    print("\n支持: 单个视频、播放列表、频道 URL")
    print("示例: https://www.youtube.com/@disneyjr")
    url = input("\n输入 YouTube URL: ").strip()
    
    if not url:
        print("❌ URL 不能为空")
        return
    
    # 输出目录
    output_dir = os.path.join(config.DOWNLOAD_DIR, "youtube_kids")
    os.makedirs(output_dir, exist_ok=True)
    
    # 选择认证方式
    print("\n--- 认证方式 ---")
    print("1. 🍪 使用 cookies.txt 文件")
    print("2. 🌐 从浏览器读取 Cookie (Chrome)")
    print("3. 🔓 跳过 (普通视频可能可以)")
    
    auth_choice = input("选择 (1/2/3): ").strip()
    
    cookies = None
    cookies_from_browser = None
    
    if auth_choice == "1":
        # 使用 cookies.txt
        cookie_path = os.path.join(os.path.dirname(__file__), "cookies.txt")
        if os.path.exists(cookie_path):
            cookies = cookie_path
            print(f"   ✅ 使用: {cookie_path}")
        else:
            custom_path = input("   输入 cookies.txt 路径: ").strip()
            if os.path.exists(custom_path):
                cookies = custom_path
            else:
                print("   ❌ 文件不存在，将尝试无认证下载")
    
    elif auth_choice == "2":
        cookies_from_browser = "chrome"
        print("   ✅ 将从 Chrome 读取 Cookie")
    
    else:
        print("   ⚠️ 跳过认证")
    
    # 视频质量
    print("\n--- 视频质量 ---")
    print("1. 🔥 最佳画质")
    print("2. 📺 1080p")
    print("3. 📱 720p (推荐)")
    print("4. 💾 480p")
    
    quality_choice = input("选择 (1/2/3/4): ").strip()
    quality_map = {"1": "best", "2": "1080p", "3": "720p", "4": "480p"}
    quality = quality_map.get(quality_choice, "720p")
    
    # 字幕语言
    print("\n--- 字幕语言 ---")
    print("1. 🇨🇳 中文优先 (简体→繁体→英文)")
    print("2. 🇬🇧 英文")
    print("3. 🇯🇵 日文")
    
    lang_choice = input("选择 (1/2/3): ").strip()
    lang_map = {"1": "zh-Hans,zh-Hant,zh,en", "2": "en", "3": "ja"}
    language = lang_map.get(lang_choice, "zh-Hans,zh-Hant,zh,en")
    
    # 是否烧录字幕
    print("\n--- 字幕处理 ---")
    print("1. 🔥 烧录字幕进视频 (推荐)")
    print("2. 📄 仅下载字幕")
    print("3. ⏭️ 跳过字幕")
    
    subtitle_choice = input("选择 (1/2/3): ").strip()
    
    burn_subtitle = subtitle_choice == "1"
    bilingual = False
    
    if burn_subtitle:
        bilingual_input = input("   是否翻译为中英双语? (y/n): ").strip().lower()
        bilingual = bilingual_input == "y"
        
        # 字幕样式
        print("\n   字幕样式:")
        print("   1. 白色")
        print("   2. 黄色 (清晰)")
        print("   3. 青色")
        style_choice = input("   选择颜色 (1/2/3): ").strip()
        color_map = {"1": "white", "2": "yellow", "3": "cyan"}
        font_color = color_map.get(style_choice, "white")
        
        print("\n   字幕大小:")
        print("   1. 小 (20)")
        print("   2. 中 (26) ⭐")
        print("   3. 大 (32)")
        size_choice = input("   选择大小 (1/2/3): ").strip()
        size_map = {"1": "20", "2": "26", "3": "32"}
        font_size = int(size_map.get(size_choice, "26"))
    else:
        font_color = "white"
        font_size = 24
    
    # 开始下载
    print("\n" + "="*50)
    print("🚀 开始下载...")
    print("="*50)
    
    result = youtube_kids.process_video(
        url=url,
        output_dir=output_dir,
        language=language,
        quality=quality,
        cookies=cookies,
        cookies_from_browser=cookies_from_browser,
        burn_subtitle=burn_subtitle,
        bilingual=bilingual,
        font_size=font_size,
        font_color=font_color,
        position="bottom",
    )
    
    if result:
        print(f"\n✅ 下载完成!")
        print(f"   输出目录: {output_dir}")
    else:
        print("\n❌ 下载失败，请检查:")
        print("   - URL 是否正确")
        print("   - Cookie 是否有效 (如需登录)")
        print("   - 视频是否可访问")


def main():
    """主入口"""
    # 创建必要目录
    os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    os.makedirs(config.TEMP_DIR, exist_ok=True)
    
    print_banner()
    menu()


if __name__ == "__main__":
    main()
