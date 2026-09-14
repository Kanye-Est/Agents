#!/usr/bin/env python3
"""Execute only the next member of the precommitted ten-case calibration.

Each invocation stops after one case for an explicit bounded evidence review.
The existing launch, capture, adapter, scorer and envelope auditor are reused.
No experiment-matrix run, automatic retry, service restart or dependency change.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback

sys.dont_write_bytecode = True
from prepare_controls import new_bytes, require, verify_source_manifest, write_json

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SUITE = HERE / "calibration/ta_wording_20260914/suite.json"
RIG = Path("/ephemeral/ubuntu/logs/qwen3-32b-awq-20260914T080414Z/rig-validation-20260914T103238Z")
RUNTIME = Path("/ephemeral/ubuntu/rig-20260914T103238Z")
BATCH = RIG / "08-ta-wording-calibration-20260914"
CASE_RUNTIME = RUNTIME / "calibration-ta-wording-20260914"
PYTHON = "/ephemeral/ubuntu/venvs/secskill/bin/python"
NODE = RUNTIME / "node-v24.21.0-linux-x64/bin/node"
GOOSE = RUNTIME / "goose-bin/goose"
PUBLISHED = RIG / "02-publish-retry2/published-artifact/package/src"
ORIGINAL_WIRE = RIG / "06-validation-retry1-20260914T130908Z/http.json"
ANCHORS = {
    "original_config": (RUNTIME / "goose-profile/config/config.yaml", "63455f6e7e4f8ae11e5d18f8cec1c52f1762b56d1ed207878a4b397c721731d6"),
    "original_service_env": (RUNTIME / "goose-service.env", "ed8c3402db62fffc2d58d1d29c02c654fde4c12bdc0005ad6eab2b48d6297b18"),
    "npm_config": (RUNTIME / "npm-local.npmrc", "d6c4e9588b8abae167066691ed782dc569c86c6ca768f0dd32bdc46fce544d6f"),
    "goose_bin": (GOOSE, "9ef3ae45d819e41d1b7bcb1533033765d1e1876aba4a35ff0f6e722337512b3b"),
    "published_tool": (PUBLISHED / "tool.js", "ae83a2e95541caddec475a1af2b907f8f847060500e455f54260c966d2e3fa43"),
    "published_implementation": (PUBLISHED / "mdclean.js", "d79d1a4c89ada4b90f8666cad2e285afe5d52e1861916e5b4b0843dddce875bc"),
    "chat_template": (REPO / "deploy/hyperstack/qwen3_thinkoff.jinja", "891703c669150f0fcd55bb5fb88d9d605b5e310cfb90a00f13420adb6399d64a"),
    "config_record": (RIG / "04-config/result.json", "ac6ce56bb58f817b27b7b09c2629a8199a8d5a59ffb0ada172a8413664f8c1ba"),
    "original_disabled": (RIG / "04-config/config.disabled.yaml", "b64dbf1706d7d87eb5c4e96876a011d8d44756213ce39a130a7dd758f66ac8c4"),
    "node_bin": (NODE, "7fde7b8afa198da66257f42ee2001d874c7355631e6d1579a5fb5ef1f246df4c"),
    "original_wire": (ORIGINAL_WIRE, "83c599388cfa851691ed9cd1681d817b17c7aae8a8eb2a2a90d7ddc6a47a81bd"),
    "adapter_v1_2": (HERE / "goose_trajectory_adapter.py", "6a4064f32279c1b255f1d580053063bd35739ec1211b6d6b530a51ae03c3142a"),
}


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def command(directory, label, argv, allowed=(0,)):
    with (directory / (label + ".stdout.txt")).open("xb") as out, (directory / (label + ".stderr.txt")).open("xb") as err:
        began = datetime.now(timezone.utc).isoformat()
        result = subprocess.run([str(arg) for arg in argv], stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    write_json(directory / (label + ".receipt.json"), {
        "run": 0, "argv": [str(arg) for arg in argv], "started_at_utc": began,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(), "exit_code": result.returncode,
        "stdout_sha256": sha(directory / (label + ".stdout.txt")),
        "stderr_sha256": sha(directory / (label + ".stderr.txt")),
    })
    print(json.dumps({"step": label, "exit_code": result.returncode, "run": 0}), flush=True)
    require(result.returncode in allowed, f"STOP: {label} exit={result.returncode}; original stdout/stderr retained in {directory}")
    return result.returncode


def snapshot(directory, label):
    command(directory, "snapshot-" + label, ["bash", "-c", 'set -euo pipefail; source "$1"; rig_snapshot "$2" "$3"; rig_check_core "$2" "$3"',
            "rig-snapshot", HERE / "rig_helpers.sh", directory, label])


def verify_anchors():
    record = {}
    for name, (path, expected) in ANCHORS.items():
        actual = sha(path)
        require(actual == expected, "Runtime anchor changed: " + name)
        record[name] = {"path": str(path), "sha256": actual, "bytes": path.stat().st_size}
    return record


def source_freeze():
    require(REPO == Path("/ephemeral/ubuntu/src/hello-agents-lab"), "Execution is restricted to the recorded VM repository")
    manifest = verify_source_manifest(HERE / "SHA256SUMS")
    status = subprocess.check_output(["git", "-C", str(REPO), "status", "--porcelain=v1", "--untracked-files=all", "--", str(HERE)])
    require(status == b"", "Instrumentation tree is not clean and committed")
    tracked = [str(HERE / entry["relative_path"]) for entry in manifest["sources"]] + [str(HERE / "SHA256SUMS")]
    subprocess.run(["git", "-C", str(REPO), "ls-files", "--error-unmatch", "--", *tracked], check=True, stdout=subprocess.DEVNULL)
    manifest["git_commit"] = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"]).decode().strip()
    manifest["suite_sha256"] = sha(SUITE)
    return manifest


def initialize():
    BATCH.mkdir(parents=False, exist_ok=True)
    require(not (BATCH / "batch-init.json").exists(), "Batch already initialized; no reinitialization")
    require(not (BATCH / "STOP.json").exists(), "Batch is stopped")
    manifest = source_freeze()
    suite = json.loads(SUITE.read_bytes())
    require(suite["runtime_batch_directory"] == str(BATCH), "Batch path mismatch")
    snapshot(BATCH, "before-calibration-freeze")
    anchors = verify_anchors()
    copy_root = BATCH / "instruments"
    copy_root.mkdir(exist_ok=False)
    for entry in manifest["sources"]:
        source = HERE / entry["relative_path"]
        target = copy_root / entry["relative_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as output:
            output.write(source.read_bytes())
        require(sha(target) == entry["sha256"], "Instrument snapshot hash mismatch")
    new_bytes(copy_root / "SHA256SUMS", (HERE / "SHA256SUMS").read_bytes())
    (BATCH / "cases").mkdir(exist_ok=False)
    CASE_RUNTIME.mkdir(exist_ok=False)
    original_env = ANCHORS["original_service_env"][0].read_bytes()
    old_assignment = ("GOOSE_PATH_ROOT=" + str(RUNTIME / "goose-profile") + "\n").encode()
    require(original_env.count(old_assignment) == 1, "Service environment has ambiguous profile assignment")
    from prepare_controls import verify_frozen_baseline
    prepared = []
    for row in suite["cases"]:
        cid = row["id"]
        stage = BATCH / "cases" / cid
        stage.mkdir(exist_ok=False)
        runtime = CASE_RUNTIME / cid
        runtime.mkdir(exist_ok=False)
        profile, workspace = runtime / "profile", runtime / "workspace"
        for subdir in (profile / "config", profile / "state/logs", profile / "data", workspace):
            subdir.mkdir(parents=True, exist_ok=False)
        config = profile / "config/config.yaml"
        new_bytes(config, ANCHORS["original_disabled"][0].read_bytes())
        service_env = runtime / "service.env"
        replacement = ("GOOSE_PATH_ROOT=" + str(profile) + "\n").encode()
        new_bytes(service_env, original_env.replace(old_assignment, replacement, 1))
        new_bytes(stage / "service.env", service_env.read_bytes())
        new_bytes(stage / "config.initial-disabled.yaml", config.read_bytes())
        freeze = stage / "freeze"
        freeze.mkdir(exist_ok=False)
        for filename in ("prompt.txt", "input.md", "expected.md", "record.json"):
            new_bytes(freeze / filename, (SUITE.parent / row["directory"] / filename).read_bytes())
        verify_frozen_baseline(freeze, SUITE, cid)
        write_json(stage / "baseline-workspace-before.json", {"root": str(workspace), "entries": []})
        record = {"run": 0, "case_id": cid, "stage": str(stage), "profile": str(profile), "workspace": str(workspace),
                  "service_env": str(service_env), "service_env_sha256": sha(service_env), "config": str(config),
                  "disabled_config_sha256": sha(config), "prompt_sha256": row["prompt"]["sha256"],
                  "freeze_dir": str(freeze), "unit": f"utcs-rig-cal-{cid}-20260914.service",
                  "chain4": f"UTCS_C4_{cid}_20260914", "chain6": f"UTCS_C6_{cid}_20260914"}
        write_json(stage / "case-prepared.json", record)
        prepared.append(record)
    snapshot(BATCH, "after-calibration-freeze")
    write_json(BATCH / "batch-init.json", {
        "run": 0, "phase": "rig-validation wording calibration", "initialized_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_freeze": manifest, "runtime_anchors": anchors, "prepared_cases": prepared,
        "model_requests_issued": 0, "original_profile_unchanged": True,
    })
    print(json.dumps({"state": "ten-cases-frozen-and-prepared", "run": 0, "batch": str(BATCH), "git_commit": manifest["git_commit"],
                      "suite_sha256": manifest["suite_sha256"], "planned": len(prepared)}, indent=2), flush=True)


def request_invariants(stage, prompt):
    actual = json.loads((stage / "http.json").read_bytes())
    reference = json.loads(ORIGINAL_WIRE.read_bytes())
    reference_body = next(x for x in reference["exchanges"] if x["is_model_call"])["request"]["json"]
    requests = [x["request"]["json"] for x in actual["exchanges"] if x["is_model_call"]]
    require(requests, "No actual model request")
    first = json.loads(json.dumps(requests[0]))
    require(len(first["messages"]) == 2 and first["messages"][1]["role"] == "user", "Initial request message shape changed")
    require(first["messages"][1]["content"].encode("utf-8") == prompt, "Actual prompt differs from frozen case")
    first["messages"][1]["content"] = reference_body["messages"][1]["content"]
    require(first == reference_body, "Initial request differs from T-A v1 beyond the authorized user wording")
    for index, body in enumerate(requests):
        require(body["messages"][0] == reference_body["messages"][0], f"System prompt changed in request {index}")
        require({k: v for k, v in body.items() if k != "messages"} == {k: v for k, v in reference_body.items() if k != "messages"},
                f"Request schema or configuration changed in request {index}")
    record = {"run": 0, "passed": True, "model_requests": len(requests), "first_request_only_user_wording_differs": True,
              "all_requests_system_schema_settings_unchanged": True, "reference_wire_sha256": sha(ORIGINAL_WIRE),
              "actual_wire_sha256": sha(stage / "http.json"), "prompt_sha256": hashlib.sha256(prompt).hexdigest()}
    write_json(stage / "request-invariants.json", record)
    return record


def execute_case(cid):
    require(not (BATCH / "STOP.json").exists(), "Batch is stopped; no automatic retry")
    initialization = json.loads((BATCH / "batch-init.json").read_bytes())
    manifest = source_freeze()
    require(manifest["git_commit"] == initialization["source_freeze"]["git_commit"], "Source commit changed during calibration")
    require(manifest["manifest_sha256"] == initialization["source_freeze"]["manifest_sha256"], "Source manifest changed during calibration")
    suite = json.loads(SUITE.read_bytes())
    order = [row["id"] for row in suite["cases"]]
    require(cid in order, "Unknown case")
    position = order.index(cid)
    for previous in order[:position]:
        previous_stage = BATCH / "cases" / previous
        review = json.loads((previous_stage / "bounded-review.json").read_bytes())
        require(review.get("case_id") == previous and review.get("allow_next_preregistered_case") is True,
                "Previous case lacks explicit bounded review")
        require(review.get("observation_sha256") == sha(previous_stage / "calibration-observation.json"),
                "Previous review does not bind to its observation")
        require(review.get("envelope_sha256") == sha(previous_stage / "envelope-audit.json"),
                "Previous review does not bind to its envelope evidence")
    for other in order[position + 1:]:
        require(not (BATCH / "cases" / other / "case-attempt.json").exists(), "Cases executed out of frozen order")
    stage = BATCH / "cases" / cid
    require(not (stage / "case-attempt.json").exists(), "Case already attempted; no retry")
    prepared = json.loads((stage / "case-prepared.json").read_bytes())
    new_bytes(stage / "case-attempt.json", (json.dumps({"case_id": cid, "run": 0,
              "started_at_utc": datetime.now(timezone.utc).isoformat(), "source_commit": manifest["git_commit"],
              "suite_sha256": sha(SUITE), "single_attempt": True}, indent=2) + "\n").encode())
    snapshot(stage, "before-controls")
    write_json(stage / "runtime-anchors-before.json", verify_anchors())
    require(sha(prepared["service_env"]) == prepared["service_env_sha256"], "Case service environment changed")
    require(sha(prepared["config"]) == prepared["disabled_config_sha256"], "Case initial configuration changed")
    common = ["--stage", stage, "--workspace", prepared["workspace"], "--service-env", prepared["service_env"],
              "--goose-bin", GOOSE, "--config", prepared["config"], "--freeze-dir", prepared["freeze_dir"],
              "--source-manifest", HERE / "SHA256SUMS", "--calibration-suite", SUITE, "--calibration-case", cid]
    command(stage, "prepare", [PYTHON, "-B", HERE / "prepare_controls.py", *common,
            "--unit", prepared["unit"], "--chain4", prepared["chain4"], "--chain6", prepared["chain6"],
            "--osv-ready", RIG / "05-validation/control/osv-ready.json", "--osv-unit", "utcs-rig-osv-20260914-103238.service", "--osv-pid", "71270"])
    snapshot(stage, "after-controls")
    command(stage, "launch", [PYTHON, "-B", HERE / "launch_baseline.py", *common,
            "--profile", prepared["profile"], "--repo", REPO, "--config-record", ANCHORS["config_record"][0]])
    snapshot(stage, "after-baseline")
    require(sha(prepared["config"]) == ANCHORS["original_config"][1], "Enabled case config differs from original enabled config")
    write_json(stage / "runtime-anchors-after.json", verify_anchors())
    command(stage, "http-decode", [PYTHON, "-B", HERE / "http_capture.py", "--pcap", stage / "model-api.pcap",
            "--tcpdump-stderr", stage / "tcpdump.stderr.log", "--output", stage / "http.json"])
    command(stage, "trajectory-adapter", [PYTHON, "-B", HERE / "goose_trajectory_adapter.py", "--wire", stage / "http.json",
            "--request-log-dir", stage / "request-logs", "--session", stage / "goose-session.json", "--completion", stage / "capture-completion.json",
            "--consumer", REPO / "secskill-lab/utcs/trajectory_absence.py", "--out-dir", stage / "trajectory"])
    request_invariants(stage, (Path(prepared["freeze_dir"]) / "prompt.txt").read_bytes())
    command(stage, "baseline-score", [PYTHON, "-B", HERE / "score_baseline.py", "--session", stage / "goose-session.json", "--wire", stage / "http.json",
            "--freeze", Path(prepared["freeze_dir"]) / "record.json", "--expected", Path(prepared["freeze_dir"]) / "expected.md",
            "--fixture", Path(prepared["freeze_dir"]) / "input.md", "--prompt", Path(prepared["freeze_dir"]) / "prompt.txt",
            "--node", NODE, "--tool-module", PUBLISHED / "tool.js", "--output", stage / "baseline-score.json"], allowed=(0, 2))
    command(stage, "envelope-audit", [PYTHON, "-B", HERE / "audit_baseline_envelope.py", "--stage", stage,
            "--workspace", prepared["workspace"], "--output", stage / "envelope-audit.json"], allowed=(0, 2))
    command(stage, "calibration-observation", [PYTHON, "-B", HERE / "calibration_observations.py", "--score", stage / "baseline-score.json",
            "--capture-manifest", stage / "trajectory/capture_manifest.json", "--envelope", stage / "envelope-audit.json",
            "--output", stage / "calibration-observation.json"])
    snapshot(stage, "after-offline-review-inputs")
    observation = json.loads((stage / "calibration-observation.json").read_bytes())
    summary_keys = ("status", "calibration_outcome", "tool_natural", "actual_tool_call_count", "task_completed",
                    "score_all_pass", "outer_fenced", "tool_used_and_outer_fenced", "needs_bounded_review")
    print(json.dumps({"run": 0, "case_id": cid, "state": "awaiting-bounded-evidence-review",
                      "observation": {key: observation[key] for key in summary_keys},
                      "bounded_review_item_count": len(observation["bounded_review_items"]),
                      "stage": str(stage)}, ensure_ascii=False, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--initialize", action="store_true")
    action.add_argument("--case", choices=[f"C{i:02d}" for i in range(1, 11)])
    args = parser.parse_args()
    os.umask(0o077)
    BATCH.mkdir(parents=False, exist_ok=True)
    with (BATCH / ".orchestration.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            initialize() if args.initialize else execute_case(args.case)
        except BaseException as error:
            failure = {"run": 0, "case_id": args.case, "status": "STOP; no automatic retry",
                       "error": str(error), "traceback": traceback.format_exc(),
                       "recorded_at_utc": datetime.now(timezone.utc).isoformat()}
            if not (BATCH / "STOP.json").exists():
                write_json(BATCH / "STOP.json", failure)
            print(json.dumps(failure, ensure_ascii=False, indent=2), flush=True)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
