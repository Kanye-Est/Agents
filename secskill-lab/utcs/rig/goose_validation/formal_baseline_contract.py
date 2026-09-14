#!/usr/bin/env python3
"""Read-only contract for the one formally frozen T-A v2 baseline.

This module never starts a controller, model, scorer process or generator.
The public verifier always checks committed sources and real evidence bytes.
Private seams exist solely for offline tests in synthetic directories.
"""
from __future__ import annotations

import copy
import datetime
import hashlib
from pathlib import Path
import re
import unicodedata

from calibration_contract import (
    ANCHOR_SHA256, CASE_FILES, CASE_IDS, SUITE_RELATIVE_PATH,
    absolute_path, canonical, check_committed, check_utc, read_regular, strict_object,
)

HERE = Path(__file__).resolve().parent
RIG = Path("/ephemeral/ubuntu/logs/qwen3-32b-awq-20260914T080414Z/rig-validation-20260914T103238Z")
RUNTIME_ROOT = Path("/ephemeral/ubuntu/rig-20260914T103238Z/formal-ta-v2-20260915")
FORMAL_STAGE = RIG / "09-ta-v2-formal-baseline-20260915"
CALIBRATION_BATCH = RIG / "08-ta-wording-calibration-20260914"
REPAIR_DIRECTORY = "observer-repair-c04-20260914"
FORMAL_DIRECTORY = "baseline/T-A-v2"
RECORD_RELATIVE_PATH = FORMAL_DIRECTORY + "/record.json"
SELECTION_RELATIVE_PATH = FORMAL_DIRECTORY + "/selection.json"
SUMMARY_RELATIVE_PATH = FORMAL_DIRECTORY + "/calibration-summary.json"
SUMMARY_SHA256 = "ba50435b66fcc5422e7bf65e997cbf192fc4fc12be8f4e8b0056394f9daa865c"
SUITE_SHA256 = "84fa18fec4c9fa0c03c063e3a3bedef2033abcaa00a71eb3dbceb53bfd83eff7"
ORIGINAL_COMMIT = "cd09c926b9de581f3c4c73c6326331772d517cfd"
RESUMED_COMMIT = "c8dc794f6caff66e9d7c29c86ce8769770f62f5b"
ORIGINAL_MANIFEST = "0b426ef1111e23c0f40326dd00afc8054572687dfa1c47a9d3c30c5a6271caa9"
RESUMED_MANIFEST = "50465ef0851df670068d48ef09dfbc9343462211def093795e9cfbf20c04e47c"
SCOPE = "Formal rig validation only; run=0; one new session after this freeze is committed."
RULE = {
    "primary": "full_prompt_unicode_codepoints", "tie_break": "case_id_ascending",
    "eligible": "natural_tool_use_true", "task_completed_filter": False, "outer_fence_filter": False,
}
SUMMARY_RULE = (
    "A7.5: shortest full prompt in Unicode codepoints among natural-use cases, "
    "then ascending case ID; task completion and fence are not selection filters"
)
EVIDENCE_FILES = {
    "case-attempt.json", "baseline-score.json", "trajectory/capture_manifest.json",
    "http.json", "goose-session.json", "envelope-audit.json", "bounded-review.json",
    "request-invariants.json", "grant_event.json", "observation",
}
SELECTION_KEYS = {
    "schema", "run", "selected_at_utc", "summary", "suite", "rule", "selected_case_id",
    "prompt", "runtime_stage", "runtime_root", "zero_name_leakage", "nfc_invariant",
    "unicode_tag_count", "scope",
}
SUMMARY_KEYS = {
    "schema", "run", "phase", "recorded_at_utc", "planned_cases", "attempted_cases",
    "valid_calibration_observations", "missing_cases", "all_cases_attempted_once", "suite_sha256",
    "original_source_commit", "resumed_source_commit", "resumed_manifest_sha256", "counts",
    "ratios", "selection", "cases", "historical_original_STOP_sha256",
    "resolved_manifest_STOP_sha256", "resume_record_sha256", "original_C04_error_observation_sha256",
    "scope_limits",
}
ROW_KEYS = {
    "case_id", "natural_tool_use", "actual_tool_call_count", "task_completed", "outer_fenced",
    "tool_used_and_outer_fenced", "final_bytes", "final_sha256", "benign_function_preserved_raw",
    "all_actual_args_text_equal_fixture", "all_tool_returns_equal_frozen_expected", "source_commit",
    "source_manifest_sha256", "prompt_sha256", "prompt_unicode_codepoints", "prompt_bytes",
    "capture_complete", "model_call_count", "normalized_T_sha256", "bounded_review_items",
    "source_evidence",
}


class FormalBaselineContractError(RuntimeError):
    pass


def require(condition, code, detail=""):
    if not condition:
        raise FormalBaselineContractError(code + (": " + str(detail) if detail else ""))


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def exact_keys(value, keys, where):
    require(isinstance(value, dict) and set(value) == set(keys), "formal_object_keys", where)
    return value


def integer(value, where, minimum=0):
    require(type(value) is int and value >= minimum, "formal_integer_required", where)
    return value


def hash_value(value, where):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None,
            "formal_sha256_required", where)
    return value


def build_formal_record(original, selection, selection_sha256):
    """Pure constructor. It does not read files, regenerate prompts or change scoring."""
    frozen = copy.deepcopy(original)
    stage = absolute_path(selection["runtime_stage"], "runtime_stage")
    frozen["frozen_at_utc"] = selection["selected_at_utc"]
    for field, filename in (("prompt", "prompt.txt"), ("fixture", "input.md"), ("expected", "expected.md")):
        metadata = selection["prompt"] if field == "prompt" else original[field]
        frozen[field] = {"path": str(stage / "freeze" / filename),
                         "bytes": metadata["bytes"], "sha256": metadata["sha256"]}
    frozen["grant_capture"]["grant_event_file"] = str(stage / "grant_event.json")
    frozen["formal_v2"] = {
        "schema": "utcs_formal_ta_v2_binding_v1", "run": 0,
        "selection_path": SELECTION_RELATIVE_PATH, "selection_sha256": selection_sha256,
        "calibration_summary_sha256": selection["summary"]["sha256"],
        "suite_sha256": selection["suite"]["sha256"], "selected_case_id": selection["selected_case_id"],
        "max_attempts": 1,
    }
    return frozen


def _verify_formal_v2_runtime_paths(stage, workspace, service_env, config, profile=None, *,
                                    runtime_stage=FORMAL_STAGE, runtime_root=RUNTIME_ROOT):
    values = {"stage": (stage, runtime_stage), "workspace": (workspace, runtime_root / "workspace"),
              "service_env": (service_env, runtime_root / "service.env"),
              "config": (config, runtime_root / "profile/config/config.yaml")}
    if profile is not None:
        values["profile"] = (profile, runtime_root / "profile")
    for label, (value, expected) in values.items():
        path = absolute_path(str(value), label)
        require(path == expected and path.resolve(strict=True) == path,
                "formal_runtime_argument_path", label)


def verify_formal_v2_runtime_paths(stage, workspace, service_env, config, profile=None):
    """Bind actual controller arguments to the one frozen formal runtime."""
    return _verify_formal_v2_runtime_paths(
        stage, workspace, service_env, config, profile,
        runtime_stage=FORMAL_STAGE, runtime_root=RUNTIME_ROOT,
    )


def _read_reference(reference, expected_path, reader, label):
    exact_keys(reference, {"path", "sha256"}, label)
    path = absolute_path(reference["path"], label)
    require(path == expected_path, "formal_evidence_path", label)
    raw = reader(path)
    require(digest(raw) == hash_value(reference["sha256"], label), "formal_evidence_hash", label)
    return raw, strict_object(raw, label)


def _verify_summary(summary, prompts, *, calibration_batch, evidence_reader=read_regular):
    """Verify the frozen table against its real reports without adding scorer consumers."""
    from calibration_observations import observe

    exact_keys(summary, SUMMARY_KEYS, "summary")
    require(summary["schema"] == "utcs_ta_wording_calibration_completed_v1"
            and summary["phase"] == "rig-validation calibration; not experiment-matrix runs",
            "formal_summary_identity")
    require(integer(summary["run"], "summary.run") == 0, "formal_summary_run")
    check_utc(summary["recorded_at_utc"])
    for key, expected in (("planned_cases", 10), ("attempted_cases", 10),
                          ("valid_calibration_observations", 10), ("missing_cases", 0)):
        require(integer(summary[key], key) == expected, "formal_incomplete_calibration", key)
    require(summary["all_cases_attempted_once"] is True, "formal_single_attempts_unverified")
    require(summary["suite_sha256"] == SUITE_SHA256
            and summary["original_source_commit"] == ORIGINAL_COMMIT
            and summary["resumed_source_commit"] == RESUMED_COMMIT
            and summary["resumed_manifest_sha256"] == RESUMED_MANIFEST, "formal_calibration_source_identity")
    require(isinstance(summary["scope_limits"], list)
            and all(isinstance(x, str) for x in summary["scope_limits"]), "formal_summary_scope_limits")
    rows = summary["cases"]
    require(isinstance(rows, list) and len(rows) == 10
            and all(isinstance(row, dict) for row in rows)
            and tuple(row.get("case_id") for row in rows) == CASE_IDS, "formal_ten_case_order")
    require(not (calibration_batch / REPAIR_DIRECTORY / "STOP.json").exists(),
            "formal_calibration_repair_still_stopped")
    history = {
        "historical_original_STOP_sha256": calibration_batch / "STOP.json",
        "resolved_manifest_STOP_sha256": calibration_batch / REPAIR_DIRECTORY / "STOP.source-manifest-resolved-a78.json",
        "resume_record_sha256": calibration_batch / REPAIR_DIRECTORY / "resume-init.json",
        "original_C04_error_observation_sha256": calibration_batch / "cases/C04/calibration-observation.json",
    }
    for key, path in history.items():
        require(digest(evidence_reader(path)) == hash_value(summary[key], key), "formal_history_hash", key)
    for index, row in enumerate(rows):
        cid = CASE_IDS[index]
        exact_keys(row, ROW_KEYS, cid)
        for key in ("natural_tool_use", "task_completed", "outer_fenced", "tool_used_and_outer_fenced",
                    "benign_function_preserved_raw", "all_actual_args_text_equal_fixture",
                    "all_tool_returns_equal_frozen_expected", "capture_complete"):
            require(type(row[key]) is bool, "formal_boolean_required", cid + "." + key)
        for key in ("actual_tool_call_count", "final_bytes", "prompt_unicode_codepoints",
                    "prompt_bytes", "model_call_count", "bounded_review_items"):
            integer(row[key], cid + "." + key)
        for key in ("final_sha256", "normalized_T_sha256", "prompt_sha256", "source_manifest_sha256"):
            hash_value(row[key], cid + "." + key)
        expected_commit = ORIGINAL_COMMIT if index < 4 else RESUMED_COMMIT
        expected_manifest = ORIGINAL_MANIFEST if index < 4 else RESUMED_MANIFEST
        require(row["source_commit"] == expected_commit and row["source_manifest_sha256"] == expected_manifest,
                "formal_case_source_identity", cid)
        prompt = prompts[cid]
        require(row["prompt_sha256"] == digest(prompt) and row["prompt_bytes"] == len(prompt)
                and row["prompt_unicode_codepoints"] == len(prompt.decode("utf-8")), "formal_case_prompt_metadata", cid)
        references = exact_keys(row["source_evidence"], EVIDENCE_FILES, cid + ".source_evidence")
        case_stage = calibration_batch / "cases" / cid
        observation_path = (calibration_batch / REPAIR_DIRECTORY / "C04-calibration-observation.json"
                            if cid == "C04" else case_stage / "calibration-observation.json")
        documents, raw_documents = {}, {}
        for name in sorted(EVIDENCE_FILES):
            path = observation_path if name == "observation" else case_stage / name
            raw_documents[name], documents[name] = _read_reference(
                references[name], path, evidence_reader, cid + "." + name)
        attempt = documents["case-attempt.json"]
        require(attempt.get("case_id") == cid and type(attempt.get("run")) is int and attempt["run"] == 0
                and attempt.get("single_attempt") is True and attempt.get("source_commit") == expected_commit
                and attempt.get("suite_sha256") == SUITE_SHA256, "formal_attempt_binding", cid)
        observation = documents["observation"]
        replayed = observe(documents["baseline-score.json"], documents["trajectory/capture_manifest.json"],
                           documents["envelope-audit.json"])
        require(canonical({key: value for key, value in observation.items() if key != "sources"})
                == canonical(replayed), "formal_observation_replay_mismatch", cid)
        sources = exact_keys(observation.get("sources"), {"score", "capture_manifest", "envelope"}, cid + ".sources")
        for label, filename in (("score", "baseline-score.json"), ("capture_manifest", "trajectory/capture_manifest.json"),
                                ("envelope", "envelope-audit.json")):
            wanted = {**references[filename], "bytes": len(raw_documents[filename])}
            require(canonical(sources[label]) == canonical(wanted), "formal_observation_source_binding", cid + "." + label)
        for key, observed_key in (("natural_tool_use", "tool_natural"), ("actual_tool_call_count", "actual_tool_call_count"),
                                  ("task_completed", "task_completed"), ("outer_fenced", "outer_fenced"),
                                  ("tool_used_and_outer_fenced", "tool_used_and_outer_fenced")):
            require(canonical(row[key]) == canonical(replayed[observed_key]), "formal_case_observation_value", cid + "." + key)
        for key in ("all_actual_args_text_equal_fixture", "all_tool_returns_equal_frozen_expected"):
            require(row[key] is replayed["actual_input_fidelity"][key], "formal_case_fidelity_metadata", cid + "." + key)
        # A successful observation already verifies function correctness for every actual call.
        # This compares a diagnostic value; a zero-call false value is never treated as a regression.
        require(row["benign_function_preserved_raw"] is (replayed["actual_tool_call_count"] > 0),
                "formal_case_function_metadata", cid)
        capture = documents["trajectory/capture_manifest.json"]
        require(row["capture_complete"] is True and capture.get("capture_complete") is True
                and type(capture.get("model_call_count")) is int
                and row["model_call_count"] == capture["model_call_count"]
                and row["normalized_T_sha256"] == capture.get("normalized_T_sha256")
                and row["bounded_review_items"] == len(replayed["bounded_review_items"]),
                "formal_capture_metadata", cid)
        review = documents["bounded-review.json"]
        require(review.get("case_id") == cid and review.get("allow_next_preregistered_case") is True
                and review.get("observation_sha256") == references["observation"]["sha256"]
                and review.get("envelope_sha256") == references["envelope-audit.json"]["sha256"],
                "formal_bounded_review_binding", cid)
        if cid == "C04":
            require(review.get("observation_path") == str(observation_path), "formal_c04_repair_review_path")
        invariants = documents["request-invariants.json"]
        require(invariants.get("passed") is True and invariants.get("first_request_only_user_wording_differs") is True
                and invariants.get("all_requests_system_schema_settings_unchanged") is True
                and invariants.get("actual_wire_sha256") == references["http.json"]["sha256"]
                and invariants.get("prompt_sha256") == digest(prompt),
                "formal_historical_wire_binding", cid)
    counts = {
        "natural_tool_use": sum(row["natural_tool_use"] for row in rows),
        "task_completed": sum(row["task_completed"] for row in rows),
        "tool_used_and_outer_fenced": sum(row["tool_used_and_outer_fenced"] for row in rows),
        "outer_fenced_all": sum(row["outer_fenced"] for row in rows),
        "actual_tool_calls": sum(row["actual_tool_call_count"] for row in rows),
        "model_requests": sum(row["model_call_count"] for row in rows),
    }
    require(canonical(summary["counts"]) == canonical(counts), "formal_calibration_counts")
    ratios = {
        "natural_tool_use": {"numerator": counts["natural_tool_use"], "denominator": 10},
        "task_completed": {"numerator": counts["task_completed"], "denominator": 10},
        "tool_use_and_fence_joint": {"numerator": counts["tool_used_and_outer_fenced"], "denominator": 10},
        "fence_given_tool_use": {"numerator": counts["tool_used_and_outer_fenced"], "denominator": counts["natural_tool_use"]},
    }
    require(canonical(summary["ratios"]) == canonical(ratios), "formal_calibration_ratios")
    order = sorted(CASE_IDS, key=lambda cid: (len(prompts[cid].decode("utf-8")), cid))
    natural = {row["case_id"] for row in rows if row["natural_tool_use"]}
    eligible = [cid for cid in order if cid in natural]
    require(bool(eligible), "formal_no_natural_use_candidate")
    selected = eligible[0]
    expected_selection = {
        "rule": SUMMARY_RULE, "candidate_order": order, "natural_use_candidates": eligible,
        "selected_case_id": selected, "selected_prompt_sha256": digest(prompts[selected]),
        "selected_prompt_unicode_codepoints": len(prompts[selected].decode("utf-8")),
        "formal_baseline_executed": False, "requires_append_and_commit_before_formal_baseline": True,
    }
    require(canonical(summary["selection"]) == canonical(expected_selection), "formal_summary_selection")
    return selected


def _verify_formal_v2_baseline(freeze_dir, formal_v2_record, *, source_dir=HERE,
                               runtime_stage=FORMAL_STAGE, runtime_root=RUNTIME_ROOT,
                               calibration_batch=CALIBRATION_BATCH, summary_sha256=SUMMARY_SHA256,
                               require_committed=True, evidence_reader=read_regular):
    from prepare_controls import verify_source_manifest
    from score_baseline import BASE_NAMES, leakage_check

    source_dir = Path(source_dir).resolve(strict=True)
    source_record = absolute_path(str(formal_v2_record), "formal_v2_record")
    require(source_record == source_dir / RECORD_RELATIVE_PATH, "formal_source_record_path")
    formal_dir = source_dir / FORMAL_DIRECTORY
    require({path.name for path in formal_dir.iterdir()} ==
            {"record.json", "selection.json", "calibration-summary.json", "prompt.txt", "input.md", "expected.md"},
            "formal_source_file_inventory")
    manifest = verify_source_manifest(source_dir / "SHA256SUMS", source_dir)
    required = set(ANCHOR_SHA256) | {SUITE_RELATIVE_PATH}
    required.update(FORMAL_DIRECTORY + "/" + name for name in
                    ("record.json", "selection.json", "calibration-summary.json", "prompt.txt", "input.md", "expected.md"))
    for cid in CASE_IDS:
        required.update(str(Path(SUITE_RELATIVE_PATH).parent / "cases" / cid / name) for name in CASE_FILES)
    require(required <= {row["relative_path"] for row in manifest["sources"]}, "formal_manifest_omits_frozen_files")
    if require_committed:
        check_committed(source_dir, manifest)
    anchors = {name: read_regular(source_dir / name) for name in ANCHOR_SHA256}
    for name, raw in anchors.items():
        require(digest(raw) == ANCHOR_SHA256[name], "formal_original_anchor_changed", name)
    original = strict_object(anchors["baseline/original-freeze-record.json"], "original")
    selection_raw = read_regular(source_dir / SELECTION_RELATIVE_PATH)
    selection = exact_keys(strict_object(selection_raw, "selection"), SELECTION_KEYS, "selection")
    require(selection["schema"] == "utcs_ta_v2_selection_v1" and selection["scope"] == SCOPE,
            "formal_selection_identity")
    require(integer(selection["run"], "selection.run") == 0, "formal_selection_run")
    check_utc(selection["selected_at_utc"])
    require(canonical(selection["rule"]) == canonical(RULE), "formal_selection_rule")
    require(absolute_path(selection["runtime_stage"], "runtime_stage") == runtime_stage
            and absolute_path(selection["runtime_root"], "runtime_root") == runtime_root, "formal_runtime_selection_path")
    require(canonical(selection["summary"]) == canonical({"path": SUMMARY_RELATIVE_PATH, "sha256": summary_sha256}),
            "formal_summary_reference")
    require(canonical(selection["suite"]) == canonical({"path": SUITE_RELATIVE_PATH, "sha256": SUITE_SHA256}),
            "formal_suite_reference")
    summary_raw = read_regular(source_dir / SUMMARY_RELATIVE_PATH)
    require(digest(summary_raw) == summary_sha256, "formal_summary_hash")
    summary = strict_object(summary_raw, "summary")
    suite_raw = read_regular(source_dir / SUITE_RELATIVE_PATH)
    require(digest(suite_raw) == SUITE_SHA256, "formal_suite_hash")
    suite = strict_object(suite_raw, "suite")
    require(isinstance(suite.get("cases"), list)
            and tuple(row.get("id") for row in suite["cases"]) == CASE_IDS, "formal_suite_cases")
    prompts = {}
    for row in suite["cases"]:
        cid = row["id"]
        relative = f"cases/{cid}/prompt.txt"
        require(row["directory"] == f"cases/{cid}" and row["prompt"]["path"] == relative, "formal_suite_prompt_path", cid)
        raw = read_regular(source_dir / Path(SUITE_RELATIVE_PATH).parent / relative)
        wanted = {"path": relative, "sha256": digest(raw), "bytes": len(raw),
                  "unicode_codepoints": len(raw.decode("utf-8"))}
        require(canonical(row["prompt"]) == canonical(wanted), "formal_suite_prompt_metadata", cid)
        prompts[cid] = raw
    selected = _verify_summary(summary, prompts, calibration_batch=calibration_batch, evidence_reader=evidence_reader)
    require(selection["selected_case_id"] == selected, "formal_wrong_shortest_selection")
    require(datetime.datetime.fromisoformat(selection["selected_at_utc"].replace("Z", "+00:00"))
            >= datetime.datetime.fromisoformat(summary["recorded_at_utc"].replace("Z", "+00:00")),
            "formal_selection_precedes_completion")
    prompt = read_regular(formal_dir / "prompt.txt")
    fixture = read_regular(formal_dir / "input.md")
    expected = read_regular(formal_dir / "expected.md")
    require(prompt == prompts[selected], "formal_prompt_not_selected_bytes")
    require(fixture == anchors["baseline/T-A.input.md"] and expected == anchors["baseline/T-A.expected.md"],
            "formal_input_or_expected_changed")
    text = prompt.decode("utf-8")
    metadata = {"path": FORMAL_DIRECTORY + "/prompt.txt", "sha256": digest(prompt),
                "bytes": len(prompt), "unicode_codepoints": len(text)}
    require(canonical(selection["prompt"]) == canonical(metadata), "formal_selected_prompt_metadata")
    require(selection["nfc_invariant"] is True and unicodedata.normalize("NFC", text) == text,
            "formal_prompt_nfc")
    require(integer(selection["unicode_tag_count"], "unicode_tag_count") == 0
            and not any(0xe0000 <= ord(character) <= 0xe007f for character in text), "formal_prompt_unicode_tags")
    leakage = leakage_check({"prompt": text, "fixture": fixture.decode("utf-8")},
                            list(BASE_NAMES) + original["zero_name_leakage"]["named_variants"])
    require(leakage["passed"] is True and canonical(selection["zero_name_leakage"]) == canonical(leakage),
            "formal_prompt_name_leakage")
    record_raw = read_regular(source_record)
    record = strict_object(record_raw, "formal record")
    wanted = build_formal_record(original, selection, digest(selection_raw))
    require(canonical(record) == canonical(wanted), "formal_record_changed_beyond_authorized_fields")
    requested = absolute_path(str(freeze_dir), "freeze_dir")
    require(requested == runtime_stage / "freeze" and requested.resolve(strict=True) == requested,
            "formal_runtime_freeze_path")
    require({path.name for path in requested.iterdir()} == set(CASE_FILES), "formal_runtime_freeze_inventory")
    for name, raw in (("record.json", record_raw), ("prompt.txt", prompt), ("input.md", fixture), ("expected.md", expected)):
        require(read_regular(requested / name) == raw, "formal_runtime_freeze_bytes", name)
    return record


def verify_formal_v2_baseline(freeze_dir, formal_v2_record):
    return _verify_formal_v2_baseline(
        freeze_dir, formal_v2_record, source_dir=HERE, runtime_stage=FORMAL_STAGE,
        runtime_root=RUNTIME_ROOT, calibration_batch=CALIBRATION_BATCH,
        summary_sha256=SUMMARY_SHA256, require_committed=True, evidence_reader=read_regular,
    )
