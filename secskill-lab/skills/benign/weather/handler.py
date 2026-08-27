"""良性 skill：查天气（模拟，返回固定的假数据）。"""
# 用一个写死的"天气数据库"模拟真实天气 API，避免联网依赖。
FAKE_WEATHER = {
    "北京": "晴 28°C",
    "上海": "多云 25°C",
    "深圳": "雷阵雨 30°C",
    "杭州": "阴 23°C",
}


def run(args):
    city = (args or {}).get("input", "").strip()
    if not city:
        return "请提供城市名，例如：北京"
    return f"{city}当前天气：{FAKE_WEATHER.get(city, '晴 26°C')}（模拟数据）"
