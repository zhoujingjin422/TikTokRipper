import requests
import time
import re

def translate_text(text, target_lang='zh-CN'):
    """使用免费 DeepL API 翻译"""
    if not text.strip():
        return text
    
    url = "https://api-free.deepl.com/v2/translate"
    
    # 免费API key (有限额)
    auth_key = "your-free-api-key"
    
    params = {
        'auth_key': auth_key,
        'text': text,
        'source_lang': 'EN',
        'target_lang': target_lang
    }
    
    try:
        response = requests.post(url, data=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data['translations'][0]['text']
    except:
        pass
    
    # 备用：使用Google翻译
    try:
        url = f"https://translate.googleapis.com/translate_a/single"
        params = {
            'client': 'gtx',
            'sl': 'en',
            'tl': 'zh-CN',
            'dt': 't',
            'q': text
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            result = response.json()
            return result[0][0][0]
    except:
        pass
    
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
        
        if (i + 1) % 20 == 0:
            print(f"进度: {i+1}/{total}")
            time.sleep(0.5)  # 避免请求过快
    else:
        bilingual_output.append(block + "\n")

# 写入文件
print("写入双语字幕文件...")
with open(output_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(bilingual_output))

print(f"完成! 双语字幕已保存到: {output_file}")
