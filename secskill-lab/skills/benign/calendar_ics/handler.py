"""Create a deterministic, importable iCalendar artifact."""

from __future__ import annotations

import os
import re
from pathlib import Path


def _to_ics_utc(value: str, missing: str) -> str:
    raw = value.strip()
    if re.fullmatch(r"\d{8}T\d{6}Z", raw):
        return raw
    match = re.fullmatch(
        r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})Z",
        raw,
    )
    if match:
        return "".join(match.groups()[:3]) + "T" + "".join(match.groups()[3:]) + "Z"
    return missing


def run(args):
    values = args or {}
    summary = str(values.get("title", "")).strip() or "MISSING_SUMMARY"
    start = _to_ics_utc(
        str(values.get("start_time", "")),
        "19700101T000000Z",
    )
    end = _to_ics_utc(
        str(values.get("end_time", "")),
        "19700101T010000Z",
    )
    text = "\r\n".join(
        [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//SecSkill Lab//Acquisition Pilot//EN",
            "CALSCALE:GREGORIAN",
            "BEGIN:VEVENT",
            "UID:advisor-sync-20260818@secskill.invalid",
            f"DTSTART:{start}",
            f"DTEND:{end}",
            f"SUMMARY:{summary}",
            "END:VEVENT",
            "END:VCALENDAR",
            "",
        ]
    )
    root = Path(os.environ["ACQUISITION_ARTIFACT_DIR"]).resolve()
    root.mkdir(parents=True, exist_ok=True)
    path = root / "advisor_sync.ics"
    path.write_text(text, encoding="utf-8", newline="")
    return f"ARTIFACT_CREATED path={path} type=text/calendar"
