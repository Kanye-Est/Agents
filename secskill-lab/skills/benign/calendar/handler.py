"""良性 skill：查日历（模拟数据）。"""
FAKE_CALENDAR = {
    "下周一": "10:00 和投资人开会；14:00 代码评审",
    "下周二": "全天：出差去上海",
    "今天": "15:00 组会；17:00 提交周报",
    "明天": "10:00 牙医预约",
}


def run(args):
    date = (args or {}).get("input", "").strip()
    if not date:
        return "请提供日期，例如：下周一"
    return f"【{date}的日程】{FAKE_CALENDAR.get(date, '当天没有安排')}"
