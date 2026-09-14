#!/usr/bin/env python3
"""Run the committed T-A v2 formal baseline once, without calibration leniency.

The stage and profile are fixed. Existing evidence is never replaced. A failed
score stops the formal baseline after its offline evidence has been collected.
No experiment-matrix run, backend change, automatic retry, or service restart.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback

sys.dont_write_bytecode = True

from prepare_controls import new_bytes, require, write_json
from run_calibration_case import (
    ANCHORS, HERE, NODE, ORIGINAL_WIRE, PUBLISHED, PYTHON, REPO, RIG,
    command, sha, snapshot, source_freeze, verify_anchors,
)

STAGE = RIG / "09-ta-v2-formal-baseline-20260915"
RUNTIME = Path("/ephemeral/ubuntu/rig-20260914T103238Z/formal-ta-v2-20260915")
LOCK = RIG / ".formal-ta-v2-20260915.lock"
SOURCE = HERE / "baseline/T-A-v2"


def canonical(value):
    """Keep JSON scalar types distinct in the wire comparison."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def check_request_bodies(requests, reference, prompt):
    require(isinstance(requests, list) and bool(requests), "No formal model request")
    first = json.loads(canonical(requests[0]))
    require(isinstance(first.get("messages"), list) and len(first["messages"]) == 2
            and first["messages"][1].get("role") == "user",
            "Formal initial message shape changed")
    content = first["messages"][1].get("content")
    require(isinstance(content, str) and content.encode("utf-8") == prompt,
            "Actual formal prompt differs from its frozen bytes")
    first["messages"][1]["content"] = reference["messages"][1]["content"]
    require(canonical(first) == canonical(reference),
            "Formal initial request differs beyond the selected user wording")
    settings = {k: v for k, v in reference.items() if k != "messages"}
    for index, body in enumerate(requests):
        require(canonical(body["messages"][0]) == canonical(reference["messages"][0]),
                f"Formal system prompt changed in request {index}")
        require(canonical({k: v for k, v in body.items() if k != "messages"})
                == canonical(settings), f"Formal schema or settings changed in request {index}")


def request_invariants(stage, prompt):
    actual = json.loads((stage / "http.json").read_bytes())
    original = json.loads(ORIGINAL_WIRE.read_bytes())
    reference = next(e for e in original["exchanges"] if e["is_model_call"])["request"]["json"]
    requests = [e["request"]["json"] for e in actual["exchanges"] if e["is_model_call"]]
    check_request_bodies(requests, reference, prompt)
    write_json(stage / "request-invariants.json", {
        "run": 0, "passed": True, "model_requests": len(requests),
        "first_request_only_user_wording_differs": True,
        "all_requests_system_schema_settings_unchanged": True,
        "json_scalar_types_preserved": True,
        "reference_wire_sha256": sha(ORIGINAL_WIRE),
        "actual_wire_sha256": sha(stage / "http.json"),
        "prompt_sha256": hashlib.sha256(prompt).hexdigest(),
    })


def pre_review_state(score_exit, observer_exit):
    """Use the original scorer's CLI verdict, never a second field-name table."""
    require(type(score_exit) is int and score_exit in (0, 2), "Unexpected scorer exit")
    require(type(observer_exit) is int and observer_exit in (0, 2), "Unexpected observer exit")
    return "awaiting-bounded-review" if score_exit == observer_exit == 0 else "STOP"


def _reserve_stage(stage):
    # Atomic exclusive creation also prevents another invocation choosing this
    # stage after a failed preflight. There is no arbitrary-stage CLI argument.
    Path(stage).mkdir(exist_ok=False)


def _execute_reserved():
    from formal_baseline_contract import verify_formal_v2_baseline

    manifest = source_freeze()
    anchors = verify_anchors()
    write_json(STAGE / "case-attempt.json", {
        "run": 0, "phase": "formal T-A v2 rig validation", "single_attempt": True,
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": manifest["git_commit"],
        "source_manifest_sha256": manifest["manifest_sha256"],
        "formal_record_sha256": sha(SOURCE / "record.json"),
        "selection_sha256": sha(SOURCE / "selection.json"),
        "calibration_summary_sha256": sha(SOURCE / "calibration-summary.json"),
    })
    write_json(STAGE / "source-freeze.json", manifest)
    write_json(STAGE / "runtime-anchors-before.json", anchors)
    copied = STAGE / "instruments"
    copied.mkdir(exist_ok=False)
    for entry in manifest["sources"]:
        destination = copied / entry["relative_path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        new_bytes(destination, (HERE / entry["relative_path"]).read_bytes())
        require(sha(destination) == entry["sha256"], "Formal source snapshot mismatch")
    new_bytes(copied / "SHA256SUMS", (HERE / "SHA256SUMS").read_bytes())

    RUNTIME.mkdir(exist_ok=False)
    profile, workspace = RUNTIME / "profile", RUNTIME / "workspace"
    for folder in (profile / "config", profile / "state/logs", profile / "data", workspace):
        folder.mkdir(parents=True, exist_ok=False)
    config, service_env = profile / "config/config.yaml", RUNTIME / "service.env"
    new_bytes(config, ANCHORS["original_disabled"][0].read_bytes())
    original_env = ANCHORS["original_service_env"][0].read_bytes()
    previous_root = b"GOOSE_PATH_ROOT=/ephemeral/ubuntu/rig-20260914T103238Z/goose-profile\n"
    require(original_env.count(previous_root) == 1, "Ambiguous original Goose profile assignment")
    new_bytes(service_env, original_env.replace(
        previous_root, ("GOOSE_PATH_ROOT=" + str(profile) + "\n").encode(), 1))
    new_bytes(STAGE / "service.env", service_env.read_bytes())
    new_bytes(STAGE / "config.initial-disabled.yaml", config.read_bytes())
    freeze = STAGE / "freeze"
    freeze.mkdir(exist_ok=False)
    for name in ("prompt.txt", "input.md", "expected.md", "record.json"):
        new_bytes(freeze / name, (SOURCE / name).read_bytes())
    verify_formal_v2_baseline(freeze, SOURCE / "record.json")
    write_json(STAGE / "baseline-workspace-before.json", {"root": str(workspace), "entries": []})
    write_json(STAGE / "instance.json", {
        "run": 0, "profile": str(profile), "workspace": str(workspace),
        "config": str(config), "service_env": str(service_env),
        "disabled_config_sha256": sha(config), "service_env_sha256": sha(service_env),
        "source_commit": manifest["git_commit"], "manifest_sha256": manifest["manifest_sha256"],
    })
    common = ["--stage", STAGE, "--workspace", workspace, "--service-env", service_env,
              "--goose-bin", ANCHORS["goose_bin"][0], "--config", config,
              "--freeze-dir", freeze, "--source-manifest", HERE / "SHA256SUMS",
              "--formal-v2-record", SOURCE / "record.json"]
    snapshot(STAGE, "before-controls")
    command(STAGE, "prepare", [PYTHON, "-B", HERE / "prepare_controls.py", *common,
            "--unit", "utcs-rig-formal-v2-20260915.service",
            "--chain4", "UTCS_FV2_4_20260915", "--chain6", "UTCS_FV2_6_20260915",
            "--osv-ready", RIG / "05-validation/control/osv-ready.json",
            "--osv-unit", "utcs-rig-osv-20260914-103238.service", "--osv-pid", "71270"])
    snapshot(STAGE, "after-controls")
    current = source_freeze()
    require(current["git_commit"] == manifest["git_commit"]
            and current["manifest_sha256"] == manifest["manifest_sha256"],
            "Formal source changed before launch")
    command(STAGE, "launch", [PYTHON, "-B", HERE / "launch_baseline.py", *common,
            "--profile", profile, "--repo", REPO, "--config-record", ANCHORS["config_record"][0]])
    snapshot(STAGE, "after-baseline")
    require(sha(config) == ANCHORS["original_config"][1], "Formal enabled config differs from original")
    write_json(STAGE / "runtime-anchors-after.json", verify_anchors())
    command(STAGE, "http-decode", [PYTHON, "-B", HERE / "http_capture.py", "--pcap", STAGE / "model-api.pcap",
            "--tcpdump-stderr", STAGE / "tcpdump.stderr.log", "--output", STAGE / "http.json"])
    command(STAGE, "trajectory-adapter", [PYTHON, "-B", HERE / "goose_trajectory_adapter.py",
            "--wire", STAGE / "http.json", "--request-log-dir", STAGE / "request-logs",
            "--session", STAGE / "goose-session.json", "--completion", STAGE / "capture-completion.json",
            "--consumer", REPO / "secskill-lab/utcs/trajectory_absence.py", "--out-dir", STAGE / "trajectory"])
    request_invariants(STAGE, (freeze / "prompt.txt").read_bytes())
    # Preserve all offline reports even when the original formal scoring gate
    # fails. No following command can start another Goose/model session.
    score_exit = command(STAGE, "baseline-score", [PYTHON, "-B", HERE / "score_baseline.py",
            "--session", STAGE / "goose-session.json", "--wire", STAGE / "http.json",
            "--freeze", freeze / "record.json", "--expected", freeze / "expected.md",
            "--fixture", freeze / "input.md", "--prompt", freeze / "prompt.txt",
            "--node", NODE, "--tool-module", PUBLISHED / "tool.js", "--output", STAGE / "baseline-score.json"],
            allowed=(0, 2))
    command(STAGE, "envelope-audit", [PYTHON, "-B", HERE / "audit_baseline_envelope.py",
            "--stage", STAGE, "--workspace", workspace, "--output", STAGE / "envelope-audit.json"], allowed=(0, 2))
    observer_exit = command(STAGE, "formal-observation", [PYTHON, "-B", HERE / "calibration_observations.py",
            "--score", STAGE / "baseline-score.json", "--capture-manifest", STAGE / "trajectory/capture_manifest.json",
            "--envelope", STAGE / "envelope-audit.json", "--output", STAGE / "formal-observation.json"], allowed=(0, 2))
    snapshot(STAGE, "after-offline-review-inputs")
    final_source = source_freeze()
    require(final_source["git_commit"] == manifest["git_commit"]
            and final_source["manifest_sha256"] == manifest["manifest_sha256"],
            "Formal source changed during execution")
    state = pre_review_state(score_exit, observer_exit)
    outcome = {
        "run": 0, "phase": "formal T-A v2 rig validation", "state": state,
        "source_commit": manifest["git_commit"], "manifest_sha256": manifest["manifest_sha256"],
        "scorer_exit_code": score_exit, "observer_exit_code": observer_exit,
        "calibration_leniency_applied": False, "formal_baseline_passed": False,
        "root_review_required": True, "human_readthrough_completed": False,
        "evidence": {name: {"path": str(STAGE / name), "sha256": sha(STAGE / name)} for name in
                     ("baseline-score.json", "formal-observation.json", "envelope-audit.json",
                      "trajectory/capture_manifest.json", "request-invariants.json")},
        "no_automatic_retry": True,
    }
    write_json(STAGE / "outcome.json", outcome)
    if state == "STOP":
        write_json(STAGE / "STOP.json", {**outcome,
                   "reason": "Original formal scorer or evidence validation failed; preserve evidence and stop."})
    print(json.dumps(outcome, ensure_ascii=False, indent=2), flush=True)
    return 2 if state == "STOP" else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", required=True)
    parser.parse_args(argv)
    os.umask(0o077)
    with LOCK.open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(json.dumps({"run": 0, "state": "STOP", "reason": "Formal invocation already running; no retry"}))
            return 2
        try:
            _reserve_stage(STAGE)
        except FileExistsError:
            print(json.dumps({"run": 0, "state": "STOP", "reason": "Formal stage already exists; original evidence preserved"}))
            return 2
        try:
            return _execute_reserved()
        except BaseException as error:
            failure = {"run": 0, "state": "STOP", "reason": str(error),
                       "traceback": traceback.format_exc(), "no_automatic_retry": True,
                       "recorded_at_utc": datetime.now(timezone.utc).isoformat()}
            if not (STAGE / "STOP.json").exists():
                write_json(STAGE / "STOP.json", failure)
            print(json.dumps(failure, ensure_ascii=False, indent=2), flush=True)
            return 2


if __name__ == "__main__":
    raise SystemExit(main())
