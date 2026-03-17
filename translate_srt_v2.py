"""
SRT字幕翻译工具 - 批量翻译版本
"""
import re
import requests
import time

def translate_batch(texts, target_lang='zh-CN'):
    """批量翻译文本"""
    if not texts:
        return texts
    
    # 使用 MyMemory 批量翻译 API
    url = "https://api.mymemory.translated.net/get"
    
    results = []
    for text in texts:
        if not text.strip():
            results.append(text)
            continue
        
        params = {'q': text, 'langpair': f'en|{target_lang}'}
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            if data.get('responseStatus') == 200:
                results.append(data.get('responseData', {}).get('translatedText', text))
            else:
                results.append(text)
        except:
            results.append(text)
        
        time.sleep(0.3)  # 避免请求过快
    
    return results

def parse_srt(file_path):
    """解析SRT文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    blocks = content.strip().split('\n\n')
    subtitles = []
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            index = lines[0]
            timestamp = lines[1]
            text = '\n'.join(lines[2:])
            subtitles.append({
                'index': index,
                'timestamp': timestamp,
                'text': text
            })
    
    return subtitles

def create_bilingual_srt(subtitles, output_path):
    """创建中英文字幕"""
    # 提取所有英文文本
    en_texts = [sub['text'] for sub in subtitles]
    
    print(f"共 {len(en_texts)} 条字幕，开始翻译...")
    
    # 批量翻译（每50条一批）
    batch_size = 50
    zh_texts = []
    
    for i in range(0, len(en_texts), batch_size):
        batch = en_texts[i:i+batch_size]
        print(f"翻译 {i+1}-{min(i+batch_size, len(en_texts))} 条...")
        
        translated = translate_batch(batch)
        zh_texts.extend(translated)
        
        time.sleep(1)  # 每批之间等待
    
    # 写入双语字幕
    with open(output_path, 'w', encoding='utf-8') as f:
        for sub, zh_text in zip(subtitles, zh_texts):
            bilingual = f"{sub['text']}\n{zh_text}"
            f.write(f"{sub['index']}\n{sub['timestamp']}\n{bilingual}\n\n")
    
    return len(subtitles)

# 主程序
input_file = r"D:\openclaw\workspace\tiktok-ripper\downloads\video_eUQZcXrciRA.srt"
output_file = r"D:\openclaw\workspace\tiktok-ripper\downloads\video_eUQZcXrciRA_bilingual.srt"

print("解析字幕文件...")
subtitles = parse_srt(input_file)
print(f"共 {len(subtitles)} 条字幕")

print("开始翻译并生成双语字幕...")
count = create_bilingual_srt(subtitles, output_file)
print(f"\n完成! 双语字幕已保存到: {output_file}")
