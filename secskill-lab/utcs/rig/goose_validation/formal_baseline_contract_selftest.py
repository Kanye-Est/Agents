#!/usr/bin/env python3
"""Offline formal-contract checks; synthetic paths, no VM, sockets or controllers.

Report replay uses preserved real C04 score/capture/envelope bytes and the saved
zero-call score/envelope. The zero-call capture is explicitly synthetic. No
test fixture is a new study observation or a formal baseline.
"""
from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

with patch("subprocess.run", side_effect=AssertionError("import launched a command")), \
     patch("subprocess.Popen", side_effect=AssertionError("import launched a process")):
    import formal_baseline_contract as formal
    import prepare_controls as prepare
    import launch_baseline as launch
    from calibration_observations import observe

HERE = Path(__file__).resolve().parent


def raw_json(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw_json(value))


class FormalFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="utcs-formal-contract-offline-")
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.stage = self.root / "formal-stage"
        self.runtime = self.root / "runtime"
        self.batch = self.root / "calibration-batch"
        self.source.mkdir()
        self.stage.mkdir()
        self.batch.mkdir()
        self.no_network = patch("socket.create_connection", side_effect=AssertionError("No network"))
        self.no_commands = patch("subprocess.run", side_effect=AssertionError("No external commands"))
        self.no_processes = patch("subprocess.Popen", side_effect=AssertionError("No processes"))
        self.network = self.no_network.start()
        self.commands = self.no_commands.start()
        self.processes = self.no_processes.start()
        for relative in formal.ANCHOR_SHA256:
            target = self.source / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((HERE / relative).read_bytes())
        suite_dir = Path(formal.SUITE_RELATIVE_PATH).parent
        for relative in [formal.SUITE_RELATIVE_PATH] + [
            str(suite_dir / "cases" / cid / filename) for cid in formal.CASE_IDS for filename in formal.CASE_FILES
        ]:
            target = self.source / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((HERE / relative).read_bytes())
        (self.source / "synthetic_helper.py").write_text("# synthetic source inventory\n")
        self.original = json.loads((self.source / "baseline/original-freeze-record.json").read_bytes())
        self.summary = json.loads((HERE / formal.SUMMARY_RELATIVE_PATH).read_bytes())
        self.selection = json.loads((HERE / formal.SELECTION_RELATIVE_PATH).read_bytes())
        self.selection["runtime_stage"] = str(self.stage)
        self.selection["runtime_root"] = str(self.runtime)
        self.formal_dir = self.source / formal.FORMAL_DIRECTORY
        self.formal_dir.mkdir()
        for filename in ("prompt.txt", "input.md", "expected.md"):
            (self.formal_dir / filename).write_bytes((HERE / formal.FORMAL_DIRECTORY / filename).read_bytes())
        positive_dir = HERE / "validation/calibration-observer-c04-repair-20260914/inputs"
        positive = {name: json.loads((positive_dir / filename).read_bytes()) for name, filename in
                    (("score", "baseline-score.json"), ("capture", "capture_manifest.json"), ("envelope", "envelope-audit.json"))}
        negative_dir = HERE / "validation/calibration-instrument-replay-20260914"
        negative = {
            "score": json.loads((negative_dir / "original-capture-calibration-observation.json").read_bytes())["original_score"],
            "envelope": json.loads((negative_dir / "original-envelope-audit.json").read_bytes()),
            "capture": copy.deepcopy(positive["capture"]),
        }
        # This is a synthetic capture report, not an attestation about a real new capture.
        negative["capture"].update(model_call_count=1, native_request_log_count=1, generated_tool_call_count=0)
        for row in self.summary["cases"]:
            cid = row["case_id"]
            values = positive if cid in ("C04", "C06", "C08") else negative
            case = self.batch / "cases" / cid
            case.mkdir(parents=True)
            observation_path = (self.batch / formal.REPAIR_DIRECTORY / "C04-calibration-observation.json"
                                if cid == "C04" else case / "calibration-observation.json")
            evidence = {}
            def store(name, value, path=None):
                path = case / name if path is None else path
                write_json(path, value)
                evidence[name] = {"path": str(path), "sha256": formal.digest(path.read_bytes())}
            store("case-attempt.json", {"case_id": cid, "run": 0, "single_attempt": True,
                  "source_commit": row["source_commit"], "suite_sha256": formal.SUITE_SHA256})
            store("baseline-score.json", values["score"])
            store("trajectory/capture_manifest.json", values["capture"])
            store("envelope-audit.json", values["envelope"])
            for name in ("http.json", "goose-session.json", "grant_event.json"):
                store(name, {"synthetic_report": name, "case_id": cid})
            replay = observe(values["score"], values["capture"], values["envelope"])
            replay["sources"] = {}
            for label, filename in (("score", "baseline-score.json"),
                                    ("capture_manifest", "trajectory/capture_manifest.json"), ("envelope", "envelope-audit.json")):
                replay["sources"][label] = {**evidence[filename], "bytes": (case / filename).stat().st_size}
            store("observation", replay, observation_path)
            review = {"case_id": cid, "allow_next_preregistered_case": True,
                      "observation_sha256": evidence["observation"]["sha256"],
                      "envelope_sha256": evidence["envelope-audit.json"]["sha256"]}
            if cid == "C04":
                review["observation_path"] = str(observation_path)
            store("bounded-review.json", review)
            store("request-invariants.json", {
                "passed": True, "first_request_only_user_wording_differs": True,
                "all_requests_system_schema_settings_unchanged": True,
                "actual_wire_sha256": evidence["http.json"]["sha256"], "prompt_sha256": row["prompt_sha256"],
            })
            row["source_evidence"] = evidence
            for row_key, observation_key in (("natural_tool_use", "tool_natural"),
                    ("actual_tool_call_count", "actual_tool_call_count"), ("task_completed", "task_completed"),
                    ("outer_fenced", "outer_fenced"), ("tool_used_and_outer_fenced", "tool_used_and_outer_fenced")):
                row[row_key] = replay[observation_key]
            row["benign_function_preserved_raw"] = replay["actual_tool_call_count"] > 0
            for key in ("all_actual_args_text_equal_fixture", "all_tool_returns_equal_frozen_expected"):
                row[key] = replay["actual_input_fidelity"][key]
            row["capture_complete"] = True
            row["model_call_count"] = values["capture"]["model_call_count"]
            row["normalized_T_sha256"] = values["capture"]["normalized_T_sha256"]
            row["bounded_review_items"] = len(replay["bounded_review_items"])
        for key, path in {
            "historical_original_STOP_sha256": self.batch / "STOP.json",
            "resolved_manifest_STOP_sha256": self.batch / formal.REPAIR_DIRECTORY / "STOP.source-manifest-resolved-a78.json",
            "resume_record_sha256": self.batch / formal.REPAIR_DIRECTORY / "resume-init.json",
            "original_C04_error_observation_sha256": self.batch / "cases/C04/calibration-observation.json",
        }.items():
            write_json(path, {"synthetic_historical_evidence": key})
            self.summary[key] = formal.digest(path.read_bytes())
        rows = self.summary["cases"]
        counts = {
            "natural_tool_use": sum(r["natural_tool_use"] for r in rows),
            "task_completed": sum(r["task_completed"] for r in rows),
            "tool_used_and_outer_fenced": sum(r["tool_used_and_outer_fenced"] for r in rows),
            "outer_fenced_all": sum(r["outer_fenced"] for r in rows),
            "actual_tool_calls": sum(r["actual_tool_call_count"] for r in rows),
            "model_requests": sum(r["model_call_count"] for r in rows),
        }
        self.summary["counts"] = counts
        self.summary["ratios"] = {
            "natural_tool_use": {"numerator": counts["natural_tool_use"], "denominator": 10},
            "task_completed": {"numerator": counts["task_completed"], "denominator": 10},
            "tool_use_and_fence_joint": {"numerator": counts["tool_used_and_outer_fenced"], "denominator": 10},
            "fence_given_tool_use": {"numerator": counts["tool_used_and_outer_fenced"], "denominator": counts["natural_tool_use"]},
        }
        self.refresh()

    def tearDown(self):
        try:
            self.network.assert_not_called()
            self.commands.assert_not_called()
            self.processes.assert_not_called()
        finally:
            self.no_network.stop()
            self.no_commands.stop()
            self.no_processes.stop()
            self.temp.cleanup()

    def manifest(self):
        # Only this freshly created synthetic source tree is enumerated.
        paths = sorted(p for p in self.source.rglob("*") if p.is_file() and p.name != "SHA256SUMS")
        (self.source / "SHA256SUMS").write_text("".join(
            formal.digest(p.read_bytes()) + "  " + p.relative_to(self.source).as_posix() + "\n" for p in paths))

    def refresh(self):
        write_json(self.formal_dir / "calibration-summary.json", self.summary)
        self.summary_hash = formal.digest((self.formal_dir / "calibration-summary.json").read_bytes())
        self.selection["summary"]["sha256"] = self.summary_hash
        write_json(self.formal_dir / "selection.json", self.selection)
        self.record = formal.build_formal_record(
            self.original, self.selection, formal.digest((self.formal_dir / "selection.json").read_bytes()))
        write_json(self.formal_dir / "record.json", self.record)
        self.refresh_runtime()
        self.manifest()

    def refresh_runtime(self):
        (self.stage / "freeze").mkdir(exist_ok=True)
        for filename in formal.CASE_FILES:
            (self.stage / "freeze" / filename).write_bytes((self.formal_dir / filename).read_bytes())

    def verify(self):
        return formal._verify_formal_v2_baseline(
            self.stage / "freeze", self.formal_dir / "record.json", source_dir=self.source,
            runtime_stage=self.stage, runtime_root=self.runtime, calibration_batch=self.batch,
            summary_sha256=self.summary_hash, require_committed=False,
        )

    def test_real_report_replay_and_exact_formal_freeze_pass(self):
        result = self.verify()
        self.assertEqual(result, self.record)
        self.assertEqual(result["scoring"], self.original["scoring"])
        self.assertNotIn("calibration", result)
        self.assertEqual(result["formal_v2"]["selected_case_id"], "C04")
        self.assertEqual(result["formal_v2"]["max_attempts"], 1)

    def test_false_task_scores_and_fences_do_not_disqualify_natural_candidate(self):
        self.assertTrue(all(not row["task_completed"] for row in self.summary["cases"]))
        self.assertTrue(self.summary["cases"][3]["outer_fenced"])
        self.assertEqual(self.verify()["formal_v2"]["selected_case_id"], "C04")

    def test_public_verifier_has_no_bypass_arguments_and_forces_all_checks(self):
        with patch.object(formal, "_verify_formal_v2_baseline", return_value="verified") as seam:
            self.assertEqual(formal.verify_formal_v2_baseline("/freeze", "/record"), "verified")
        kwargs = seam.call_args.kwargs
        self.assertIs(kwargs["require_committed"], True)
        self.assertEqual(kwargs["summary_sha256"], formal.SUMMARY_SHA256)
        self.assertEqual(kwargs["runtime_stage"], formal.FORMAL_STAGE)
        self.assertEqual(kwargs["calibration_batch"], formal.CALIBRATION_BATCH)
        self.assertIs(kwargs["evidence_reader"], formal.read_regular)
        with self.assertRaises(TypeError):
            formal.verify_formal_v2_baseline("/freeze", "/record", require_committed=False)

    def test_constructor_is_pure_and_preserves_original(self):
        before = copy.deepcopy(self.original)
        with patch.object(Path, "read_bytes", side_effect=AssertionError("constructor read a file")):
            result = formal.build_formal_record(self.original, self.selection, "a" * 64)
        self.assertEqual(self.original, before)
        self.assertEqual(result["rig_build_head"], before["rig_build_head"])
        self.assertEqual(result["zero_name_leakage"], before["zero_name_leakage"])
        self.assertEqual(result["scoring"], before["scoring"])

    def test_incomplete_calibration_is_rejected(self):
        self.summary["cases"].pop()
        self.refresh()
        with self.assertRaisesRegex(RuntimeError, "ten_case_order"):
            self.verify()

    def test_duplicate_case_is_rejected(self):
        self.summary["cases"][1]["case_id"] = "C01"
        self.refresh()
        with self.assertRaisesRegex(RuntimeError, "ten_case_order"):
            self.verify()

    def test_boolean_cannot_substitute_for_zero_integer(self):
        self.summary["cases"][0]["actual_tool_call_count"] = False
        self.refresh()
        with self.assertRaisesRegex(RuntimeError, "integer_required"):
            self.verify()

    def test_zero_cannot_substitute_for_boolean(self):
        self.summary["cases"][0]["natural_tool_use"] = 0
        self.refresh()
        with self.assertRaisesRegex(RuntimeError, "boolean_required"):
            self.verify()

    def test_task_completion_selection_filter_is_rejected(self):
        self.selection["rule"]["task_completed_filter"] = True
        self.refresh()
        with self.assertRaisesRegex(RuntimeError, "selection_rule"):
            self.verify()

    def test_longer_natural_candidate_is_rejected(self):
        self.selection["selected_case_id"] = "C08"
        self.refresh()
        with self.assertRaisesRegex(RuntimeError, "wrong_shortest_selection"):
            self.verify()

    def test_unknown_selection_metadata_is_rejected(self):
        self.selection["allow_retry"] = True
        self.refresh()
        with self.assertRaisesRegex(RuntimeError, "object_keys"):
            self.verify()

    def test_summary_count_cannot_be_claimed_without_corresponding_rows(self):
        self.summary["counts"]["natural_tool_use"] = 4
        self.refresh()
        with self.assertRaisesRegex(RuntimeError, "calibration_counts"):
            self.verify()

    def test_wrong_report_path_is_rejected_before_read(self):
        self.summary["cases"][0]["source_evidence"]["http.json"]["path"] = str(self.root / "outside.json")
        self.refresh()
        with self.assertRaisesRegex(RuntimeError, "evidence_path"):
            self.verify()

    def test_changed_real_evidence_bytes_are_rejected(self):
        path = Path(self.summary["cases"][3]["source_evidence"]["baseline-score.json"]["path"])
        path.write_bytes(path.read_bytes() + b" ")
        with self.assertRaisesRegex(RuntimeError, "evidence_hash"):
            self.verify()

    def test_forged_observation_is_rejected_even_with_updated_reference_hash(self):
        ref = self.summary["cases"][0]["source_evidence"]["observation"]
        path = Path(ref["path"])
        observation = json.loads(path.read_bytes())
        observation["tool_natural"] = True
        write_json(path, observation)
        ref["sha256"] = formal.digest(path.read_bytes())
        self.refresh()
        with self.assertRaisesRegex(RuntimeError, "observation_replay_mismatch"):
            self.verify()

    def test_c04_review_must_bind_corrected_observation_path(self):
        ref = self.summary["cases"][3]["source_evidence"]["bounded-review.json"]
        path = Path(ref["path"])
        review = json.loads(path.read_bytes())
        review["observation_path"] = str(self.batch / "cases/C04/calibration-observation.json")
        write_json(path, review)
        ref["sha256"] = formal.digest(path.read_bytes())
        self.refresh()
        with self.assertRaisesRegex(RuntimeError, "c04_repair_review_path"):
            self.verify()

    def test_final_case_still_requires_its_bound_review(self):
        ref = self.summary["cases"][-1]["source_evidence"]["bounded-review.json"]
        path = Path(ref["path"])
        review = json.loads(path.read_bytes())
        review["allow_next_preregistered_case"] = False
        write_json(path, review)
        ref["sha256"] = formal.digest(path.read_bytes())
        self.refresh()
        with self.assertRaisesRegex(RuntimeError, "bounded_review_binding"):
            self.verify()

    def test_original_stop_bytes_are_preserved(self):
        (self.batch / "STOP.json").write_bytes(b"changed historical STOP")
        with self.assertRaisesRegex(RuntimeError, "history_hash"):
            self.verify()

    def test_new_calibration_repair_stop_blocks_formal(self):
        write_json(self.batch / formal.REPAIR_DIRECTORY / "STOP.json", {"status": "new STOP"})
        with self.assertRaisesRegex(RuntimeError, "repair_still_stopped"):
            self.verify()

    def test_formal_record_cannot_inherit_calibration_failure_policy(self):
        record = copy.deepcopy(self.record)
        record["scoring"]["failure_policy"] = "Continue after failed task scores."
        write_json(self.formal_dir / "record.json", record)
        self.refresh_runtime()
        self.manifest()
        with self.assertRaisesRegex(RuntimeError, "record_changed_beyond"):
            self.verify()

    def test_formal_record_rejects_calibration_tag(self):
        record = copy.deepcopy(self.record)
        record["calibration"] = {"case_id": "C04"}
        write_json(self.formal_dir / "record.json", record)
        self.refresh_runtime()
        self.manifest()
        with self.assertRaisesRegex(RuntimeError, "record_changed_beyond"):
            self.verify()

    def test_runtime_bytes_cannot_be_changed(self):
        path = self.stage / "freeze/prompt.txt"
        path.write_bytes(path.read_bytes() + b"\n")
        with self.assertRaisesRegex(RuntimeError, "runtime_freeze_bytes"):
            self.verify()

    def test_different_stage_cannot_create_another_formal_baseline(self):
        other = self.root / "another-freeze"
        shutil.copytree(self.stage / "freeze", other)
        with self.assertRaisesRegex(RuntimeError, "runtime_freeze_path"):
            formal._verify_formal_v2_baseline(
                other, self.formal_dir / "record.json", source_dir=self.source, runtime_stage=self.stage,
                runtime_root=self.runtime, calibration_batch=self.batch,
                summary_sha256=self.summary_hash, require_committed=False)

    def test_changed_expected_bytes_are_not_authorized(self):
        path = self.formal_dir / "expected.md"
        path.write_bytes(path.read_bytes() + b"\n")
        self.refresh_runtime()
        self.manifest()
        with self.assertRaisesRegex(RuntimeError, "input_or_expected_changed"):
            self.verify()

    def test_manifest_must_cover_new_helper_code(self):
        (self.source / "unlisted.py").write_text("# unlisted\n")
        with self.assertRaisesRegex(RuntimeError, "omits helper code"):
            self.verify()

    def test_original_default_lock_still_rejects_formal_record(self):
        with patch.object(prepare, "HERE", self.source):
            with self.assertRaisesRegex(RuntimeError, "Original baseline freeze record changed"):
                prepare.verify_frozen_baseline(self.stage / "freeze")

    def test_runtime_controller_arguments_use_exact_profile_workspace_and_config(self):
        (self.runtime / "profile/config").mkdir(parents=True)
        (self.runtime / "workspace").mkdir()
        (self.runtime / "service.env").write_text("synthetic environment\n")
        (self.runtime / "profile/config/config.yaml").write_text("synthetic disabled config\n")
        args = (self.stage, self.runtime / "workspace", self.runtime / "service.env",
                self.runtime / "profile/config/config.yaml")
        formal._verify_formal_v2_runtime_paths(
            *args, self.runtime / "profile", runtime_stage=self.stage, runtime_root=self.runtime)
        other = self.runtime / "other-workspace"
        other.mkdir()
        with self.assertRaisesRegex(RuntimeError, "runtime_argument_path"):
            formal._verify_formal_v2_runtime_paths(
                self.stage, other, *args[2:], runtime_stage=self.stage, runtime_root=self.runtime)


class FormalDispatchTests(unittest.TestCase):
    def test_explicit_formal_dispatch(self):
        with patch.object(formal, "verify_formal_v2_baseline", return_value={"formal_v2": {}}) as call:
            result = prepare.verify_frozen_baseline("/freeze", formal_v2_record="/record")
        call.assert_called_once_with("/freeze", "/record")
        self.assertIn("formal_v2", result)

    def test_mixed_modes_never_invoke_either_verifier(self):
        with patch.object(formal, "verify_formal_v2_baseline") as formal_call, \
             patch("calibration_contract.verify_calibration_baseline") as calibration_call:
            with self.assertRaisesRegex(RuntimeError, "cannot be combined"):
                prepare.verify_frozen_baseline("/freeze", "/suite", "C04", "/record")
        formal_call.assert_not_called()
        calibration_call.assert_not_called()

    def test_original_calibration_dispatch_is_unchanged(self):
        with patch("calibration_contract.verify_calibration_baseline", return_value={"calibration": {}}) as call:
            result = prepare.verify_frozen_baseline("/freeze", "/suite", "C04")
        call.assert_called_once_with("/freeze", "/suite", "C04")
        self.assertIn("calibration", result)

    def test_prepare_cli_rejects_mixed_modes_before_controller_construction(self):
        names = ("stage", "workspace", "service-env", "goose-bin", "config", "freeze-dir",
                 "unit", "chain4", "chain6", "osv-ready", "osv-unit")
        argv = [item for name in names for item in ("--" + name, "/synthetic")]
        argv += ["--osv-pid", "1", "--calibration-suite", "/suite", "--calibration-case", "C04",
                 "--formal-v2-record", "/record"]
        with patch.object(prepare, "PrepareController") as controller, contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as failure:
                prepare.main(argv)
        self.assertEqual(failure.exception.code, 2)
        controller.assert_not_called()

    def test_launch_cli_rejects_mixed_modes_before_controller_construction(self):
        names = ("stage", "profile", "workspace", "service-env", "goose-bin", "config", "repo", "freeze-dir", "config-record")
        argv = [item for name in names for item in ("--" + name, "/synthetic")]
        argv += ["--calibration-suite", "/suite", "--calibration-case", "C04", "--formal-v2-record", "/record"]
        with patch.object(launch, "LaunchController") as controller, contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as failure:
                launch.main(argv)
        self.assertEqual(failure.exception.code, 2)
        controller.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
