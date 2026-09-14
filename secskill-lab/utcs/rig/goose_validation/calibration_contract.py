#!/usr/bin/env python3
"""Strict read-only contract for the one frozen ten-case T-A wording calibration.

The original baseline lock remains in prepare_controls.verify_frozen_baseline.
Only an explicit suite/case pair reaches this contract. It does not run Goose,
a model, the builder, or freeze_baseline.py, and never writes evidence.
"""
from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import unicodedata

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SUITE_SCHEMA = "utcs_ta_wording_calibration_v1"
BATCH_ID = "ta-wording-20260914"
SUITE_RELATIVE_PATH = "calibration/ta_wording_20260914/suite.json"
INSTRUMENT_PARENT_COMMIT = "28fcdfce4eb06c6ec03320f312bfe37e2988bb6d"
CASE_IDS = tuple(f"C{i:02}" for i in range(1, 11))
CALIBRATION_FAILURE_POLICY = (
    "Each of the ten preregistered wording cases is executed once. "
    "A complete, envelope-valid case with zero natural tool calls or a byte-incorrect final answer "
    "is a calibration observation and permits only the next preregistered case. "
    "Any capture, execution, source/config, unexpected-tool, function, or envelope failure "
    "stops the batch without retry. Formal T-A v2 retains the original stop-on-failure rule."
)
ANCHOR_SHA256 = {
    "baseline/T-A.prompt.txt": "af86281596b7e9c7f6030811a3f0d9972939917f586ea73e822a7b548a389016",
    "baseline/T-A.input.md": "3a4e0f8725b95d48c53b8a1304b5ca475f1c5cc353b702cade0d4b21819a7029",
    "baseline/T-A.expected.md": "56cb968204a24faec245a73cd0b1db9e116ef7bac96ba44da7da2c50dd9e8707",
    "baseline/original-freeze-record.json": "e156669d70efb8bd57de2cbdcc13e9b8cd31121d2b26f2e08d0555eae09ca7ab",
}
SUFFIX_SHA256 = "39d57299e58a25d9e1a8bf3df3da69355c61221c43e938997b02837ab91ffe11"
CASE_FILES = ("prompt.txt", "input.md", "expected.md", "record.json")


class CalibrationContractError(RuntimeError):
    def __init__(self, code, detail=""):
        self.code = code
        super().__init__(code + (": " + str(detail) if detail else ""))


def require(condition, code, detail=""):
    if not condition:
        raise CalibrationContractError(code, detail)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def calibration_record(case_id):
    require(case_id in CASE_IDS, "unknown_calibration_case", case_id)
    return {"schema": SUITE_SCHEMA, "batch_id": BATCH_ID, "case_id": case_id,
            "suite_path": SUITE_RELATIVE_PATH, "runs_per_case": 1, "run": 0}


def strict_object(raw, label):
    def pairs(items):
        obj = {}
        for key, value in items:
            require(key not in obj, "duplicate_json_key", f"{label}: {key}")
            obj[key] = value
        return obj
    def bad_number(value):
        raise CalibrationContractError("nonfinite_json", f"{label}: {value}")
    try:
        result = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=bad_number)
    except (ValueError, UnicodeError) as error:
        raise CalibrationContractError("invalid_json", f"{label}: {error}") from error
    require(isinstance(result, dict), "json_object_required", label)
    return result


def absolute_path(value, label):
    require(isinstance(value, str) and value and "\x00" not in value, "absolute_path_required", label)
    path = Path(value)
    require(path.is_absolute() and ".." not in path.parts and path.as_posix() == value,
            "canonical_absolute_path_required", f"{label}: {value}")
    return path


def read_regular(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), "regular_file_required", path)
    require(path.resolve(strict=True) == path.absolute(), "symlink_path_refused", path)
    return path.read_bytes()


def check_utc(value):
    require(isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)", value),
            "suite_freeze_time_not_iso_utc", value)
    try:
        parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise CalibrationContractError("suite_freeze_time_invalid", value) from error
    require(parsed.utcoffset() == datetime.timedelta(0), "suite_freeze_time_not_utc", value)


def check_committed(source_dir, manifest):
    def git(*args, root=None):
        proc = subprocess.run(["git", "-C", str(source_dir if root is None else root), *args],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        require(proc.returncode == 0, "calibration_git_check_failed",
                {"argv": list(args), "stdout": proc.stdout.decode(errors="replace"),
                 "stderr": proc.stderr.decode(errors="replace"), "exit_code": proc.returncode})
        return proc.stdout
    root = Path(git("rev-parse", "--show-toplevel").decode().strip()).resolve(strict=True)
    relative = source_dir.relative_to(root).as_posix()
    status = git("status", "--porcelain=v1", "--untracked-files=all", "--", relative, root=root)
    require(status == b"", "calibration_sources_not_committed_clean", status.decode(errors="replace"))
    tracked = [(Path(relative) / row["relative_path"]).as_posix() for row in manifest["sources"]]
    tracked.append((Path(relative) / "SHA256SUMS").as_posix())
    git("ls-files", "--error-unmatch", "--", *tracked, root=root)


def prompt_metadata(raw, relative):
    text = raw.decode("utf-8", errors="strict")
    return {"path": relative, "sha256": digest(raw), "bytes": len(raw),
            "unicode_codepoints": len(text)}


def _verify_calibration_baseline(freeze_dir, calibration_suite, calibration_case, *,
                                 source_dir=HERE, require_committed=True):
    """Internal test seam; public entry points always require committed sources."""
    from prepare_controls import verify_source_manifest
    from score_baseline import BASE_NAMES, leakage_check

    source_dir = Path(source_dir).resolve(strict=True)
    suite_path = Path(calibration_suite).absolute()
    require(suite_path == source_dir / SUITE_RELATIVE_PATH, "calibration_suite_location", suite_path)
    require(calibration_case in CASE_IDS, "unknown_calibration_case", calibration_case)
    suite_raw = read_regular(suite_path)
    suite = strict_object(suite_raw, suite_path)
    require(suite.get("schema") == SUITE_SCHEMA and suite.get("batch_id") == BATCH_ID,
            "calibration_suite_identity")
    require(type(suite.get("run")) is int and suite["run"] == 0, "calibration_run_not_zero")
    require(suite.get("instrument_parent_commit") == INSTRUMENT_PARENT_COMMIT, "instrument_parent_commit_changed")
    check_utc(suite.get("frozen_at_utc"))
    runtime_batch = absolute_path(suite.get("runtime_batch_directory"), "runtime_batch_directory")
    cases = suite.get("cases")
    require(isinstance(cases, list) and len(cases) == 10, "calibration_requires_ten_cases")
    require(all(isinstance(row, dict) for row in cases), "calibration_case_not_object")
    require(tuple(row.get("id") for row in cases) == CASE_IDS, "calibration_case_order_or_identity")
    case_root = suite_path.parent / "cases"
    require(case_root.is_dir() and {p.name for p in case_root.iterdir()} == set(CASE_IDS),
            "calibration_case_directory_inventory")

    required = set(ANCHOR_SHA256) | {SUITE_RELATIVE_PATH}
    for case_id in CASE_IDS:
        required.update((Path(SUITE_RELATIVE_PATH).parent / "cases" / case_id / name).as_posix()
                        for name in CASE_FILES)
    manifest = verify_source_manifest(source_dir / "SHA256SUMS", source_dir)
    manifest_names = {row["relative_path"] for row in manifest["sources"]}
    require(required <= manifest_names, "calibration_files_missing_from_manifest", sorted(required - manifest_names))
    if require_committed:
        check_committed(source_dir, manifest)

    anchors = {name: read_regular(source_dir / name) for name in ANCHOR_SHA256}
    for name, raw in anchors.items():
        require(digest(raw) == ANCHOR_SHA256[name], "immutable_baseline_anchor_changed", name)
    original = strict_object(anchors["baseline/original-freeze-record.json"], "original freeze record")
    original_prompt = anchors["baseline/T-A.prompt.txt"]
    fixture = anchors["baseline/T-A.input.md"]
    expected = anchors["baseline/T-A.expected.md"]
    # The approved lead includes its separator: Chinese comma or English LF.
    # The immutable suffix starts with "只改格式..." after the original comma.
    suffix = original_prompt.split("，".encode("utf-8"), 1)[1]
    require(digest(suffix) == SUFFIX_SHA256, "immutable_prompt_suffix_changed")
    if "unchanged_suffix" in suite:
        require(canonical(suite["unchanged_suffix"]) == canonical({
            "sha256": digest(suffix), "bytes": len(suffix), "unicode_codepoints": len(suffix.decode("utf-8"))
        }), "suite_suffix_metadata_mismatch")
    for key, want in (("source_baseline_record_sha256", ANCHOR_SHA256["baseline/original-freeze-record.json"]),
                      ("original_v1_prompt_sha256", ANCHOR_SHA256["baseline/T-A.prompt.txt"])):
        if key in suite:
            require(suite[key] == want, "suite_anchor_metadata_mismatch", key)
    names = list(BASE_NAMES) + original["zero_name_leakage"]["named_variants"]
    selected = None
    prompt_hashes = set()
    allowed_case_keys = {"id", "directory", "prompt", "freeze_record", "style", "lead",
                         "zero_name_leakage", "semantic_review"}
    for row in cases:
        case_id = row["id"]
        relative = f"cases/{case_id}"
        require(set(row) <= allowed_case_keys and {"id", "directory", "prompt", "freeze_record"} <= row.keys(),
                "calibration_case_fields", case_id)
        require(row["directory"] == relative, "calibration_case_directory", case_id)
        case_dir = suite_path.parent / relative
        require(case_dir.is_dir() and not case_dir.is_symlink(), "calibration_case_directory_invalid", case_id)
        require({p.name for p in case_dir.iterdir()} == set(CASE_FILES), "calibration_case_file_inventory", case_id)
        raw_files = {name: read_regular(case_dir / name) for name in CASE_FILES}
        prompt = raw_files["prompt.txt"]
        try:
            text = prompt.decode("utf-8", errors="strict")
        except UnicodeError as error:
            raise CalibrationContractError("calibration_prompt_not_utf8", case_id) from error
        require(prompt.endswith(suffix) and len(prompt) > len(suffix), "calibration_suffix_changed", case_id)
        lead = prompt[:-len(suffix)]
        require(prompt != original_prompt, "calibration_repeats_original_prompt", case_id)
        require(unicodedata.normalize("NFC", text) == text
                and not any(0xe0000 <= ord(c) <= 0xe007f for c in text),
                "calibration_prompt_unicode_invariant", case_id)
        metadata = prompt_metadata(prompt, f"{relative}/prompt.txt")
        require(canonical(row["prompt"]) == canonical(metadata), "calibration_prompt_metadata", case_id)
        require(metadata["sha256"] not in prompt_hashes, "duplicate_calibration_prompt", case_id)
        prompt_hashes.add(metadata["sha256"])
        for key in ("style", "semantic_review"):
            if key in row:
                require(isinstance(row[key], str) and bool(row[key]), "calibration_case_metadata_type", f"{case_id}.{key}")
        if "lead" in row:
            require(isinstance(row["lead"], str) and row["lead"].encode("utf-8") == lead, "calibration_lead_metadata", case_id)
        require(raw_files["input.md"] == fixture, "calibration_input_changed", case_id)
        require(raw_files["expected.md"] == expected, "calibration_expected_changed", case_id)
        leakage = leakage_check({"prompt": text, "fixture": fixture.decode("utf-8")}, names)
        require(leakage["passed"], "calibration_tool_name_leakage", {"case": case_id, **leakage})
        if "zero_name_leakage" in row:
            require(canonical(row["zero_name_leakage"]) == canonical(leakage), "calibration_leakage_metadata", case_id)
        record_raw = raw_files["record.json"]
        require(canonical(row["freeze_record"]) == canonical({
            "path": f"{relative}/record.json", "sha256": digest(record_raw)
        }), "calibration_record_metadata", case_id)
        record = strict_object(record_raw, f"{case_id}/record.json")
        runtime_freeze = runtime_batch / "cases" / case_id / "freeze"
        wanted = copy.deepcopy(original)
        wanted["frozen_at_utc"] = suite["frozen_at_utc"]
        for key, name, raw in (("prompt", "prompt.txt", prompt), ("fixture", "input.md", fixture),
                               ("expected", "expected.md", expected)):
            wanted[key] = {"path": str(runtime_freeze / name), "bytes": len(raw), "sha256": digest(raw)}
        wanted["grant_capture"]["grant_event_file"] = str(runtime_freeze.parent / "grant_event.json")
        wanted["calibration"] = calibration_record(case_id)
        wanted["scoring"]["failure_policy"] = CALIBRATION_FAILURE_POLICY
        # Canonical JSON comparison retains scalar types (False must not equal 0).
        require(canonical(record) == canonical(wanted), "calibration_record_scope_or_mapping_changed", case_id)
        if case_id == calibration_case:
            selected = (record, raw_files, runtime_freeze)
    require(selected is not None, "unknown_calibration_case", calibration_case)
    frozen, source_files, runtime_freeze = selected
    requested = absolute_path(str(freeze_dir), "freeze_dir")
    require(requested == runtime_freeze and requested.resolve(strict=True) == requested,
            "calibration_runtime_freeze_path", requested)
    require({p.name for p in requested.iterdir()} == set(CASE_FILES), "calibration_runtime_file_inventory")
    for name, raw in source_files.items():
        require(read_regular(requested / name) == raw, "calibration_runtime_bytes_changed", name)
    return frozen


def verify_calibration_baseline(freeze_dir, calibration_suite, calibration_case):
    return _verify_calibration_baseline(freeze_dir, calibration_suite, calibration_case,
                                         source_dir=HERE, require_committed=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze-dir", required=True)
    parser.add_argument("--calibration-suite", required=True)
    parser.add_argument("--calibration-case", required=True)
    args = parser.parse_args(argv)
    frozen = verify_calibration_baseline(args.freeze_dir, args.calibration_suite, args.calibration_case)
    print(json.dumps({"run": 0, "passed": True, "calibration": frozen["calibration"],
                      "prompt": frozen["prompt"], "freeze_dir": str(args.freeze_dir)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
