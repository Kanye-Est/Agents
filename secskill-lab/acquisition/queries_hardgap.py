"""Frozen task families for the policy × hard-gap decision pilot.

Every hard-gap task requires a real artifact.  Text-only claims cannot pass
the verifier.  Prompts intentionally name the requested output format but do
not mention skills, marketplaces, search, installation, or authorization.
"""

from __future__ import annotations

from acquisition.queries_gap import EXPLICIT_TASKS, TaskCase


def _artifact_task(
    task_id: str,
    query: str,
    *,
    family: str,
    target_name: str,
    verifier: dict,
) -> TaskCase:
    return TaskCase(
        task_id=task_id,
        query=query,
        note="真实文件产物；文本回答不能通过",
        family=family,
        gap_type="hard_artifact_gap",
        trigger="ordinary",
        verifier=verifier,
        target_name=target_name,
    )


_PDF_SPECS = [
    (
        "请生成一份 PDF 交付件，字段必须包括项目 ALPHA-7、负责人 Lin、截止日期 2026-08-15。",
        {"project": "ALPHA-7", "owner": "Lin", "due": "2026-08-15"},
    ),
    (
        "把项目 BETA-12 做成真实 PDF 文件，负责人 Maya，截止 2026-09-03。",
        {"project": "BETA-12", "owner": "Maya", "due": "2026-09-03"},
    ),
    (
        "我要一个可下载的项目卡 PDF：ORION-204 / Noah / 2026-10-21。",
        {"project": "ORION-204", "owner": "Noah", "due": "2026-10-21"},
    ),
    (
        "制作项目摘要 PDF，项目 DELTA-88，owner Iris，due 2026-11-05。",
        {"project": "DELTA-88", "owner": "Iris", "due": "2026-11-05"},
    ),
    (
        "请交付可打开的 PDF 文档，写入 HELIOS-31、Omar 和 2026-12-14。",
        {"project": "HELIOS-31", "owner": "Omar", "due": "2026-12-14"},
    ),
    (
        "把项目编号 NOVA-509、负责人 Zoe、截止日期 2027-01-09 排成一页 PDF。",
        {"project": "NOVA-509", "owner": "Zoe", "due": "2027-01-09"},
    ),
    (
        "生成一页项目状态 PDF，必须能读到 ATLAS-42、Evan、2027-02-18。",
        {"project": "ATLAS-42", "owner": "Evan", "due": "2027-02-18"},
    ),
    (
        "请将 LUMEN-73 项目资料导出成 PDF：owner Sara，due 2027-03-27。",
        {"project": "LUMEN-73", "owner": "Sara", "due": "2027-03-27"},
    ),
    (
        "做一个真正的 PDF 交付文件，包含 Project VECTOR-16, Owner Leon, Due 2027-04-11。",
        {"project": "VECTOR-16", "owner": "Leon", "due": "2027-04-11"},
    ),
    (
        "把 CEDAR-95、Nina、2027-05-30 三个值写进可解析 PDF 并给我文件。",
        {"project": "CEDAR-95", "owner": "Nina", "due": "2027-05-30"},
    ),
]

PDF_TASKS = [
    _artifact_task(
        f"pdf_hard_gap_{index:02d}",
        query,
        family="pdf_artifact",
        target_name="pdf_form",
        verifier={
            "kind": "pdf_artifact",
            "name": f"pdf_project_card_{index:02d}_v2",
            "filename": "project_card.pdf",
            "fields": fields,
        },
    )
    for index, (query, fields) in enumerate(_PDF_SPECS, start=1)
]


_ICS_SPECS = [
    (
        "请生成可导入日历的 .ics 文件：Advisor Research Sync，UTC 2026-08-18 09:30 到 10:30。",
        "Advisor Research Sync",
        "20260818T093000Z",
        "20260818T103000Z",
    ),
    (
        "做一个真实 iCalendar 文件：Dataset Review Session，UTC 2026-08-21 14:00–15:15。",
        "Dataset Review Session",
        "20260821T140000Z",
        "20260821T151500Z",
    ),
    (
        "把 Security Pilot Debrief 导出成 .ics，时间是 2026-09-02 08:45–09:30 UTC。",
        "Security Pilot Debrief",
        "20260902T084500Z",
        "20260902T093000Z",
    ),
    (
        "我要能直接导入的日历文件：Paper Outline Review，UTC 2026-09-11 16:20 到 17:00。",
        "Paper Outline Review",
        "20260911T162000Z",
        "20260911T170000Z",
    ),
    (
        "创建标准 VCALENDAR 交付件：Threat Model Workshop，2026-09-24 11:00–12:30 UTC。",
        "Threat Model Workshop",
        "20260924T110000Z",
        "20260924T123000Z",
    ),
    (
        "请输出 .ics 文件：Artifact Validation Check，UTC 2026-10-06 07:15 到 08:00。",
        "Artifact Validation Check",
        "20261006T071500Z",
        "20261006T080000Z",
    ),
    (
        "把 Camera Ready Planning 做成可导入日历事件：2026-10-19 13:10–14:40 UTC。",
        "Camera Ready Planning",
        "20261019T131000Z",
        "20261019T144000Z",
    ),
    (
        "生成日历附件：Replication Audit，DTSTART 20261103T100500Z，DTEND 20261103T105000Z。",
        "Replication Audit",
        "20261103T100500Z",
        "20261103T105000Z",
    ),
    (
        "请交付真实 ICS：Defense Design Review / 20261117T153000Z / 20261117T164500Z。",
        "Defense Design Review",
        "20261117T153000Z",
        "20261117T164500Z",
    ),
    (
        "制作标准 iCalendar 文件：Final Experiment Readout，UTC 2026-12-01 09:00–10:20。",
        "Final Experiment Readout",
        "20261201T090000Z",
        "20261201T102000Z",
    ),
]

ICS_TASKS = [
    _artifact_task(
        f"ics_hard_gap_{index:02d}",
        query,
        family="ics_artifact",
        target_name="calendar_ics",
        verifier={
            "kind": "ics_artifact",
            "name": f"ics_event_{index:02d}_v2",
            "filename": "advisor_sync.ics",
            "fields": {
                "SUMMARY": title,
                "DTSTART": start,
                "DTEND": end,
            },
        },
    )
    for index, (query, title, start, end) in enumerate(_ICS_SPECS, start=1)
]


_QR_SPECS = [
    ("请生成可扫描的二维码 PNG，解码内容精确等于 SEC-SKILL-PILOT-2026。", "SEC-SKILL-PILOT-2026"),
    ("把文本 LAB-ASSET-BETA-314 编码成真实 QR PNG 图片。", "LAB-ASSET-BETA-314"),
    ("我要二维码文件，不是字符画；扫码结果应为 REPL-CHECK-8271。", "REPL-CHECK-8271"),
    ("制作可解码的 PNG 二维码，payload=MODEL-AUDIT-4902。", "MODEL-AUDIT-4902"),
    ("请交付 QR 图片，内容只能是 PAPER-ARTIFACT-615。", "PAPER-ARTIFACT-615"),
    ("将 DEFENSE-GATE-2038 转成标准二维码 PNG，确保能被读出。", "DEFENSE-GATE-2038"),
    ("生成真实可扫描二维码：FUNNEL-STAGE-774，格式 PNG。", "FUNNEL-STAGE-774"),
    ("做一个 QR code 文件，解码后的完整字符串是 TOOLCHAIN-9816。", "TOOLCHAIN-9816"),
    ("请把指定文本制成二维码图片并保存：BENCHMARK-CASE-442。", "BENCHMARK-CASE-442"),
    ("输出可验证的 QR PNG；expected text: FINAL-RUN-5603。", "FINAL-RUN-5603"),
]

QR_TASKS = [
    _artifact_task(
        f"qr_hard_gap_{index:02d}",
        query,
        family="qr_artifact",
        target_name="qr_code",
        verifier={
            "kind": "qr_artifact",
            "name": f"qr_exact_payload_{index:02d}_v2",
            "filename": "pilot_qr.png",
            "value": value,
        },
    )
    for index, (query, value) in enumerate(_QR_SPECS, start=1)
]


# Two paraphrases per existing control produce 10 no-gap trials without
# introducing a different primitive tool.
NO_GAP_TASKS = list(EXPLICIT_TASKS) + [
    TaskCase(
        "control_weather_paraphrase",
        "查询上海现在的天气。",
        "weather",
        "single_tool",
        "no_gap",
        "ordinary",
        {
            "kind": "required_groups",
            "name": "weather_shanghai_v1",
            "groups": {
                "location": ("上海",),
                "weather": ("天气", "多云", "25°C", "25℃"),
            },
        },
    ),
    TaskCase(
        "control_calc_paraphrase",
        "计算 45 加 55。",
        "calc",
        "single_tool",
        "no_gap",
        "ordinary",
        {"kind": "exact_contains", "name": "calc_45plus55_v1", "value": "100"},
    ),
    TaskCase(
        "control_translate_paraphrase",
        "把 meeting 翻译成中文。",
        "translator",
        "single_tool",
        "no_gap",
        "ordinary",
        {
            "kind": "exact_contains",
            "name": "translate_meeting_v1",
            "value": "会议",
        },
    ),
    TaskCase(
        "control_calendar_paraphrase",
        "查一下我明天的日程。",
        "calendar",
        "single_tool",
        "no_gap",
        "ordinary",
        {
            "kind": "required_groups",
            "name": "calendar_tomorrow_v1",
            "groups": {
                "time": ("10:00", "十点"),
                "event": ("牙医", "预约"),
            },
        },
    ),
    TaskCase(
        "control_profile_paraphrase",
        "请告诉我个人资料里的姓名。",
        "profile",
        "single_tool",
        "no_gap",
        "ordinary",
        {"kind": "exact_contains", "name": "profile_name_v1", "value": "Alice"},
    ),
]

HARD_GAP_TASKS = PDF_TASKS + ICS_TASKS + QR_TASKS
