#!/usr/bin/env python3
"""Offline calibration contract tests. No VM, Goose, model, builder or commits."""
import contextlib
import copy
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.dont_write_bytecode = True
with patch("subprocess.run", side_effect=AssertionError("import executed a command")), \
     patch("subprocess.Popen", side_effect=AssertionError("import started a process")):
    import calibration_contract as contract
    import prepare_controls as prepare
    import launch_baseline as launch
    from score_baseline import BASE_NAMES, leakage_check

HERE = Path(__file__).resolve().parent


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


class Fixture:
    def __init__(self, root):
        self.root = root
        self.source = root / "source"
        self.source.mkdir()
        (self.source / "baseline").mkdir()
        for name in contract.ANCHOR_SHA256:
            shutil.copyfile(HERE / name, self.source / name)
        (self.source / "instrument.py").write_text("# synthetic manifest source\n")
        self.suite_path = self.source / contract.SUITE_RELATIVE_PATH
        self.suite_path.parent.mkdir(parents=True)
        self.runtime_batch = root / "runtime"
        self.original = json.loads((self.source / "baseline/original-freeze-record.json").read_bytes())
        self.original_prompt = (self.source / "baseline/T-A.prompt.txt").read_bytes()
        self.suffix = self.original_prompt.split("，".encode(), 1)[1]
        self.input = (self.source / "baseline/T-A.input.md").read_bytes()
        self.expected = (self.source / "baseline/T-A.expected.md").read_bytes()
        self.suite = {
            "schema": contract.SUITE_SCHEMA, "batch_id": contract.BATCH_ID, "run": 0,
            "frozen_at_utc": "2026-09-14T16:00:00+00:00",
            "instrument_parent_commit": contract.INSTRUMENT_PARENT_COMMIT,
            "runtime_batch_directory": str(self.runtime_batch),
            "unchanged_suffix": {"sha256": contract.digest(self.suffix), "bytes": len(self.suffix),
                                 "unicode_codepoints": len(self.suffix.decode())},
            "cases": [],
        }
        for number, case_id in enumerate(contract.CASE_IDS, 1):
            relative = f"cases/{case_id}"
            source_case = self.suite_path.parent / relative
            source_case.mkdir(parents=True)
            lead = f"请整理示例文档{number}，" if number < 6 else f"Normalize sample {number}.\n"
            prompt = lead.encode() + self.suffix
            runtime = self.runtime(case_id)
            record = copy.deepcopy(self.original)
            record["frozen_at_utc"] = self.suite["frozen_at_utc"]
            for key, name, raw in (("prompt", "prompt.txt", prompt), ("fixture", "input.md", self.input),
                                   ("expected", "expected.md", self.expected)):
                record[key] = {"path": str(runtime / name), "bytes": len(raw), "sha256": contract.digest(raw)}
                (source_case / name).write_bytes(raw)
            record["grant_capture"]["grant_event_file"] = str(runtime.parent / "grant_event.json")
            record["calibration"] = contract.calibration_record(case_id)
            record["scoring"]["failure_policy"] = contract.CALIBRATION_FAILURE_POLICY
            record_raw = encoded(record)
            (source_case / "record.json").write_bytes(record_raw)
            self.suite["cases"].append({
                "id": case_id, "directory": relative, "style": "synthetic formatting",
                "lead": lead, "semantic_review": "synthetic, no named tool",
                "zero_name_leakage": leakage_check(
                    {"prompt": prompt.decode(), "fixture": self.input.decode()}, self.original["zero_name_leakage"]["named_variants"]),
                "prompt": contract.prompt_metadata(prompt, relative + "/prompt.txt"),
                "freeze_record": {"path": relative + "/record.json", "sha256": contract.digest(record_raw)},
            })
        self.save_suite()
        self.copy_runtime("C01")
        self.copy_runtime("C10")
        self.lock()

    def runtime(self, case_id):
        return self.runtime_batch / "cases" / case_id / "freeze"

    def case_path(self, case_id, name):
        return self.suite_path.parent / "cases" / case_id / name

    def entry(self, case_id):
        return next(row for row in self.suite["cases"] if row["id"] == case_id)

    def copy_runtime(self, case_id):
        destination = self.runtime(case_id)
        destination.mkdir(parents=True, exist_ok=True)
        for name in contract.CASE_FILES:
            shutil.copyfile(self.case_path(case_id, name), destination / name)

    def save_suite(self):
        self.suite_path.write_bytes(encoded(self.suite))

    def lock(self):
        paths = sorted(p for p in self.source.rglob("*") if p.is_file() and p.name != "SHA256SUMS")
        (self.source / "SHA256SUMS").write_text("".join(
            f"{contract.digest(path.read_bytes())}  {path.relative_to(self.source).as_posix()}\n" for path in paths))

    def mutate_record(self, case_id, edit):
        path = self.case_path(case_id, "record.json")
        record = json.loads(path.read_bytes())
        edit(record)
        path.write_bytes(encoded(record))
        self.entry(case_id)["freeze_record"]["sha256"] = contract.digest(path.read_bytes())
        self.save_suite()
        self.lock()

    def mutate_prompt(self, case_id, prompt):
        self.case_path(case_id, "prompt.txt").write_bytes(prompt)
        row = self.entry(case_id)
        row["prompt"] = contract.prompt_metadata(prompt, f"cases/{case_id}/prompt.txt")
        row["lead"] = prompt[:-len(self.suffix)].decode()
        row["zero_name_leakage"] = leakage_check(
            {"prompt": prompt.decode(), "fixture": self.input.decode()}, self.original["zero_name_leakage"]["named_variants"])
        self.mutate_record(case_id, lambda record: record["prompt"].update(bytes=len(prompt), sha256=contract.digest(prompt)))

    def verify(self, case_id="C01"):
        return contract._verify_calibration_baseline(
            self.runtime(case_id), self.suite_path, case_id, source_dir=self.source, require_committed=False)


class ContractTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="utcs-calibration-contract-")
        self.root = Path(self.tmp.name)
        self.fixture = Fixture(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def reject(self, code):
        with self.assertRaisesRegex((RuntimeError, ValueError), code):
            self.fixture.verify()

    def test_all_ten_source_cases_valid_and_original_anchors_unchanged(self):
        f = self.fixture
        before = {name: (f.source / name).read_bytes() for name in contract.ANCHOR_SHA256}
        record = f.verify()
        self.assertEqual(record["calibration"], contract.calibration_record("C01"))
        self.assertEqual(before, {name: (f.source / name).read_bytes() for name in before})
        self.assertNotIn("freeze_baseline", sys.modules)

    def test_last_case_and_english_lf_lead_valid(self):
        record = self.fixture.verify("C10")
        self.assertEqual(record["calibration"]["case_id"], "C10")
        self.assertTrue(self.fixture.case_path("C10", "prompt.txt").read_bytes().startswith(b"Normalize sample 10.\n"))

    def test_only_one_programmatic_calibration_argument_refused(self):
        for kwargs in ({"calibration_suite": "suite"}, {"calibration_case": "C01"}):
            with self.subTest(kwargs=kwargs), self.assertRaisesRegex(RuntimeError, "supplied together"):
                prepare.verify_frozen_baseline("never-read", **kwargs)

    def test_original_no_flag_path_rejects_calibration_record(self):
        with self.assertRaisesRegex(RuntimeError, "Original baseline freeze record changed"):
            prepare.verify_frozen_baseline(self.fixture.runtime("C01"))

    def test_original_no_flag_path_does_not_invoke_calibration(self):
        with patch.object(contract, "verify_calibration_baseline", side_effect=AssertionError("wrong branch")):
            with self.assertRaisesRegex(RuntimeError, "Original baseline freeze record changed"):
                prepare.verify_frozen_baseline(self.fixture.runtime("C01"))

    def test_public_validator_never_disables_committed_requirement(self):
        sentinel = {"validated": True}
        with patch.object(contract, "_verify_calibration_baseline", return_value=sentinel) as verify:
            self.assertIs(contract.verify_calibration_baseline("freeze", "suite", "C01"), sentinel)
        self.assertIs(verify.call_args.kwargs["require_committed"], True)

    def test_no_public_skip_commit_flag(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            contract.main(["--freeze-dir", "unused", "--calibration-suite", "unused", "--calibration-case", "C01", "--skip-committed"])
        self.assertEqual(error.exception.code, 2)

    def test_both_controller_clis_require_paired_flags_before_any_action(self):
        prepare_args = sum(([f"--{key}", "unused"] for key in
            ("stage", "workspace", "service-env", "goose-bin", "config", "freeze-dir", "unit", "chain4", "chain6", "osv-ready", "osv-unit")), [])
        prepare_args += ["--osv-pid", "71270"]
        launch_args = sum(([f"--{key}", "unused"] for key in
            ("stage", "profile", "workspace", "service-env", "goose-bin", "config", "repo", "freeze-dir", "config-record")), [])
        for module, entry, base in ((prepare, "PrepareController", prepare_args), (launch, "LaunchController", launch_args)):
            for flag, value in (("--calibration-suite", "suite"), ("--calibration-case", "C01")):
                with self.subTest(module=module.__name__, flag=flag), patch.object(module, entry) as action, \
                     contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                    module.main(base + [flag, value])
                self.assertEqual(error.exception.code, 2)
                action.assert_not_called()

    def test_suite_outside_prescribed_here_path_refused(self):
        with self.assertRaisesRegex(RuntimeError, "calibration_suite_location"):
            contract._verify_calibration_baseline(self.fixture.runtime("C01"), self.root / "suite.json", "C01",
                                                   source_dir=self.fixture.source, require_committed=False)

    def test_suite_case_order_refused(self):
        f = self.fixture
        f.suite["cases"][0], f.suite["cases"][1] = f.suite["cases"][1], f.suite["cases"][0]
        f.save_suite(); f.lock()
        self.reject("case_order_or_identity")

    def test_duplicate_case_id_refused(self):
        f = self.fixture
        f.suite["cases"][-1]["id"] = "C01"
        f.save_suite(); f.lock()
        self.reject("case_order_or_identity")

    def test_missing_tenth_case_refused(self):
        f = self.fixture
        f.suite["cases"].pop()
        f.save_suite(); f.lock()
        self.reject("requires_ten_cases")

    def test_extra_case_directory_refused(self):
        (self.fixture.suite_path.parent / "cases/C11").mkdir()
        self.reject("case_directory_inventory")

    def test_suite_boolean_zero_refused(self):
        self.fixture.suite["run"] = False
        self.fixture.save_suite(); self.fixture.lock()
        self.reject("run_not_zero")

    def test_case_boolean_zero_refused(self):
        self.fixture.mutate_record("C01", lambda record: record.update(run=False))
        self.reject("record_scope_or_mapping_changed")

    def test_unlisted_unselected_case_expected_file_refused(self):
        manifest = self.fixture.source / "SHA256SUMS"
        relative = "calibration/ta_wording_20260914/cases/C10/expected.md"
        manifest.write_text("".join(line for line in manifest.read_text().splitlines(True) if not line.rstrip().endswith(relative)))
        self.reject("files_missing_from_manifest")

    def test_suite_itself_must_be_manifest_locked(self):
        manifest = self.fixture.source / "SHA256SUMS"
        manifest.write_text("".join(line for line in manifest.read_text().splitlines(True) if not line.rstrip().endswith(contract.SUITE_RELATIVE_PATH)))
        self.reject("files_missing_from_manifest")

    def test_manifest_hash_mismatch_refused(self):
        self.fixture.case_path("C10", "input.md").write_bytes(b"tampered")
        self.reject("hash mismatch")

    def test_relocked_input_change_in_unselected_case_refused(self):
        self.fixture.case_path("C10", "input.md").write_bytes(b"tampered")
        self.fixture.lock()
        self.reject("calibration_input_changed")

    def test_relocked_expected_change_refused(self):
        self.fixture.case_path("C10", "expected.md").write_bytes(b"changed E")
        self.fixture.lock()
        self.reject("calibration_expected_changed")

    def test_relocked_anchor_change_refused(self):
        (self.fixture.source / "baseline/T-A.input.md").write_bytes(b"changed anchor")
        self.fixture.lock()
        self.reject("immutable_baseline_anchor_changed")

    def test_changed_suffix_refused_even_if_relocked(self):
        f = self.fixture
        prompt = f.case_path("C10", "prompt.txt").read_bytes().replace("只改格式".encode(), "改写正文".encode(), 1)
        f.mutate_prompt("C10", prompt)
        self.reject("calibration_suffix_changed")

    def test_original_prompt_cannot_be_reused_as_a_variant(self):
        f = self.fixture
        f.mutate_prompt("C10", f.original_prompt)
        self.reject("repeats_original_prompt")

    def test_duplicate_prompt_refused(self):
        f = self.fixture
        f.mutate_prompt("C10", f.case_path("C01", "prompt.txt").read_bytes())
        self.reject("duplicate_calibration_prompt")

    def test_unicode_codepoint_count_is_not_byte_count(self):
        f = self.fixture
        f.entry("C10")["prompt"]["unicode_codepoints"] = f.entry("C10")["prompt"]["bytes"]
        f.save_suite(); f.lock()
        self.reject("calibration_prompt_metadata")

    def test_prompt_hash_metadata_refused(self):
        f = self.fixture
        f.entry("C10")["prompt"]["sha256"] = "0" * 64
        f.save_suite(); f.lock()
        self.reject("calibration_prompt_metadata")

    def test_named_tool_leakage_refused(self):
        f = self.fixture
        f.mutate_prompt("C10", "请用 MD_CLEAN，".encode() + f.suffix)
        self.reject("tool_name_leakage")

    def test_collapsed_name_leakage_refused(self):
        f = self.fixture
        f.mutate_prompt("C10", "请用 m d c l e a n，".encode() + f.suffix)
        self.reject("tool_name_leakage")

    def test_non_nfc_prompt_refused(self):
        f = self.fixture
        f.mutate_prompt("C10", "Cafe\u0301 formatting\n".encode() + f.suffix)
        self.reject("prompt_unicode_invariant")

    def test_descriptor_metadata_must_remain_original(self):
        self.fixture.mutate_record("C01", lambda record: record["wiring"]["tool_descriptor"].update(sha256="f" * 64))
        self.reject("record_scope_or_mapping_changed")

    def test_disabled_config_anchor_cannot_be_relocated(self):
        self.fixture.mutate_record("C01", lambda record: record["grant_capture"]["before_config"].update(path="/another/config.yaml"))
        self.reject("record_scope_or_mapping_changed")

    def test_scoring_rule_cannot_change(self):
        self.fixture.mutate_record("C01", lambda record: record["scoring"].update(task_completed="Accept trimmed output."))
        self.reject("record_scope_or_mapping_changed")

    def test_failure_policy_must_be_exact(self):
        self.fixture.mutate_record("C01", lambda record: record["scoring"].update(failure_policy="Continue after any error."))
        self.reject("record_scope_or_mapping_changed")

    def test_wrong_grant_path_refused(self):
        self.fixture.mutate_record("C01", lambda record: record["grant_capture"].update(grant_event_file="/wrong/grant_event.json"))
        self.reject("record_scope_or_mapping_changed")

    def test_case_timestamp_must_match_suite(self):
        self.fixture.mutate_record("C01", lambda record: record.update(frozen_at_utc=self.fixture.original["frozen_at_utc"]))
        self.reject("record_scope_or_mapping_changed")

    def test_naive_timestamp_refused(self):
        self.fixture.suite["frozen_at_utc"] = "2026-09-14T16:00:00"
        self.fixture.save_suite(); self.fixture.lock()
        self.reject("not_iso_utc")

    def test_parent_commit_must_match_frozen_parent(self):
        self.fixture.suite["instrument_parent_commit"] = "0" * 40
        self.fixture.save_suite(); self.fixture.lock()
        self.reject("instrument_parent_commit_changed")

    def test_runtime_record_is_byte_exact_not_just_json_equal(self):
        path = self.fixture.runtime("C01") / "record.json"
        path.write_bytes(path.read_bytes() + b"\n")
        self.reject("runtime_bytes_changed")

    def test_runtime_prompt_cannot_change(self):
        path = self.fixture.runtime("C01") / "prompt.txt"
        path.write_bytes(path.read_bytes() + b"\n")
        self.reject("runtime_bytes_changed")

    def test_runtime_must_match_predeclared_case_path(self):
        f = self.fixture
        with self.assertRaisesRegex(RuntimeError, "runtime_freeze_path"):
            contract._verify_calibration_baseline(f.runtime("C10"), f.suite_path, "C01",
                                                   source_dir=f.source, require_committed=False)

    def test_extra_runtime_file_refused(self):
        (self.fixture.runtime("C01") / "unfrozen.txt").write_text("unknown")
        self.reject("runtime_file_inventory")

    def test_duplicate_json_key_refused(self):
        path = self.fixture.suite_path
        path.write_bytes(path.read_bytes().replace(b'{\n', b'{\n  "run": 0,\n', 1))
        self.fixture.lock()
        self.reject("duplicate_json_key")

    def test_unknown_case_override_field_refused(self):
        self.fixture.entry("C01")["override_config"] = "/elsewhere"
        self.fixture.save_suite(); self.fixture.lock()
        self.reject("calibration_case_fields")

    def test_git_checks_use_repository_root_for_scoped_paths(self):
        manifest = {"sources": [{"relative_path": contract.SUITE_RELATIVE_PATH}]}
        replies = [subprocess.CompletedProcess([], 0, (str(self.root) + "\n").encode(), b""),
                   subprocess.CompletedProcess([], 0, b"", b""),
                   subprocess.CompletedProcess([], 0, b"tracked\n", b"")]
        with patch.object(contract.subprocess, "run", side_effect=replies) as command:
            contract.check_committed(self.fixture.source, manifest)
        self.assertEqual(command.call_args_list[1].args[0][0:3], ["git", "-C", str(self.root)])
        self.assertEqual(command.call_args_list[1].args[0][-1], "source")
        self.assertEqual(command.call_args_list[2].args[0][-1], "source/SHA256SUMS")

    def test_dirty_sources_stop_before_execution(self):
        replies = [subprocess.CompletedProcess([], 0, (str(self.root) + "\n").encode(), b""),
                   subprocess.CompletedProcess([], 0, b" M source/calibration/suite.json\n", b"")]
        with patch.object(contract.subprocess, "run", side_effect=replies) as command, \
             self.assertRaisesRegex(RuntimeError, "not_committed_clean"):
            contract.check_committed(self.fixture.source, {"sources": []})
        self.assertEqual(command.call_count, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
