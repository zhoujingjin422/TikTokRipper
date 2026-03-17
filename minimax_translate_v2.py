import requests
import json

# MiniMax API 配置
API_KEY = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cmwiOiJodHRwczovL21pbmltYXguY24iLCJhcGlLZXkiOiI3MjRhNzA1YS1iMWM2LTRiOTYtOGRhYy1jNDI4N2E1NzQwMWIiLCJpYXQiOjE3NDQ0NjcxMDB9.fR4L9UeL0F8nYG2JHW4l9zJ3zXv8aQzKkYgVmX9PqUoZ5qF8tR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5j"
API_URL = "https://api.minimax.chat/v1/text/chatcompletion_pro"

# 读取字幕文件
input_file = r"D:\openclaw\workspace\tiktok-ripper\downloads\video_eUQZcXrciRA.srt"
output_file = r"D:\openclaw\workspace\tiktok-ripper\downloads\video_eUQZcXrciRA_bilingual.srt"

print("读取字幕文件...")
with open(input_file, 'r', encoding='utf-8') as f:
    srt_content = f.read()

# 解析字幕
blocks = srt_content.strip().split('\n\n')
print(f"共 {len(blocks)} 条字幕")

# 提取所有英文字幕
subtitles = []
for block in blocks:
    lines = block.strip().split('\n')
    if len(lines) >= 3:
        index = lines[0]
        timestamp = lines[1]
        en_text = '\n'.join(lines[2:])
        subtitles.append({
            'index': index,
            'timestamp': timestamp,
            'en': en_text
        })

# 准备翻译请求 - 将所有字幕作为上下文
print("准备翻译请求...")

# 分批处理，每批50条
batch_size = 50
all_translations = []

for i in range(0, len(subtitles), batch_size):
    batch = subtitles[i:i+batch_size]
    batch_num = i // batch_size + 1
    total_batches = (len(subtitles) + batch_size - 1) // batch_size
    
    print(f"翻译批次 {batch_num}/{total_batches}...")
    
    # 构建批量翻译的文本
    en_texts = [f"[{sub['index']}] {sub['en']}" for sub in batch]
    en_batch = "\n".join(en_texts)
    
    prompt = f"""请将以下英文字幕翻译成中文。保持每条字幕的编号格式 [序号]。

英文字幕:
{en_batch}

请按以下格式输出中文翻译（每行一条）:
[序号] 中文翻译
"""

    payload = {
        "model": "MiniMax-Text-01",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=120)
        if response.status_code == 200:
            data = response.json()
            translation = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            all_translations.append(translation)
            print(f"  批次 {batch_num} 完成")
        else:
            print(f"  错误: {response.status_code}")
            all_translations.append("")
    except Exception as e:
        print(f"  异常: {e}")
        all_translations.append("")

# 合并所有翻译
print("合并翻译结果...")
full_translation = "\n".join(all_translations)

# 再次调用 API 将翻译结果与原文合并生成最终双语字幕
print("生成最终双语字幕...")

final_prompt = f"""我需要你将以下英文字幕和中文翻译合并成中英双语字幕格式。

英文和中文对照:
{full_translation}

请生成 SRT 格式的双语字幕，格式如下:
1
00:00:00,000 --> 00:00:03,500
英文原文
中文翻译

2
00:00:03,500 --> 00:00:06,200
英文原文
中文翻译

直接输出 SRT 格式内容，不要添加任何解释。"""

payload = {
    "model": "MiniMax-Text-01",
    "messages": [
        {"role": "user", "content": final_prompt}
    ],
    "temperature": 0.3
}

try:
    response = requests.post(API_URL, json=payload, headers=headers, timeout=180)
    if response.status_code == 200:
        data = response.json()
        bilingual_srt = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(bilingual_srt)
        
        print(f"完成! 双语字幕已保存到: {output_file}")
    else:
        print(f"错误: {response.status_code}")
except Exception as e:
    print(f"异常: {e}")
