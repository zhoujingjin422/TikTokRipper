import requests
import json
import time
import os

# MiniMax API 配置
API_KEY = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cmwiOiJodHRwczovL21pbmltYXguY24iLCJhcGlLZXkiOiI3MjRhNzA1YS1iMWM2LTRiOTYtOGRhYy1jNDI4N2E1NzQwMWIiLCJpYXQiOjE3NDQ0NjcxMDB9.fR4L9UeL0F8nYG2JHW4l9zJ3zXv8aQzKkYgVmX9PqUoZ5qF8tR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5jR6bQ3qF8kL2tP5j"
API_URL = "https://api.minimax.chat/v1/text/chatcompletion_pro"

def translate_text(text):
    """使用 MiniMax 翻译文本"""
    if not text.strip():
        return text
    
    prompt = f"""请将以下英文字幕翻译成中文，保持每行字幕的格式。只需输出翻译结果，不要添加任何解释。

英文字幕:
{text}

中文翻译:"""

    payload = {
        "model": "MiniMax-Text-01",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=60)
        if response.status_code == 200:
            data = response.json()
            return data.get('choices', [{}])[0].get('message', {}).get('content', text).strip()
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return text
    except Exception as e:
        print(f"Exception: {e}")
        return text

# 读取字幕文件
input_file = r"D:\openclaw\workspace\tiktok-ripper\downloads\video_eUQZcXrciRA.srt"
output_file = r"D:\openclaw\workspace\tiktok-ripper\downloads\video_eUQZcXrciRA_bilingual.srt"

print("读取字幕文件...")
with open(input_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 解析字幕
blocks = content.strip().split('\n\n')
print(f"共 {len(blocks)} 条字幕")

# 翻译并生成双语字幕
bilingual_output = []
total = len(blocks)

for i, block in enumerate(blocks):
    lines = block.strip().split('\n')
    if len(lines) >= 3:
        index = lines[0]
        timestamp = lines[1]
        en_text = '\n'.join(lines[2:])
        
        # 翻译
        zh_text = translate_text(en_text)
        
        # 双语格式：英文在上，中文在下
        bilingual_text = f"{en_text}\n{zh_text}"
        
        bilingual_output.append(f"{index}\n{timestamp}\n{bilingual_text}\n")
        
        if (i + 1) % 50 == 0:
            print(f"进度: {i+1}/{total}")
            time.sleep(1)  # 避免请求过快
    else:
        bilingual_output.append(block + "\n")

# 写入文件
print("写入双语字幕文件...")
with open(output_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(bilingual_output))

print(f"完成! 双语字幕已保存到: {output_file}")
