"""
AI 标题和描述生成器
使用 LLM 生成抖音风格的标题和描述
"""
import os
import json


def call_llm(prompt, model="default"):
    """
    调用 LLM 生成内容
    
    Args:
        prompt: 提示词
        model: 模型名称
    
    Returns:
        str: 生成的文本，失败返回 None
    """
    # 检查是否有配置 LLM API
    # 优先使用 MiniMax (国内更快更稳定)
    
    # 先检查 config.py (用户配置优先)
    try:
        import config
        if hasattr(config, 'MINIMAX_API_KEY') and config.MINIMAX_API_KEY:
            print("[INFO] 使用 MiniMax API")
            return call_minimax(prompt, config.MINIMAX_API_KEY)
        if hasattr(config, 'OPENAI_API_KEY') and config.OPENAI_API_KEY:
            print("[INFO] 使用 OpenAI API")
            return call_openai(prompt, config.OPENAI_API_KEY)
    except:
        pass
    
    # 再检查环境变量
    minimax_key = os.environ.get("MINIMAX_API_KEY")
    if minimax_key:
        print("[INFO] 使用 MiniMax API (环境变量)")
        return call_minimax(prompt, minimax_key)
    
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        print("[INFO] 使用 OpenAI API (环境变量)")
        return call_openai(prompt, openai_key)
    
    print("[INFO] 未配置 LLM API，请在 config.py 中设置")
    return None


def call_openai(prompt, api_key):
    """调用 OpenAI API"""
    import urllib.request
    import urllib.error
    
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
        "max_tokens": 500
    }
    
    return call_api(url, headers, data)


def call_minimax(prompt, api_key):
    """调用 MiniMax API"""
    import urllib.request
    import urllib.error
    
    url = "https://api.minimax.chat/v1/text/chatcompletion_v2"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": "abab6.5s-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
        "max_tokens": 500
    }
    
    return call_api(url, headers, data)


def call_api(url, headers, data):
    """通用 API 调用"""
    import urllib.request
    import urllib.error
    import json
    
    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            elif 'error' in result:
                print(f"[ERROR] API 错误: {result['error']}")
                return None
            
    except urllib.error.URLError as e:
        print(f"[ERROR] 网络错误: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] 调用失败: {e}")
        return None


def generate_title_and_description(video_title=None, video_content=None, 
                                     video_duration=0, language="zh"):
    """
    生成抖音风格的标题和描述
    
    Args:
        video_title: 视频原标题 (可选)
        video_content: 视频内容描述 (可选)
        video_duration: 视频时长(秒)
        language: 语言 (zh/en)
    
    Returns:
        dict: {'title': str, 'description': str, 'tags': list}
    """
    # 构建提示词
    if language == "zh":
        prompt = f"""你是一个抖音内容运营专家。请为以下视频生成爆款标题和描述。

视频信息:
- 原标题: {video_title or '无'}
- 内容描述: {video_content or '无'}
- 时长: {video_duration}秒

要求:
1. 标题要吸引眼球，引发好奇，使用 emoji
2. 描述要自然流畅，能引发互动
3. 生成5个标签
4. 输出格式如下(只输出JSON，不要其他内容):
{{
    "titles": ["标题1", "标题2", "标题3"],
    "description": "描述内容",
    "tags": ["标签1", "标签2", "标签3", "标签4", "标签5"]
}}
"""
    else:
        prompt = f"""You are a TikTok content expert. Generate viral titles and descriptions.

Video Info:
- Title: {video_title or 'N/A'}
- Content: {video_content or 'N/A'}
- Duration: {video_duration}s

Output JSON only:
{{
    "titles": ["title1", "title2", "title3"],
    "description": "description",
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}
"""
    
    print("[AI] 正在生成标题和描述...")
    
    result = call_llm(prompt)
    
    if result:
        try:
            # 解析 JSON
            data = json.loads(result)
            
            return {
                'title': data.get('titles', [''])[0] if data.get('titles') else '',
                'titles': data.get('titles', []),
                'description': data.get('description', ''),
                'tags': data.get('tags', [])
            }
        except json.JSONDecodeError:
            print(f"[ERROR] 解析 AI 返回失败")
            # 尝试提取 JSON
            import re
            match = re.search(r'\{.*\}', result, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group())
                    return {
                        'title': data.get('titles', [''])[0] if data.get('titles') else '',
                        'titles': data.get('titles', []),
                        'description': data.get('description', ''),
                        'tags': data.get('tags', [])
                    }
                except:
                    pass
    
    # 返回默认内容
    return {
        'title': video_title or '精彩视频',
        'titles': [video_title or '精彩视频'],
        'description': '关注我了解更多精彩内容',
        'tags': ['短视频', '精彩', '推荐']
    }


def generate_content_outline(video_duration=60, topic=None, language="zh"):
    """
    生成视频内容大纲 (用于配音/文案)
    
    Args:
        video_duration: 视频时长(秒)
        topic: 主题
        language: 语言
    
    Returns:
        str: 生成的文案内容
    """
    if language == "zh":
        prompt = f"""你是一个视频文案专家。请为{topic or '以下主题'}生成一段{video_duration}秒的短视频文案。

要求:
1. 语言简洁有力，易于口语表达
2. 能引发观众共鸣和互动
3. 适合配音
4. 字数控制在{video_duration * 3}字以内
5. 直接输出文案，不要其他内容
"""
    else:
        prompt = f"""Write a {video_duration}s video script about {topic or 'the topic'}.

Requirements:
1. Concise and powerful
2. Engaging
3. Suitable for voiceover
4. Output only the script
"""
    
    result = call_llm(prompt)
    
    if result:
        return result.strip()
    
    return "精彩内容，尽在视频中！"


if __name__ == "__main__":
    # 测试
    print("=== AI 生成器测试 ===")
    
    result = generate_title_and_description(
        video_title="有趣的科学实验",
        video_duration=30
    )
    
    print(f"\n生成的标题: {result['title']}")
    print(f"生成的描述: {result['description']}")
    print(f"生成的标签: {result['tags']}")
