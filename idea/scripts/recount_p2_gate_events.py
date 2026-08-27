#!/usr/bin/python3 -S
"""Recount P2-denied hard-gap gate trials and events from raw result JSON.

This intentionally reads the full raw results rather than ``*.analysis.json``:
the event-level ``approval_gate_blocked`` records live only in the raw files.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SCRIPT = Path(__file__).resolve()
LAB_ROOT = SCRIPT.parents[2]
RESULTS = LAB_ROOT / "secskill-lab" / "acquisition" / "results"

INPUTS = (
    (
        "Qwen × text",
        RESULTS / "policy_hardgap_causal_v2_full_20260726.json",
    ),
    (
        "Llama × text",
        RESULTS / "policy_hardgap_causal_v2_full_llama3.3-70b-awq-s1_20260726.json",
    ),
    (
        "Qwen × native FC",
        RESULTS / "policy_hardgap_causal_v2_full_qwen3-32b-awq-native-fc_20260726.json",
    ),
)


def is_p2_hard(row: dict[str, Any]) -> bool:
    return row.get("policy") == "P2" and row.get("gap_type") == "hard_artifact_gap"


def count_file(label: str, path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = [row for row in payload["rows"] if is_p2_hard(row)]

    blocked_trials = 0
    blocked_events = 0
    install_emitted_events = 0
    install_parsed_events = 0
    install_started_events = 0

    for row in rows:
        row_blocked = 0
        for event in row.get("events", []):
            if event.get("tool_name") != "install_skill":
                continue
            kind = event.get("kind")
            if kind == "tool_call_emitted":
                install_emitted_events += 1
            elif kind == "tool_call_parsed":
                install_parsed_events += 1
            elif kind == "approval_gate_blocked":
                blocked_events += 1
                row_blocked += 1
            elif kind == "tool_execution_started":
                install_started_events += 1
        blocked_trials += int(row_blocked > 0)

    return {
        "cell": label,
        "source": str(path),
        "p2_hard_trials": len(rows),
        "trials_with_block": blocked_trials,
        "blocked_install_events": blocked_events,
        "install_emitted_events": install_emitted_events,
        "install_parsed_events": install_parsed_events,
        "install_execution_started_events": install_started_events,
    }


def render_markdown(rows: list[dict[str, Any]], totals: dict[str, int]) -> str:
    lines = [
        "| Cell | P2 hard trials | Trials with ≥1 block | Blocked install events | Install starts |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['cell']} | {row['p2_hard_trials']} | "
            f"{row['trials_with_block']} | {row['blocked_install_events']} | "
            f"{row['install_execution_started_events']} |"
        )
    lines.append(
        f"| **Total** | **{totals['p2_hard_trials']}** | "
        f"**{totals['trials_with_block']}** | "
        f"**{totals['blocked_install_events']}** | "
        f"**{totals['install_execution_started_events']}** |"
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    args = parser.parse_args()

    rows = [count_file(label, path) for label, path in INPUTS]
    totals = {
        key: sum(int(row[key]) for row in rows)
        for key in (
            "p2_hard_trials",
            "trials_with_block",
            "blocked_install_events",
            "install_emitted_events",
            "install_parsed_events",
            "install_execution_started_events",
        )
    }

    expected = {
        "p2_hard_trials": 90,
        "trials_with_block": 65,
        "blocked_install_events": 99,
        "install_execution_started_events": 0,
    }
    observed = {key: totals[key] for key in expected}
    if observed != expected:
        raise SystemExit(f"frozen recount mismatch: expected={expected}, observed={observed}")

    if args.format == "json":
        print(json.dumps({"cells": rows, "totals": totals}, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(rows, totals))


if __name__ == "__main__":
    main()
