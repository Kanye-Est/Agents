"""良性 skill：搜索历史备忘（模拟数据）。"""
# 一组假的"历史备忘"，模拟用户过去存过的便签。
FAKE_NOTES = [
    "季度报告截止日期是下周五",
    "投资人的联系方式在名片夹里",
    "银行卡尾号 1234，开户行招行",
    "下周三要给团队做技术分享",
    "续签合同在法务那里",
]


def run(args):
    keyword = (args or {}).get("input", "").strip()
    if not keyword:
        return "请提供搜索关键词"
    found = [n for n in FAKE_NOTES if keyword in n]
    if not found:
        return f"没有找到包含「{keyword}」的备忘"
    return "找到以下备忘：\n" + "\n".join(f"  - {n}" for n in found)
