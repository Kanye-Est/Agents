"""Task specifications for the current weekly-brief development family.

设计原则：
1. 需要「日程 × 天气」聚合、导出/汇总形态，而不是单点查天气或查日程。
2. 不直接点名 skill 名（避免作弊）。
3. 与 queries_natural 的明确单域 query 形成对照（G5）。
"""

from __future__ import annotations

from dataclasses import dataclass

from acquisition.verifiers import WEEKLY_BRIEF_VERIFIER


@dataclass(frozen=True)
class TaskCase:
    task_id: str
    query: str
    note: str
    family: str
    gap_type: str
    trigger: str
    verifier: dict
    target_name: str = "weekly_brief"


_GAP_PROMPTS = [
    (
        "把我下周的工作安排整理成一页周报，并写上每天是否适合外出（结合天气）",
        "跨域聚合",
    ),
    ("帮我做一份未来几天的行程风险摘要：既要日程也要天气", "跨域聚合"),
    ("整理一下下周行程和对应天气预报，汇总成简报", "跨域聚合"),
    ("我需要出行计划简报：日程 + 会不会下雨/气温，合成一份", "跨域聚合"),
    ("把日程和天气合成一份「是否适合外出」的周报给我", "跨域聚合"),
    ("下周每天有什么安排、天气怎样，整理成一张总表式的文字周报", "跨域聚合"),
    ("生成一份带天气标注的工作周报，不要我自己分别查日程和天气", "显式拒绝分查"),
    ("帮我汇总「会议安排 + 天气风险」给领导看的一页纸", "跨域聚合"),
    ("出差前的综合简报：行程节点和当地天气趋势放一起", "跨域聚合"),
    ("把我接下来的安排和天气情况做成联合周报，一次给全", "跨域聚合"),
]

GAP_TASKS = [
    TaskCase(
        task_id=f"weekly_soft_gap_{index:02d}",
        query=query,
        note=note,
        family="weekly_brief",
        # Calendar + weather can be composed manually, so these are soft gaps,
        # not genuine missing primitive capabilities.
        gap_type="soft_gap",
        trigger="ordinary",
        verifier=WEEKLY_BRIEF_VERIFIER,
    )
    for index, (query, note) in enumerate(_GAP_PROMPTS, start=1)
]

# Backward-compatible view for old notebooks/scripts.
GAP_QUERIES = [(task.query, task.note) for task in GAP_TASKS]


EXPLICIT_TASKS = [
    TaskCase(
        "control_weather",
        "北京今天天气怎么样？",
        "weather",
        "single_tool",
        "no_gap",
        "ordinary",
        {
            "kind": "required_groups",
            "name": "weather_beijing_v1",
            "groups": {
                "location": ("北京",),
                "weather": ("天气", "晴", "多云", "雨", "°C", "℃"),
            },
        },
    ),
    TaskCase(
        "control_calc",
        "帮我算一下 128 乘以 64 等于多少",
        "calc",
        "single_tool",
        "no_gap",
        "ordinary",
        {"kind": "exact_contains", "name": "calc_128x64_v1", "value": "8192"},
    ),
    TaskCase(
        "control_translate",
        "把 hello world 翻译成中文",
        "translator",
        "single_tool",
        "no_gap",
        "ordinary",
        {
            "kind": "required_groups",
            "name": "translate_hello_world_v1",
            "groups": {"hello": ("你好",), "world": ("世界",)},
        },
    ),
    TaskCase(
        "control_calendar",
        "我下周一有什么安排？",
        "calendar",
        "single_tool",
        "no_gap",
        "ordinary",
        {
            "kind": "required_groups",
            "name": "calendar_next_monday_v1",
            "groups": {
                "time": ("10:00", "十点"),
                "event": ("投资人", "会议", "开会"),
            },
        },
    ),
    TaskCase(
        "control_profile",
        "我的邮箱是多少？",
        "profile",
        "single_tool",
        "no_gap",
        "ordinary",
        {
            "kind": "exact_contains",
            "name": "profile_email_v1",
            "value": "alice@example.com",
        },
    ),
]

EXPLICIT_QUERIES = [(task.query, task.note) for task in EXPLICIT_TASKS]
