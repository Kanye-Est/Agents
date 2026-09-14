#!/usr/bin/env python3
"""Record the explicitly authorized C04 observer repair without rewriting history.

Only C05-C10 may use this transition. C04 is classified offline from its saved
reports; the original STOP, observation error, attempts and batch freeze stay
byte-identical. A new STOP in the repair directory blocks all further work.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from prepare_controls import new_bytes, require, write_json

DIRECTORY = "observer-repair-c04-20260914"
SCHEMA = "utcs_calibration_resume_after_c04_v1"
REMAINING = [f"C{i:02d}" for i in range(5, 11)]
ORIGINAL_COMMIT = "cd09c926b9de581f3c4c73c6326331772d517cfd"
ORIGINAL_SUITE = "84fa18fec4c9fa0c03c063e3a3bedef2033abcaa00a71eb3dbceb53bfd83eff7"
ORIGINAL_EVIDENCE = {
    "STOP.json": "312130fc688be1903ea5f9b15abe84bbc8084b1859debe59e7436c320f3a4c87",
    "batch-init.json": "9079c1136e73038e45c0c882f759767914e511e5586635a59ba67d1deb7bb30b",
    "cases/C04/case-attempt.json": "36a5fdfc17cf201ec2a73689b753dbc2ec938d146b0067877dec2347a8b567d1",
    "cases/C04/calibration-observation.json": "c6ee7c9856d64a89841b2e8f86bb3e07bb4a6c99b73cec834f161edb157fb034",
    "cases/C04/baseline-score.json": "a565fd98b8f90bdc994dddc1a82e7c2c6dade02ad27bcd4282f3c7dc0a848b2a",
    "cases/C04/trajectory/capture_manifest.json": "ad9d04ecbe43ec5535c9799f0c1b20be8a88c6aee47ebc4ef64a828acd818c18",
    "cases/C04/envelope-audit.json": "8c7fcdab4c5939242723eae83d7ced168dcb579fceb5878f52ff16901fa04c4d",
    "cases/C04/http.json": "b59a52da64f7d9cc0ded993e61cb84954efb354936ccae4cb4c4d06aa566c4ab",
    "cases/C04/request-invariants.json": "f0c40305633cfd618e1c014d5a3aaefa155b4318fff5749013755ef60fea3e55",
}
# These are the only existing measurement files changed by this repair.
# Added helpers/tests are covered by the new committed source manifest.
REPAIRABLE_EXISTING_SOURCES = {
    "calibration_observations.py", "calibration_observations_selftest.py",
    "run_calibration_case.py",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def corrected_observation(batch):
    return Path(batch) / DIRECTORY / "C04-calibration-observation.json"


def verify_base(batch, manifest, source_dir):
    batch, source_dir = Path(batch), Path(source_dir)
    require(not (batch / DIRECTORY / "STOP.json").exists(), "Observer-repair continuation is stopped")
    for relative, expected in ORIGINAL_EVIDENCE.items():
        require(sha(batch / relative) == expected, "Original stopped evidence changed: " + relative)
    original = read(batch / "batch-init.json")["source_freeze"]
    require(original["git_commit"] == ORIGINAL_COMMIT, "Original source commit mismatch")
    require(manifest["git_commit"] != ORIGINAL_COMMIT, "Repair must have a new committed source freeze")
    require(manifest["suite_sha256"] == original["suite_sha256"] == ORIGINAL_SUITE,
            "Frozen ten-prompt suite changed")
    for entry in original["sources"]:
        relative = entry["relative_path"]
        require(sha(batch / "instruments" / relative) == entry["sha256"],
                "Original instrument snapshot changed: " + relative)
        if relative not in REPAIRABLE_EXISTING_SOURCES:
            require(sha(source_dir / relative) == entry["sha256"],
                    "Protected measurement source changed: " + relative)
    return original


def verify_c04_replay(batch):
    batch = Path(batch)
    path = corrected_observation(batch)
    observation = read(path)
    require(observation.get("status") == "observed" and observation.get("tool_natural") is True
            and observation.get("actual_tool_call_count") == 1
            and observation.get("task_completed") is False and observation.get("outer_fenced") is True,
            "C04 offline replay does not preserve the saved raw observations")
    for label, relative in (("score", "baseline-score.json"),
                            ("capture_manifest", "trajectory/capture_manifest.json"),
                            ("envelope", "envelope-audit.json")):
        source = batch / "cases/C04" / relative
        row = observation["sources"][label]
        require(row["path"] == str(source) and row["sha256"] == sha(source),
                "C04 replay does not consume the original report: " + label)
    review = read(batch / "cases/C04/bounded-review.json")
    require(review.get("case_id") == "C04" and review.get("allow_next_preregistered_case") is True
            and review.get("observation_path") == str(path)
            and review.get("observation_sha256") == sha(path)
            and review.get("envelope_sha256") == sha(batch / "cases/C04/envelope-audit.json"),
            "C04 corrected observation lacks a bound root review")


def record_repair(batch, manifest, source_dir, anchors):
    """No model call. Snapshot new instruments and bind one immutable transition."""
    batch, source_dir = Path(batch), Path(source_dir)
    directory = batch / DIRECTORY
    require(directory.is_dir(), "Offline replay directory is missing")
    require(not (directory / "resume-init.json").exists(), "Repair transition already recorded")
    original = verify_base(batch, manifest, source_dir)
    verify_c04_replay(batch)
    for cid in REMAINING:
        require(not (batch / "cases" / cid / "case-attempt.json").exists(),
                "Remaining case has already been attempted: " + cid)
    references = dict(ORIGINAL_EVIDENCE)
    for cid in ["C01", "C02", "C03", "C04"]:
        stage = batch / "cases" / cid
        require(read(stage / "case-attempt.json")["source_commit"] == ORIGINAL_COMMIT,
                "Historical case source commit mismatch")
        for filename in ("case-attempt.json", "calibration-observation.json", "baseline-score.json",
                         "envelope-audit.json", "bounded-review.json"):
            references[f"cases/{cid}/{filename}"] = sha(stage / filename)
        if cid != "C04":
            review = read(stage / "bounded-review.json")
            require(review.get("allow_next_preregistered_case") is True
                    and review["observation_sha256"] == sha(stage / "calibration-observation.json")
                    and review["envelope_sha256"] == sha(stage / "envelope-audit.json"),
                    "Historical review changed or incomplete: " + cid)
    references[f"{DIRECTORY}/C04-calibration-observation.json"] = sha(corrected_observation(batch))
    destination = directory / "instruments"
    destination.mkdir(exist_ok=False)
    for entry in manifest["sources"]:
        target = destination / entry["relative_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        new_bytes(target, (source_dir / entry["relative_path"]).read_bytes())
        require(sha(target) == entry["sha256"], "Repaired source snapshot mismatch")
    new_bytes(destination / "SHA256SUMS", (source_dir / "SHA256SUMS").read_bytes())
    record = {
        "schema": SCHEMA, "run": 0, "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "authorization": "User explicitly authorized correcting the observer, replaying saved C04 offline, freezing the repair and continuing C05-C10 once each.",
        "source_freeze": manifest, "original_source_freeze": original,
        "authorized_remaining_cases": REMAINING, "immutable_evidence": references,
        "runtime_anchors": anchors, "C04_model_retried": False, "original_STOP_preserved": True,
    }
    write_json(directory / "resume-init.json", record)
    return record


def load_repair(batch, manifest, source_dir, cid):
    require(cid in REMAINING, "Repair only authorizes the untouched C05-C10 cases")
    verify_base(batch, manifest, source_dir)
    record = read(Path(batch) / DIRECTORY / "resume-init.json")
    require(record.get("schema") == SCHEMA and record.get("run") == 0
            and record.get("authorized_remaining_cases") == REMAINING
            and record.get("C04_model_retried") is False
            and record.get("original_STOP_preserved") is True,
            "Invalid observer repair transition")
    for key in ("git_commit", "manifest_sha256", "suite_sha256"):
        require(manifest[key] == record["source_freeze"][key], "Source changed after observer repair: " + key)
    for relative, expected in record["immutable_evidence"].items():
        require(sha(Path(batch) / relative) == expected, "Recorded repair evidence changed: " + relative)
    verify_c04_replay(batch)
    return record
