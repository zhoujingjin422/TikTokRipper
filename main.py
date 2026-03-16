"""
TikTok Ripper - YouTube 视频搬运工具
主程序入口
"""
import os
import sys
import argparse
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import downloader
import processor
import auto_subtitle
import ai_generator
import config


def print_banner():
    """打印欢迎信息"""
    banner = """
    ╔═══════════════════════════════════════╗
    ║       TikTok Ripper v1.0              ║
    ║   YouTube -> TikTok 搬运工具          ║
    ╚═══════════════════════════════════════╝
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
    
    # 获取视频信息
    info = downloader.get_video_info(url)
    if not info:
        print("❌ 无法获取视频信息")
        return
    
    print(f"   标题: {info['title']}")
    print(f"   时长: {info['duration']}秒")
    
    # 估算视频大小
    est_size = downloader.get_video_size_estimate(url, cookie_file=None)
    if est_size:
        print(f"   预估大小: ~{est_size:.1f} MB")
    
    # Cookie
    cookie_file = None
    if hasattr(config, 'COOKIE_FILE') and config.COOKIE_FILE:
        cookie_path = config.COOKIE_FILE
        if os.path.exists(cookie_path):
            cookie_file = cookie_path
    
    # 下载
    print("\n开始下载...")
    filepath = downloader.download_video(
        url, 
        config.DOWNLOAD_DIR,
        cookie_file
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


def download_playlist():
    """下载播放列表"""
    print("\n--- 下载播放列表 ---")
    url = input("输入 YouTube 播放列表 URL: ").strip()
    
    if not url:
        print("❌ URL 不能为空")
        return
    
    limit = input("最大下载数量 (默认10): ").strip()
    limit = int(limit) if limit.isdigit() else 10
    
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
        cookie_file
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
                print(f"视频时长: {info['duration']}秒")
            
            # 切片
            clips = processor.auto_slice_video(
                input_file,
                config.OUTPUT_DIR,
                min_duration=config.TIKTOK_MIN_DURATION,
                max_duration=config.TIKTOK_MAX_DURATION,
                target_width=config.TIKTOK_WIDTH,
                target_height=config.TIKTOK_HEIGHT
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
    
    # 获取视频信息
    info = downloader.get_video_info(url)
    if info:
        print(f"   标题: {info['title']}")
        print(f"   时长: {info['duration']}秒")
        
        # 估算大小
        est_size = downloader.get_video_size_estimate(url, cookie_file=None)
        if est_size:
            print(f"   预估大小: ~{est_size:.1f} MB")
    
    # Cookie 文件
    cookie_file = None
    if hasattr(config, 'COOKIE_FILE') and config.COOKIE_FILE:
        cookie_path = config.COOKIE_FILE
        if os.path.exists(cookie_path):
            cookie_file = cookie_path
            print(f"[INFO] 使用 Cookie: {cookie_path}")
    
    # 1. 下载
    print("\n[1/3] 下载视频...")
    filepath = downloader.download_video(
        url,
        config.DOWNLOAD_DIR,
        cookie_file
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
                # 烧录字幕
                # 先找已有的字幕文件
                srt_file = input_file.replace('.mp4', '.srt').replace('.webm', '.srt')
                if not os.path.exists(srt_file):
                    print("❌ 未找到字幕文件，请先生成字幕")
                    return
                
                output_file = input_file.replace('.mp4', '_subtitled.mp4')
                result = auto_subtitle.burn_subtitles(input_file, srt_file, output_file)
                if result:
                    print(f"\n✅ 字幕烧录完成: {result}")
                    
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
