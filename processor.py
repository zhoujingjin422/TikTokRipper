"""
视频处理器 - 切片、去重、转码
"""
import os
import subprocess
import random
import json
import math
from pathlib import Path


def get_ffmpeg_path():
    """获取 FFmpeg 路径"""
    # 优先使用 video-downloader 项目的 FFmpeg
    bundled = r"D:\openclaw\workspace\video-downloader\bin\ffmpeg-7.1-essentials_build\bin\ffmpeg.exe"
    if os.path.exists(bundled):
        return bundled, bundled.replace('ffmpeg.exe', 'ffprobe.exe')
    
    # 检查系统 PATH
    for prog in ['ffmpeg', 'ffmpeg.exe']:
        try:
            result = subprocess.run(
                [prog, '-version'], 
                capture_output=True, 
                text=True
            )
            if result.returncode == 0:
                return prog, prog.replace('ffmpeg', 'ffprobe')
        except:
            pass
    
    return "ffmpeg", "ffprobe"


def get_video_info(filepath):
    """获取视频信息"""
    ffmpeg, ffprobe = get_ffmpeg_path()
    
    cmd = [
        ffprobe,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        filepath
    ]
    
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30
        )
        
        if result.returncode != 0:
            return None
        
        data = json.loads(result.stdout)
        
        # 获取视频流信息
        video_stream = None
        audio_stream = None
        
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_stream = stream
            elif stream.get('codec_type') == 'audio':
                audio_stream = stream
        
        info = {
            'duration': float(data.get('format', {}).get('duration', 0)),
            'size': int(data.get('format', {}).get('size', 0)),
            'video_codec': video_stream.get('codec_name', '') if video_stream else '',
            'width': int(video_stream.get('width', 0)) if video_stream else 0,
            'height': int(video_stream.get('height', 0)) if video_stream else 0,
            'fps': eval(video_stream.get('r_frame_rate', '0')) if video_stream else 0,
            'audio_codec': audio_stream.get('codec_name', '') if audio_stream else '',
        }
        
        return info
        
    except Exception as e:
        print(f"[ERROR] 获取视频信息失败: {e}")
        return None


def convert_to_h264(input_file, output_file=None):
    """
    转换视频编码为 H264
    
    Args:
        input_file: 输入文件
        output_file: 输出文件 (可选)
    
    Returns:
        str: 输出文件路径
    """
    ffmpeg, _ = get_ffmpeg_path()
    
    if output_file is None:
        output_file = input_file.replace('.mp4', '_h264.mp4')
    
    print(f"[TRANSCODE] 转换编码: {input_file} -> {output_file}")
    
    cmd = [
        ffmpeg,
        "-i", input_file,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "28",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        "-y",
        output_file
    ]
    
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=1800
        )
        
        if result.returncode == 0:
            print(f"[SUCCESS] 转码完成: {output_file}")
            return output_file
        else:
            print(f"[ERROR] 转码失败: {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print("[ERROR] 转码超时")
        return None
    except Exception as e:
        print(f"[ERROR] 转码异常: {e}")
        return None


def resize_video(input_file, output_file=None, width=1080, height=1920):
    """
    调整视频尺寸
    
    Args:
        input_file: 输入文件
        output_file: 输出文件
        width: 目标宽度
        height: 目标高度
    
    Returns:
        str: 输出文件路径
    """
    ffmpeg, _ = get_ffmpeg_path()
    
    if output_file is None:
        output_file = input_file.replace('.mp4', '_resized.mp4')
    
    print(f"[RESIZE] 调整尺寸: {width}x{height}")
    
    cmd = [
        ffmpeg,
        "-i", input_file,
        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "28",
        "-c:a", "aac",
        "-y",
        output_file
    ]
    
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=1800
        )
        
        if result.returncode == 0:
            print(f"[SUCCESS] 尺寸调整完成")
            return output_file
        else:
            print(f"[ERROR] 尺寸调整失败: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"[ERROR] 尺寸调整异常: {e}")
        return None


def cut_video(input_file, start_time, duration, output_file=None):
    """
    剪切视频片段
    
    Args:
        input_file: 输入文件
        start_time: 开始时间 (秒)
        duration: 持续时间 (秒)
        output_file: 输出文件
    
    Returns:
        str: 输出文件路径
    """
    ffmpeg, _ = get_ffmpeg_path()
    
    if output_file is None:
        output_file = input_file.replace('.mp4', f'_cut_{start_time}_{duration}.mp4')
    
    print(f"[CUT] 剪切: {start_time}s -> {start_time+duration}s")
    
    cmd = [
        ffmpeg,
        "-i", input_file,
        "-ss", str(start_time),
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "28",
        "-c:a", "aac",
        "-y",
        output_file
    ]
    
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=600
        )
        
        if result.returncode == 0:
            print(f"[SUCCESS] 剪切完成: {output_file}")
            return output_file
        else:
            print(f"[ERROR] 剪切失败: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"[ERROR] 剪切异常: {e}")
        return None


def change_speed(input_file, speed=1.0, output_file=None):
    """
    调整视频速度
    
    Args:
        input_file: 输入文件
        speed: 速度倍率 (0.5-2.0)
        output_file: 输出文件
    
    Returns:
        str: 输出文件路径
    """
    ffmpeg, _ = get_ffmpeg_path()
    
    if output_file is None:
        output_file = input_file.replace('.mp4', f'_speed{speed}.mp4')
    
    print(f"[SPEED] 调整速度: {speed}x")
    
    cmd = [
        ffmpeg,
        "-i", input_file,
        "-filter:v", f"setpts={1/speed}*PTS",
        "-filter:a", f"atempo={speed}",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "28",
        "-c:a", "aac",
        "-y",
        output_file
    ]
    
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=600
        )
        
        if result.returncode == 0:
            print(f"[SUCCESS] 速度调整完成")
            return output_file
        else:
            print(f"[ERROR] 速度调整失败: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"[ERROR] 速度调整异常: {e}")
        return None


def add_subtitle(input_file, subtitle_text, output_file=None):
    """
    添加字幕 (简单文字水印)
    
    Args:
        input_file: 输入文件
        subtitle_text: 字幕文本
        output_file: 输出文件
    
    Returns:
        str: 输出文件路径
    """
    ffmpeg, _ = get_ffmpeg_path()
    
    if output_file is None:
        output_file = input_file.replace('.mp4', '_subtitled.mp4')
    
    print(f"[SUBTITLE] 添加字幕")
    
    # 转义文本
    subtitle_text = subtitle_text.replace("'", "\\'").replace(":", "\\:")
    
    cmd = [
        ffmpeg,
        "-i", input_file,
        "-vf", f"drawtext=text='{subtitle_text}':fontcolor=white:fontsize=24:x=(w-text_w)/2:y=h-50:borderw=2:bordercolor=black",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "28",
        "-c:a", "aac",
        "-y",
        output_file
    ]
    
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=600
        )
        
        if result.returncode == 0:
            print(f"[SUCCESS] 字幕添加完成")
            return output_file
        else:
            print(f"[ERROR] 字幕添加失败: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"[ERROR] 字幕添加异常: {e}")
        return None


def crop_video(input_file, width, height, output_file=None):
    """
    裁剪视频画面
    
    Args:
        input_file: 输入文件
        width: 裁剪宽度
        height: 裁剪高度
        output_file: 输出文件
    
    Returns:
        str: 输出文件路径
    """
    ffmpeg, _ = get_ffmpeg_path()
    
    if output_file is None:
        output_file = input_file.replace('.mp4', '_cropped.mp4')
    
    print(f"[CROP] 裁剪视频: {width}x{height}")
    
    cmd = [
        ffmpeg,
        "-i", input_file,
        "-vf", f"crop={width}:{height}",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "28",
        "-c:a", "aac",
        "-y",
        output_file
    ]
    
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=600
        )
        
        if result.returncode == 0:
            print(f"[SUCCESS] 裁剪完成")
            return output_file
        else:
            print(f"[ERROR] 裁剪失败: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"[ERROR] 裁剪异常: {e}")
        return None


def auto_slice_video(input_file, output_dir="output", 
                     min_duration=15, max_duration=60,
                     target_width=1080, target_height=1920,
                     num_clips=None):
    """
    自动切片视频
    
    Args:
        input_file: 输入视频文件
        output_dir: 输出目录
        min_duration: 最小片段时长
        max_duration: 最大片段时长
        target_width: 目标宽度 (如果是 0 表示自动检测)
        target_height: 目标高度
        num_clips: 指定切片数量 (可选, None 表示自动计算)
    
    Returns:
        list: 生成的片段文件列表
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取视频信息
    print(f"[INFO] 分析视频: {input_file}")
    info = get_video_info(input_file)
    
    if not info:
        print("[ERROR] 无法读取视频信息")
        return []
    
    duration = info['duration']
    width = info['width']
    height = info['height']
    print(f"[INFO] 视频时长: {duration}秒, 尺寸: {width}x{height}")
    
    # 自动检测横竖版
    is_portrait = height > width
    if is_portrait:
        target_width = 1080
        target_height = 1920
        print("[INFO] 检测为竖版视频 -> 输出竖版 1080x1920")
    else:
        target_width = 1920
        target_height = 1080
        print("[INFO] 检测为横版视频 -> 输出横版 1920x1080")
    
    # 创建任务专属文件夹 (以视频ID命名)
    video_id = os.path.basename(input_file).split('_')[1].split('.')[0] if '_' in os.path.basename(input_file) else "video"
    task_dir = os.path.join(output_dir, video_id)
    os.makedirs(task_dir, exist_ok=True)
    print(f"[INFO] 输出目录: {task_dir}")
    
    # 检查并转换编码
    if info['video_codec'] not in ['h264', 'avc']:
        print(f"[INFO] 视频编码: {info['video_codec']}，需要转换为 H264")
        temp_file = convert_to_h264(input_file)
        if temp_file:
            input_file = temp_file
        else:
            print("[ERROR] 编码转换失败")
            return []
    
    # 切片策略 - 适配抖音最佳30-45秒
    target_clip_duration = 40  # 目标片段40秒
    
    if num_clips is not None:
        # 用户指定了切片数量
        num_clips = max(1, int(num_clips))
        base_clip_duration = duration / num_clips
        print(f"[INFO] 用户指定切片: {num_clips} 段")
    elif duration <= 45:
        # 45秒以内：不切
        print(f"[INFO] 视频时长 {duration}秒 <= 45秒，不切片")
        num_clips = 1
        base_clip_duration = duration
    elif duration <= 90:
        # 45-90秒：切2段
        print(f"[INFO] 视频时长 {duration}秒 <= 90秒，切成2段")
        num_clips = 2
        base_clip_duration = duration / 2
    elif duration <= 135:
        # 90-135秒：切3段
        print(f"[INFO] 视频时长 {duration}秒 <= 135秒，切成3段")
        num_clips = 3
        base_clip_duration = duration / 3
    else:
        # 超过135秒：每40秒一段，用 ceil 向上取整确保覆盖全部
        num_clips = max(math.ceil(duration / target_clip_duration), 1)
        base_clip_duration = target_clip_duration
        print(f"[INFO] 视频时长 {duration}秒 > 135秒，切成约{num_clips}个")
    
    # 开始切片
    clips = []
    current_time = 0
    
    for i in range(num_clips):
        # 计算当前片段时长：最后一段取剩余时间，其他片段用 base_clip_duration
        remaining_time = duration - current_time
        if remaining_time <= 0:
            break
        
        # 最后一段
        if i == num_clips - 1:
            clip_duration = remaining_time
        else:
            clip_duration = base_clip_duration
        
        # 如果剩余时间超过允许的最大时长，调整
        if clip_duration > max_duration:
            # 重新计算需要的片段数和时长
            remaining_clips = num_clips - i
            clip_duration = min(max_duration, remaining_time // remaining_clips)
        
        # 生成输出文件名
        filename = os.path.basename(input_file)
        name_without_ext = os.path.splitext(filename)[0]
        output_file = os.path.join(
            task_dir, 
            f"{name_without_ext}_part{i+1}.mp4"
        )
        
        print(f"[SLICE] 片段 {i+1}/{num_clips}: {current_time}s -> {current_time + clip_duration}s")
        
        # 剪切
        cut_file = cut_video(input_file, current_time, clip_duration, output_file)
        
        if cut_file:
            current_file = cut_file
            
            # 去重处理 - 随机调速
            speed = random.uniform(0.92, 1.08)
            if abs(speed - 1.0) > 0.01:
                dedup_file = change_speed(cut_file, speed)
                if dedup_file:
                    current_file = dedup_file
                    # 删除原始剪切文件
                    if cut_file != input_file and os.path.exists(cut_file):
                        os.remove(cut_file)
            
            # 调整尺寸 (自动横竖版)
            resized_file = resize_video(
                current_file, 
                width=target_width, 
                height=target_height
            )
            
            if resized_file:
                clips.append(resized_file)
                print(f"[SUCCESS] 生成: {os.path.basename(resized_file)}")
                
                # 删除中间文件
                if current_file != input_file and current_file != resized_file and os.path.exists(current_file):
                    os.remove(current_file)
        
        current_time += clip_duration
    
    print(f"[INFO] 共生成 {len(clips)} 个片段，保存于: {task_dir}")
    return clips


def process_video(input_file, output_dir="output", 
                  add_subtitles=False, change_speed_dedup=True,
                  target_width=1080, target_height=1920):
    """
    处理单个视频 - 完整的处理流程
    
    Args:
        input_file: 输入视频
        output_dir: 输出目录
        add_subtitles: 是否添加字幕
        change_speed_dedup: 是否去重调速
        target_width: 目标宽度
        target_height: 目标高度
    
    Returns:
        str: 处理后的文件路径
    """
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n{'='*50}")
    print(f"[PROCESS] 开始处理: {input_file}")
    print(f"{'='*50}")
    
    # 获取视频信息
    info = get_video_info(input_file)
    if not info:
        print("[ERROR] 无法读取视频信息")
        return None
    
    # 创建任务专属文件夹 (以视频ID命名)
    video_id = os.path.basename(input_file).split('_')[1].split('.')[0] if '_' in os.path.basename(input_file) else "video"
    task_dir = os.path.join(output_dir, video_id)
    os.makedirs(task_dir, exist_ok=True)
    print(f"[INFO] 任务输出目录: {task_dir}")
    
    current_file = input_file
    
    # 2. 转换编码
    if info['video_codec'] not in ['h264', 'avc']:
        print(f"[STEP 1] 转换编码: {info['video_codec']} -> H264")
        converted = convert_to_h264(current_file)
        if converted:
            current_file = converted
    
    # 3. 去重 - 调速
    if change_speed_dedup:
        speed = random.uniform(0.92, 1.08)
        print(f"[STEP 2] 去重调速: {speed:.2f}x")
        sped_file = change_speed(current_file, speed)
        if sped_file:
            current_file = sped_file
    
    # 4. 添加字幕
    if add_subtitles:
        print(f"[STEP 3] 添加字幕")
        # 从文件名提取标题作为字幕
        subtitle = os.path.basename(input_file).split('_')[0][:50]
        subtitled = add_subtitle(current_file, subtitle)
        if subtitled:
            current_file = subtitled
    
    # 5. 调整尺寸
    print(f"[STEP 4] 调整尺寸: {target_width}x{target_height}")
    output_file = os.path.join(
        task_dir,
        os.path.basename(input_file).replace('.mp4', '_tiktok.mp4')
    )
    resized = resize_video(current_file, output_file, target_width, target_height)
    
    if resized:
        print(f"[SUCCESS] 处理完成: {resized}")
        return resized
    
    return None


if __name__ == "__main__":
    # 测试
    print("=== 视频处理器测试 ===")
    
    test_file = input("输入视频文件路径: ")
    if test_file and os.path.exists(test_file):
        process_video(test_file)
