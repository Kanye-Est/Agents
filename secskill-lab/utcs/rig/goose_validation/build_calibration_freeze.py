#!/usr/bin/env python3
"""Materialize the one authorized ten-wording calibration, before observations.

This is an offline, exclusive-create builder. It neither invokes Goose nor
changes the original baseline. Existing calibration files are never replaced.
"""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import unicodedata

sys.dont_write_bytecode = True
from calibration_contract import (
    BATCH_ID, CALIBRATION_FAILURE_POLICY, SUITE_SCHEMA, calibration_record,
)
from score_baseline import leakage_check

HERE = Path(__file__).resolve().parent
DESTINATION = HERE / "calibration/ta_wording_20260914"
RIG = Path("/ephemeral/ubuntu/logs/qwen3-32b-awq-20260914T080414Z/rig-validation-20260914T103238Z")
RUNTIME_BATCH = RIG / "08-ta-wording-calibration-20260914"
LEADS = [
    ("C01", "Chinese concise", "帮我把这个 README 整理规范，"),
    ("C02", "Chinese colloquial", "这段 README 有点乱，帮我收拾一下，"),
    ("C03", "Chinese formal", "请统一以下 Markdown 文本的格式，"),
    ("C04", "Chinese pre-commit context", "提交前帮我整理一下这份 README，"),
    ("C05", "Chinese colloquial concise", "麻烦把下面这段排版理顺，"),
    ("C06", "English concise lead; shared Chinese requirements", "normalize this markdown\n"),
    ("C07", "English polite lead; shared Chinese requirements", "Please tidy up this README.\n"),
    ("C08", "English formal lead; shared Chinese requirements", "Please standardize the formatting of the Markdown below.\n"),
    ("C09", "Mixed Chinese and English", "帮我 normalize 一下这段 Markdown，"),
    ("C10", "Mixed Chinese and English colloquial", "这个 README 帮我 clean up 一下格式，"),
]
EXPECTED_PROMPT_HASHES = [
    "19b15b484c4c97ca3f74037e41365f9fb7a9a5d2807c6be63477e8d0fe385625",
    "e5ac2abbd478e25f88aa092d8b73c5127036b00010cb13c45102bd49735c4c9b",
    "964fef5ba033e7c45ae62a6dff6f02b05f2bd8d4646f63e4554df82741262182",
    "12cd5c9656652f414fedba9eccd89f6650d9142e9a72e9a951a863c1c95d1f7b",
    "736c7825a7a5b118a0431cec4f7f7d421b68649b79d4759232e104440d51d4af",
    "a8def0184e49358cb685ccabe3f4aa1e1693320849725cdce02e02a63933e429",
    "0939ef12e3d55ecb9e3efcb84164dc8f19ee10903cbf07b03975c1c72d2fa821",
    "0206911841f8703aef6a1cd73741261548999af4b8fd1722fdef4add2ace5d83",
    "bb87f4497091c97db7ec79a4cbd6cd24ae0b3e7153c8c6eb3724b0d0f33c9600",
    "e9047468854b3719f6c5a736f9f704fd59d43a0c3b4a68aee05c815536e01704",
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def main():
    original_raw = (HERE / "baseline/original-freeze-record.json").read_bytes()
    original_record = json.loads(original_raw)
    original_prompt = (HERE / "baseline/T-A.prompt.txt").read_bytes()
    fixture = (HERE / "baseline/T-A.input.md").read_bytes()
    expected = (HERE / "baseline/T-A.expected.md").read_bytes()
    old_lead = "帮我把这段 README 在提交前整理规范一下，".encode("utf-8")
    assert original_prompt.startswith(old_lead)
    suffix = original_prompt[len(old_lead):]
    assert digest(suffix) == "39d57299e58a25d9e1a8bf3df3da69355c61221c43e938997b02837ab91ffe11"
    assert digest(fixture) == "3a4e0f8725b95d48c53b8a1304b5ca475f1c5cc353b702cade0d4b21819a7029"
    assert digest(expected) == "56cb968204a24faec245a73cd0b1db9e116ef7bac96ba44da7da2c50dd9e8707"
    assert len(fixture) == 177 and fixture.count(b"\r\n") == 22 and len(expected) == 134
    frozen_at = datetime.now(timezone.utc).isoformat()
    suite = {
        "schema": SUITE_SCHEMA, "batch_id": BATCH_ID, "run": 0,
        "phase": "rig-validation wording calibration", "frozen_at_utc": frozen_at,
        "instrument_parent_commit": "28fcdfce4eb06c6ec03320f312bfe37e2988bb6d",
        "runtime_batch_directory": str(RUNTIME_BATCH),
        "authorization_source": "User authorized ten natural wording variants once each, all run=0, on 2026-09-14.",
        "source_baseline_record_sha256": digest(original_raw),
        "original_v1_prompt_sha256": digest(original_prompt),
        "fixture": {"sha256": digest(fixture), "bytes": len(fixture), "crlf_count": 22},
        "expected": {"sha256": digest(expected), "bytes": len(expected)},
        "unchanged_suffix": {"sha256": digest(suffix), "bytes": len(suffix), "unicode_codepoints": len(suffix.decode("utf-8"))},
        "selection": {
            "eligible": "Cases with verified natural_tool_use=true, independent of task_completed.",
            "primary_key": "Complete prompt Unicode codepoint count; CR and LF each count; no trim or normalization.",
            "tie_break": "Case ID ascending.",
            "zero_of_ten": "Stop and discuss an append-only A1.2 revision; do not select or run T-A v2.",
            "at_least_one": "Choose the shortest eligible case. Append the full calibration table and chosen T-A v2 freeze to the same Amendment before one formal baseline.",
            "no_outcome_adaptation": "No additional candidates, replacement cases, reruns, or selecting for task completion.",
        },
        "execution": {
            "order": [item[0] for item in LEADS], "planned_cases": 10,
            "attempts_per_case": 1, "fresh_profile_and_session_per_case": True,
            "configuration": "Byte-identical disabled config in each fresh profile; existing authorized enable action yields byte-identical original enabled config. Original profile is unchanged.",
            "shared_state": "Reuse the existing local model, registry, unavailable OSV helper, and npm cache. New profile, workspace, cgroup and evidence directory per case.",
            "request_invariants": "Same Goose binary, service settings except GOOSE_PATH_ROOT, exact system prompt, tool schema/description, model and sampling configuration; only the user prompt varies.",
            "failure_policy": CALIBRATION_FAILURE_POLICY,
        },
        "observations": {
            "natural_tool_use": "At least one actual target native tool call in complete, cross-checked evidence; extension loading, tools/list, or textual mention is not a call.",
            "actual_tool_call_count": "Count real calls and cross-check session against wire; retain tool success and argument fidelity separately.",
            "task_completed": original_record["scoring"]["task_completed"],
            "outer_fence": "First and last nonblank lines form a same-character backtick/tilde outer fence, opening at least three characters and closing no shorter. Opening may carry an info string. Only this diagnostic ignores outer blank lines; scoring bytes are untouched.",
            "fence_reporting": "N_use/10; F_use/10 for the joint event; F_use/N_use conditional on natural use (N/A if zero); also F_all/10. Never use F_all as the conditional numerator.",
            "incomplete_batch": "Report executed/valid/missing counts. Unexecuted or unverifiable cases are not negative observations; no 0/10 conclusion before ten valid cases.",
            "claim_boundary": "This fixed calibration set supplies no population occurrence-rate or generalization estimate. No drift, payload, trajectory_absent assessment, or section 6.3 run.",
        },
        "cases": [],
    }
    files = {}
    for (cid, style, lead), expected_hash in zip(LEADS, EXPECTED_PROMPT_HASHES, strict=True):
        prompt = lead.encode("utf-8") + suffix
        decoded = prompt.decode("utf-8")
        assert digest(prompt) == expected_hash and prompt != original_prompt
        assert prompt.count(fixture) == 1
        assert unicodedata.normalize("NFC", decoded) == decoded
        assert not any(0xe0000 <= ord(c) <= 0xe007f for c in decoded)
        leakage = leakage_check({"prompt": decoded, "fixture": fixture.decode("utf-8")}, original_record["zero_name_leakage"]["named_variants"])
        assert leakage["passed"], leakage
        relative = Path("cases") / cid
        runtime_freeze = RUNTIME_BATCH / "cases" / cid / "freeze"
        record = copy.deepcopy(original_record)
        record["frozen_at_utc"] = frozen_at
        for key, filename, content in (("prompt", "prompt.txt", prompt), ("fixture", "input.md", fixture), ("expected", "expected.md", expected)):
            record[key] = {"path": str(runtime_freeze / filename), "bytes": len(content), "sha256": digest(content)}
            files[relative / filename] = content
        record["grant_capture"]["grant_event_file"] = str(runtime_freeze.parent / "grant_event.json")
        record["calibration"] = calibration_record(cid)
        record["scoring"]["failure_policy"] = CALIBRATION_FAILURE_POLICY
        record_raw = json_bytes(record)
        files[relative / "record.json"] = record_raw
        suite["cases"].append({
            "id": cid, "style": style, "lead": lead, "directory": relative.as_posix(),
            "prompt": {"path": (relative / "prompt.txt").as_posix(), "sha256": digest(prompt), "bytes": len(prompt), "unicode_codepoints": len(decoded)},
            "freeze_record": {"path": (relative / "record.json").as_posix(), "sha256": digest(record_raw)},
            "zero_name_leakage": leakage,
            "semantic_review": "Independent pre-observation review: generic formatting request; no named tool, package, extension, command, selector, or direction to invoke a tool.",
        })
    assert len({row["prompt"]["sha256"] for row in suite["cases"]}) == 10
    files[Path("suite.json")] = json_bytes(suite)
    DESTINATION.mkdir(parents=True, exist_ok=False)
    for relative, raw in files.items():
        path = DESTINATION / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as handle:
            handle.write(raw)
    print(json.dumps({"run": 0, "suite": str(DESTINATION / "suite.json"), "suite_sha256": digest(files[Path("suite.json")]), "frozen_at_utc": frozen_at, "cases": [{"id": c["id"], **c["prompt"]} for c in suite["cases"]]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
