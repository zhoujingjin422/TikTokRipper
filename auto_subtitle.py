"""
自动字幕生成器 - 使用 Whisper 语音识别 (系统 Python 版本)
"""
import os
import subprocess
import json
import sys


# Python 路径 - 使用完整路径确保一致
PYTHON_PATH = r"C:\Users\hjj\AppData\Local\Programs\Python\Python311\python.exe"


def generate_subtitles(video_path, output_path=None, language=None):
    """
    使用 Whisper 生成字幕文件
    
    Args:
        video_path: 视频文件路径
        output_path: 输出字幕文件路径 (可选)
        language: 语言代码 (可选, 如 'zh', 'en')
    
    Returns:
        str: 生成的字幕文件路径，失败返回 None
    """
    if not os.path.exists(video_path):
        print(f"[ERROR] 视频文件不存在: {video_path}")
        return None
    
    # 获取视频目录和文件名
    video_dir = os.path.dirname(video_path)
    video_name = os.path.basename(video_path)
    video_name_base = os.path.splitext(video_name)[0]
    
    # 默认输出路径
    if output_path is None:
        output_path = os.path.join(video_dir, f"{video_name_base}.srt")
    
    print(f"[WHISPER] 正在生成字幕: {video_name}")
    
    # 使用系统 Python 和 faster-whisper
    python_code = f'''
import sys
from faster_whisper import WhisperModel

# 选择模型大小 (tiny, base, small, medium, large-v3)
model_size = "base"

print(f"加载模型: {{model_size}}...")
model = WhisperModel(model_size, device="cpu", compute_type="int8")

print("开始转录...")
segments, info = model.transcribe("{video_path}", language="{language if language else 'auto'}")

print(f"检测到语言: {{info.language}} (概率: {{info.language_probability:.2f}})")

# 生成 SRT 格式
output_srt = ""
segment_count = 1

for segment in segments:
    start_time = segment.start
    end_time = segment.end
    text = segment.text.strip()
    
    # 转换时间为 SRT 格式
    start_srt = format_time(start_time)
    end_srt = format_time(end_time)
    
    output_srt += f"{{segment_count}}\\n"
    output_srt += f"{{start_srt}} --> {{end_srt}}\\n"
    output_srt += f"{{text}}\\n\\n"
    
    segment_count += 1

# 写入文件
with open("{output_path}", "w", encoding="utf-8") as f:
    f.write(output_srt)

print("字幕生成完成!")

def format_time(seconds):
    """将秒数转换为 SRT 时间格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{{hours:02d}}:{{minutes:02d}}:{{secs:02d}},{{millis:03d}}"
'''
    
    try:
        # 在视频目录运行
        result = subprocess.run(
            [PYTHON_PATH, "-c", python_code],
            capture_output=True,
            text=True,
            timeout=600,
            cwd=video_dir
        )
        
        print(result.stdout)
        
        if os.path.exists(output_path):
            print(f"[SUCCESS] 字幕生成完成: {output_path}")
            return output_path
        else:
            print(f"[ERROR] 字幕生成失败: {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print("[ERROR] 字幕生成超时")
        return None
    except Exception as e:
        print(f"[ERROR] 字幕生成异常: {e}")
        return None


def burn_subtitles(video_path, srt_path, output_path=None):
    """
    烧录字幕到视频
    
    Args:
        video_path: 视频文件路径
        srt_path: 字幕文件路径
        output_path: 输出视频路径
    
    Returns:
        str: 输出视频路径，失败返回 None
    """
    # 使用我们刚安装的 ffmpeg
    ffmpeg_path = r"C:\ffmpeg\ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg.exe"
    
    if not os.path.exists(ffmpeg_path):
        print(f"[ERROR] FFmpeg 不存在: {ffmpeg_path}")
        return None
    
    if not os.path.exists(video_path):
        print(f"[ERROR] 视频文件不存在: {video_path}")
        return None
    
    if not os.path.exists(srt_path):
        print(f"[ERROR] 字幕文件不存在: {srt_path}")
        return None
    
    if output_path is None:
        output_path = video_path.replace('.mp4', '_subtitled.mp4')
    
    print(f"[BURN] 烧录字幕到视频")
    
    # 切换到视频所在目录执行，避免路径问题
    video_dir = os.path.dirname(video_path)
    video_name = os.path.basename(video_path)
    srt_name = os.path.basename(srt_path)
    output_name = os.path.basename(output_path)
    
    cmd = [
        ffmpeg_path,
        "-i", video_name,
        "-vf", f"subtitles={srt_name}",
        "-c:a", "copy",
        output_name
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
            cwd=video_dir
        )
        
        if result.returncode == 0:
            print(f"[SUCCESS] 字幕烧录完成: {output_path}")
            return output_path
        else:
            print(f"[ERROR] 字幕烧录失败: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"[ERROR] 字幕烧录异常: {e}")
        return None


def merge_subtitles(srt_path1, srt_path2, output_path=None):
    """合并两个 SRT 字幕文件 (中英双字幕)"""
    if not os.path.exists(srt_path1):
        print(f"[ERROR] 字幕文件不存在: {srt_path1}")
        return None
    
    if not os.path.exists(srt_path2):
        print(f"[ERROR] 字幕文件不存在: {srt_path2}")
        return None
    
    if output_path is None:
        output_path = srt_path1.replace('.srt', '_bilingual.srt')
    
    print(f"[MERGE] 合并中英字幕...")
    
    # 读取两个字幕文件
    with open(srt_path1, 'r', encoding='utf-8') as f:
        content1 = f.read()
    
    with open(srt_path2, 'r', encoding='utf-8') as f:
        content2 = f.read()
    
    # 解析 SRT
    subtitles1 = parse_srt(content1)
    subtitles2 = parse_srt(content2)
    
    # 按时间轴合并
    merged = []
    for sub1 in subtitles1:
        start_time = sub1['start']
        end_time = sub1['end']
        
        # 找对应的中文字幕
        text2 = ""
        for sub2 in subtitles2:
            if sub2['start'] <= start_time and sub2['end'] >= end_time:
                text2 = sub2['text']
                break
            elif abs(float(sub2['start'].replace(':','').replace(',','.')) - float(start_time.replace(':','').replace(',','.'))) < 1:
                text2 = sub2['text']
                break
        
        # 合并文本
        merged_text = f"{sub1['text']}\n{text2}" if text2 else sub1['text']
        
        merged.append({
            'start': start_time,
            'end': end_time,
            'text': merged_text
        })
    
    # 生成新的 SRT
    output_content = generate_srt(merged)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_content)
    
    print(f"[SUCCESS] 双语字幕已生成: {output_path}")
    return output_path


def parse_srt(content):
    """解析 SRT 内容"""
    subtitles = []
    blocks = content.strip().split('\n\n')
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            time_line = lines[1]
            times = time_line.split(' --> ')
            if len(times) == 2:
                subtitles.append({
                    'start': times[0].strip().replace(',', '.'),
                    'end': times[1].strip().replace(',', '.'),
                    'text': '\n'.join(lines[2:])
                })
    
    return subtitles


def generate_srt(subtitles):
    """生成 SRT 内容"""
    output = []
    for i, sub in enumerate(subtitles, 1):
        output.append(str(i))
        output.append(f"{sub['start']} --> {sub['end']}")
        output.append(sub['text'])
        output.append('')
    
    return '\n'.join(output)


if __name__ == "__main__":
    print("=== Whisper 字幕生成器测试 ===")
    test_video = input("输入视频文件路径: ")
    if test_video and os.path.exists(test_video):
        srt_file = generate_subtitles(test_video)
        if srt_file:
            print(f"字幕文件: {srt_file}")
