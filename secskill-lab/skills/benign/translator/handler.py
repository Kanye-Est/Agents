"""良性 skill：翻译（用关键词模拟，不调翻译 API 避免依赖）。"""
# 模拟翻译：用一个小词典做最简单的查表，够 agent "看出这是个翻译工具"即可。
# 真实环境里这里会调 Google/DeepL API，但实验不需要真实翻译质量。
MINI_DICT = {
    "hello": "你好", "world": "世界", "meeting": "会议",
    "你好": "hello", "会议": "meeting", "报告": "report",
}


def run(args):
    text = (args or {}).get("input", "").strip()
    if not text:
        return "请提供要翻译的文字"
    # 逐词查表，查不到的原样返回（模拟翻译质量不完美）
    words = text.split()
    translated = [MINI_DICT.get(w.lower(), w) for w in words]
    return " ".join(translated) + "（模拟翻译）"
