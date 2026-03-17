"""
SRT字幕翻译工具 - 生成中英文字幕
使用 Google Translate + MyMemory 双翻译器，自动切换
"""
import requests
import time
import os

# 尝试导入 deep-translator
try:
    from deep_translator import GoogleTranslator
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    print("⚠️ deep-translator 未安装，将使用 MyMemory")


def translate_with_google(text):
    """使用 Google Translate"""
    if not GOOGLE_AVAILABLE:
        return None
    
    try:
        translator = GoogleTranslator(source='en', target='zh-CN')
        result = translator.translate(text)
        if result and result.strip() and result != text:
            return result
    except Exception as e:
        pass
    
    return None


def translate_with_mymemory(text):
    """使用 MyMemory API"""
    url = "https://api.mymemory.translated.net/get"
    params = {
        'q': text,
        'langpair': 'en|zh-CN'
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        if data.get('responseStatus') == 200:
            result = data.get('responseData', {}).get('translatedText')
            if result and result.strip() and result != text:
                return result
    except:
        pass
    
    return None


def translate_text(text, max_retries=3):
    """
    翻译文本，优先 Google，失败则用 MyMemory
    
    Args:
        text: 要翻译的文本
        max_retries: 最大重试次数
    
    Returns:
        str: 翻译后的文本，失败返回原文
    """
    if not text.strip():
        return text
    
    # 先尝试 Google
    for retry in range(max_retries):
        result = translate_with_google(text)
        if result:
            return result
        
        if retry < max_retries - 1:
            print(f"    ⚠️ Google翻译失败，1秒后重试...")
            time.sleep(1)
    
    # Google 失败，尝试 MyMemory
    print(f"    🔄 切换到 MyMemory...")
    for retry in range(max_retries):
        result = translate_with_mymemory(text)
        if result:
            return result
        
        if retry < max_retries - 1:
            print(f"    ⚠️ MyMemory失败，1秒后重试...")
            time.sleep(1)
    
    print(f"    ❌ 全部翻译失败，使用原文")
    return text


def translate_with_cache(text):
    """带缓存的翻译"""
    if not hasattr(translate_with_cache, 'cache'):
        translate_with_cache.cache = {}
    
    cache_key = text.strip()
    if cache_key in translate_with_cache.cache:
        return translate_with_cache.cache[cache_key]
    
    result = translate_text(text)
    translate_with_cache.cache[cache_key] = result
    return result


def parse_srt(file_path):
    """解析SRT文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    blocks = content.strip().split('\n\n')
    
    subtitles = []
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            subtitles.append({
                'index': lines[0],
                'timestamp': lines[1],
                'text': '\n'.join(lines[2:])
            })
    
    return subtitles


def create_bilingual_srt(subtitles, output_path):
    """创建中英文字幕"""
    output = []
    translated_count = 0
    
    translate_with_cache.cache = {}
    
    total = len(subtitles)
    
    for i, sub in enumerate(subtitles):
        en_text = sub['text']
        
        print(f"翻译 {i+1}/{total}: {en_text[:30]}...")
        
        zh_text = translate_with_cache(en_text)
        
        bilingual_text = f"{en_text}\n{zh_text}"
        output.append(f"{sub['index']}\n{sub['timestamp']}\n{bilingual_text}\n")
        translated_count += 1
        
        if (i + 1) % 10 == 0:
            time.sleep(1)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
    
    return translated_count


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python translate_srt.py <字幕文件路径>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if not os.path.exists(input_file):
        print(f"文件不存在: {input_file}")
        sys.exit(1)
    
    output_file = input_file.replace('.srt', '_bilingual.srt')
    
    print("解析字幕文件...")
    subtitles = parse_srt(input_file)
    print(f"共 {len(subtitles)} 条字幕")
    
    if os.path.exists(output_file):
        confirm = input(f"输出文件已存在，覆盖? (y/n): ").strip().lower()
        if confirm != 'y':
            print("已取消")
            sys.exit(0)
    
    print("\n开始翻译...")
    print("-" * 50)
    
    count = create_bilingual_srt(subtitles, output_file)
    
    print("-" * 50)
    print(f"✅ 完成! 双语字幕已保存: {output_file}")
    print(f"   共处理 {count} 条字幕")
