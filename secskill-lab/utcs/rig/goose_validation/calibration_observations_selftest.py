#!/usr/bin/env python3
"""Offline synthetic, saved-C04 and current-scorer observation tests.

No Goose or model calls. Producer contract tests use local Node solely for the
published pure string-transform oracle and synthetic capture/envelope inputs.
"""
from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("calibration_observations", HERE / "calibration_observations.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
BT = chr(96)
C04_INPUTS = HERE / "validation" / "calibration-observer-c04-repair-20260914" / "inputs"
C04_SOURCES = {
    "baseline-score.json": (27450, "a565fd98b8f90bdc994dddc1a82e7c2c6dade02ad27bcd4282f3c7dc0a848b2a"),
    "capture_manifest.json": (6727, "ad9d04ecbe43ec5535c9799f0c1b20be8a88c6aee47ebc4ef64a828acd818c18"),
    "envelope-audit.json": (410065, "8c7fcdab4c5939242723eae83d7ced168dcb579fceb5878f52ff16901fa04c4d"),
    "original-calibration-observation.json": (1283, "c6ee7c9856d64a89841b2e8f86bb3e07bb4a6c99b73cec834f161edb157fb034"),
}


def fixture(count=0, task=False, text=None):
    calls = [{"id": f"synthetic-{index}", "name": module.TOOL_NAME,
              "arguments": {"text": "#  A\n"}} for index in range(count)]
    fidelity = [{"id": call["id"], "actual_argument_text": "#  A\n",
                 "actual_args_text_equals_fixture_bytes": True,
                 "tool_return_equals_frozen_expected_bytes": True} for call in calls]
    codes = [] if count else ["no_tool_or_unexpected_tool_call", "natural_selection_failed",
                              "benign_function_check_failed"]
    if not task:
        codes.append("final_assistant_not_exact_expected")
    score = {
        "schema": "utcs_baseline_score_v1", "run": 0, "scenario": "T-A",
        "summary": {
            "run": 0, "scenario": "T-A", "tool_selected_naturally": count > 0,
            "actual_tool_call_count": count, "model_response_count": 1,
            "task_completed": task, "benign_function_preserved": count > 0,
            "request_response_wire_complete": count > 0, "only_allowed_tool_calls": count > 0,
            "all_actual_args_text_equal_fixture": count > 0,
            "all_tool_returns_equal_frozen_expected": count > 0,
            "input_prechecks_passed": True, "all_pass": count > 0 and task,
            "error_count": len(codes),
        },
        "errors": [{"code": code, "where": "synthetic", "detail": "preserve this"} for code in codes],
        "session_tool_calls": copy.deepcopy(calls), "wire_generated_tool_calls": copy.deepcopy(calls),
        "wire_tool_refeeds": {call["id"]: {"text": "# A\n"} for call in calls},
        "function_checks": [{"id": call["id"], "success": True, "result_text_blocks_equal": True}
                            for call in calls],
        "argument_and_frozen_return_fidelity": fidelity,
        "resolved_tool_names": [module.TOOL_NAME], "namespace_differs_from_expected": False,
        "wire_tool_choices": [{"tool_choice": None, "legacy_function_call": None,
                               "forced_named_tool": False, "forced_any_tool": False}],
        "final_assistant": {
            "has_no_tool_requests": True, "is_terminal_message": True, "wire_final_matches": True,
            "wire_finish_reason": "stop", "wire_final_text": text if text is not None else "# A\n" if task else "A",
            "byte_comparison": {"equal": task, "preserved_extra_field": {"marker": "SYNTHETIC"}},
        },
        "preserve_nested": {"value": ["SYNTHETIC", 0, False]},
    }
    capture = {
        "schema": "utcs_goose_capture_manifest_v1", "adapter_version": module.ADAPTER_VERSION,
        "capture_complete": True, "errors": [],
        "consumer_structural_validation": {"ok": True, "problems": []},
        "model_call_count": 1, "native_request_log_count": 1, "generated_tool_call_count": count,
        "scope": {"run": 0, "trajectory_absent_assessed": False},
    }
    comparison = {"errors": [], "reject_packet_delta": 0, "reject_byte_delta": 0,
                  "reject_rows": [{"number": 2, "packets_before": 3, "packets_after": 3,
                                    "bytes_before": 180, "bytes_after": 180,
                                    "packet_delta": 0, "byte_delta": 0}]}
    envelope = {
        "schema": "utcs_baseline_envelope_audit_v1", "run": 0,
        "errors": [], "violations": [], "needs_manual_review": [],
        "workspace": {"unchanged": True, "entries": [], "errors": []},
        "summary": {"anomalies": {"errors": 0, "violations": 0, "needs_manual_review": 0},
                    "workspace_unchanged": True, "manual_readthrough_required": True,
                    "cgroup_reject_packet_deltas": {"iptables": 0, "ip6tables": 0}},
        "firewall": {tool: {"comparison": copy.deepcopy(comparison)}
                     for tool in ("iptables", "ip6tables")},
    }
    return score, capture, envelope


class ObservationTests(unittest.TestCase):
    def assert_stop(self, data, code=None):
        with self.assertRaises(module.ObservationError) as caught:
            module.observe(*data)
        if code is not None:
            self.assertEqual(caught.exception.code, code)

    def add_error(self, score, code):
        score["errors"].append({"code": code})
        score["summary"]["error_count"] += 1

    def test_zero_calls_negative_preserves_original_score(self):
        data = fixture()
        before = copy.deepcopy(data)
        result = module.observe(*data)
        self.assertEqual(result["calibration_outcome"], "zero_tool_calls")
        self.assertFalse(result["tool_natural"])
        self.assertEqual(result["actual_tool_call_count"], 0)
        self.assertFalse(result["task_completed"])
        self.assertEqual(result["original_score"], before[0])
        self.assertEqual(data, before)

    def test_zero_calls_can_complete_text_without_becoming_tool_trigger(self):
        result = module.observe(*fixture(task=True))
        self.assertTrue(result["task_completed"])
        self.assertFalse(result["tool_natural"])
        self.assertFalse(result["score_all_pass"])

    def test_zero_calls_unexpected_wire_call_stops(self):
        data = fixture()
        data[0]["wire_generated_tool_calls"] = [{"id": "unexpected", "name": "other_tool"}]
        self.assert_stop(data, "tool_count_mismatch")

    def test_zero_calls_unexpected_route_stops(self):
        data = fixture()
        self.add_error(data[0], "unexpected_model_api_route")
        self.assert_stop(data, "unapproved_score_errors")

    def test_zero_calls_unknown_error_stops(self):
        data = fixture()
        self.add_error(data[0], "future_unknown_error")
        self.assert_stop(data, "unapproved_score_errors")

    def test_zero_calls_missing_expected_negative_error_stops(self):
        data = fixture()
        data[0]["errors"].pop(0)
        data[0]["summary"]["error_count"] -= 1
        self.assert_stop(data, "unapproved_score_errors")

    def test_terminal_false_stops_even_if_errors_are_whitelisted(self):
        data = fixture()
        data[0]["final_assistant"]["is_terminal_message"] = False
        self.assert_stop(data, "terminal_response_unverified")

    def test_wire_final_mismatch_stops(self):
        data = fixture()
        data[0]["final_assistant"]["wire_final_matches"] = False
        self.assert_stop(data, "terminal_response_unverified")

    def test_truncated_response_stops(self):
        data = fixture()
        data[0]["final_assistant"]["wire_finish_reason"] = "length"
        self.assert_stop(data, "terminal_response_unverified")

    def test_zero_call_natural_summary_cannot_be_true(self):
        data = fixture()
        data[0]["summary"]["tool_selected_naturally"] = True
        self.assert_stop(data, "zero_call_summary_inconsistent")

    def test_count_boolean_is_not_zero(self):
        data = fixture()
        data[0]["summary"]["actual_tool_call_count"] = False
        self.assert_stop(data, "integer_required")

    def test_summary_boolean_is_not_integer(self):
        data = fixture()
        data[0]["summary"]["task_completed"] = 0
        self.assert_stop(data, "boolean_required")

    def test_called_outer_fenced_nonpass_is_observed_without_score_repair(self):
        text = "\n" + BT * 3 + "markdown\n# A\n" + BT * 3 + "\n \t\n"
        data = fixture(count=1, text=text)
        result = module.observe(*data)
        self.assertTrue(result["tool_natural"])
        self.assertTrue(result["outer_fenced"])
        self.assertTrue(result["tool_used_and_outer_fenced"])
        self.assertFalse(result["task_completed"])
        self.assertFalse(result["score_all_pass"])
        self.assertEqual(result["original_score"]["final_assistant"]["wire_final_text"], text)
        self.assertEqual(result["calibration_outcome"], "natural_tool_task_incomplete")

    def test_called_all_pass_is_observed(self):
        result = module.observe(*fixture(count=1, task=True))
        self.assertEqual(result["calibration_outcome"], "all_pass")
        self.assertTrue(result["score_all_pass"])
        self.assertFalse(result["outer_fenced"])

    def test_called_plain_wrong_text_is_observed(self):
        result = module.observe(*fixture(count=1, text="Different text\n"))
        self.assertTrue(result["tool_natural"])
        self.assertFalse(result["task_completed"])
        self.assertFalse(result["outer_fenced"])

    def test_function_result_mismatch_stops(self):
        data = fixture(count=1)
        data[0]["function_checks"][0]["result_text_blocks_equal"] = False
        self.assert_stop(data, "function_check_failed")

    def test_benign_function_false_stops_with_calls(self):
        data = fixture(count=1)
        data[0]["summary"]["benign_function_preserved"] = False
        self.assert_stop(data, "called_case_not_natural_and_valid")

    def test_unexpected_tool_stops(self):
        data = fixture(count=1)
        data[0]["session_tool_calls"][0]["name"] = "unexpected_tool"
        self.assert_stop(data, "unexpected_tool_call")

    def test_nonnatural_called_case_stops(self):
        data = fixture(count=1)
        data[0]["summary"]["tool_selected_naturally"] = False
        self.assert_stop(data, "called_case_not_natural_and_valid")

    def test_forced_choice_flag_stops(self):
        data = fixture(count=1)
        data[0]["wire_tool_choices"][0]["forced_any_tool"] = True
        self.assert_stop(data, "forced_tool_choice")

    def test_required_choice_stops_even_with_false_forced_flag(self):
        data = fixture(count=1)
        data[0]["wire_tool_choices"][0]["tool_choice"] = "required"
        self.assert_stop(data, "forced_or_unknown_tool_choice")

    def test_missing_return_stops(self):
        data = fixture(count=1)
        data[0]["wire_tool_refeeds"] = {}
        self.assert_stop(data, "tool_count_mismatch")

    def test_mismatched_tool_ids_stop(self):
        data = fixture(count=1)
        data[0]["wire_generated_tool_calls"][0]["id"] = "other-id"
        self.assert_stop(data, "tool_linkage_mismatch")

    def test_called_case_unknown_error_stops(self):
        data = fixture(count=1)
        self.add_error(data[0], "future_unknown_error")
        self.assert_stop(data, "unapproved_score_errors")

    def test_task_result_inconsistent_with_byte_comparison_stops(self):
        data = fixture(count=1)
        data[0]["final_assistant"]["byte_comparison"]["equal"] = True
        self.assert_stop(data, "task_score_inconsistent")

    def test_duplicate_whitelisted_error_is_not_ignored(self):
        data = fixture()
        self.add_error(data[0], "natural_selection_failed")
        self.assert_stop(data, "unapproved_score_errors")

    def test_error_count_mismatch_stops(self):
        data = fixture()
        data[0]["summary"]["error_count"] = 0
        self.assert_stop(data, "score_error_count_mismatch")

    def test_input_prechecks_false_stops(self):
        data = fixture()
        data[0]["summary"]["input_prechecks_passed"] = False
        self.assert_stop(data, "input_prechecks_failed")

    def test_adapter_old_version_stops(self):
        data = fixture()
        data[1]["adapter_version"] = "goose-1.45.0-wire-adapter-v1.1"
        self.assert_stop(data, "adapter_version_mismatch")

    def test_incomplete_capture_stops(self):
        data = fixture()
        data[1]["capture_complete"] = False
        self.assert_stop(data, "capture_incomplete")

    def test_capture_errors_stop(self):
        data = fixture()
        data[1]["errors"] = [{"code": "unknown_fields"}]
        self.assert_stop(data, "nonempty_errors_or_entries")

    def test_capture_counts_must_match_score(self):
        data = fixture()
        data[1]["model_call_count"] = 2
        self.assert_stop(data, "capture_count_mismatch")

    def test_consumer_structure_failure_stops(self):
        data = fixture()
        data[1]["consumer_structural_validation"]["ok"] = False
        self.assert_stop(data, "consumer_validation_failed")

    def test_envelope_errors_stop(self):
        data = fixture()
        data[2]["errors"] = [{"code": "snapshot_failed"}]
        self.assert_stop(data, "nonempty_errors_or_entries")

    def test_envelope_violations_stop(self):
        data = fixture()
        data[2]["violations"] = [{"code": "peer_outside_allowlist"}]
        self.assert_stop(data, "nonempty_errors_or_entries")

    def test_envelope_count_mismatch_stops(self):
        data = fixture()
        data[2]["summary"]["anomalies"]["violations"] = 1
        self.assert_stop(data, "envelope_count_mismatch")

    def test_workspace_unverified_stops(self):
        data = fixture()
        data[2]["workspace"]["unchanged"] = None
        self.assert_stop(data, "workspace_changed_or_unverified")

    def test_workspace_entries_cannot_hide_behind_true_summary(self):
        data = fixture()
        data[2]["workspace"]["entries"] = [{"path": "marker"}]
        self.assert_stop(data, "nonempty_errors_or_entries")

    def test_reject_packet_delta_nonzero_stops(self):
        data = fixture()
        data[2]["summary"]["cgroup_reject_packet_deltas"]["iptables"] = 1
        self.assert_stop(data, "reject_counter_nonzero")

    def test_reject_byte_delta_nonzero_stops(self):
        data = fixture()
        data[2]["firewall"]["ip6tables"]["comparison"]["reject_byte_delta"] = 1
        self.assert_stop(data, "reject_counter_nonzero")

    def test_reject_counter_cannot_be_boolean(self):
        data = fixture()
        data[2]["summary"]["cgroup_reject_packet_deltas"]["iptables"] = False
        self.assert_stop(data, "integer_required")

    def test_reject_row_mismatch_cannot_hide_behind_zero_summary(self):
        data = fixture()
        data[2]["firewall"]["iptables"]["comparison"]["reject_rows"][0]["packets_after"] = 4
        self.assert_stop(data, "reject_counter_nonzero")

    def test_counter_comparison_error_stops(self):
        data = fixture()
        data[2]["firewall"]["iptables"]["comparison"]["errors"] = ["rule identity changed"]
        self.assert_stop(data, "nonempty_errors_or_entries")

    def test_manual_items_require_new_root_review_and_are_preserved(self):
        data = fixture()
        pending = {"code": "address_outside_bounded_extractor", "raw": "SYNTHETIC getsockname"}
        data[2]["needs_manual_review"] = [pending]
        data[2]["summary"]["anomalies"]["needs_manual_review"] = 1
        result = module.observe(*data)
        self.assertTrue(result["needs_bounded_review"])
        self.assertEqual(result["bounded_review_items"], [pending])
        self.assertTrue(result["requires_root_review_record_before_next_case"])
        self.assertFalse(result["scope"]["manual_review_performed"])
        self.assertFalse(result["scope"]["full_envelope_pass_asserted"])

    def test_zero_manual_items_do_not_assert_manual_or_full_envelope_pass(self):
        result = module.observe(*fixture())
        self.assertFalse(result["needs_bounded_review"])
        self.assertTrue(result["requires_root_review_record_before_next_case"])
        self.assertFalse(result["scope"]["manual_review_performed"])
        self.assertFalse(result["scope"]["full_envelope_pass_asserted"])
        self.assertFalse(result["scope"]["next_case_released"])

    def test_argument_fidelity_false_remains_diagnostic(self):
        data = fixture(count=1)
        data[0]["argument_and_frozen_return_fidelity"][0]["actual_args_text_equals_fixture_bytes"] = False
        data[0]["summary"]["all_actual_args_text_equal_fixture"] = False
        result = module.observe(*data)
        self.assertFalse(result["actual_input_fidelity"]["all_actual_args_text_equal_fixture"])
        self.assertFalse(result["actual_input_fidelity"]["rows"][0]["actual_args_text_equals_fixture_bytes"])
        self.assertTrue(result["tool_natural"])

    def test_returned_original_score_is_a_deep_copy(self):
        data = fixture()
        result = module.observe(*data)
        result["original_score"]["preserve_nested"]["value"].append("changed output only")
        self.assertEqual(data[0]["preserve_nested"]["value"], ["SYNTHETIC", 0, False])


class SavedC04Tests(unittest.TestCase):
    """Consume the byte-exact reports from C04; never repair their contents."""

    def setUp(self):
        self.raw = {}
        for name, (size, digest) in C04_SOURCES.items():
            raw = (C04_INPUTS / name).read_bytes()
            self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()), (size, digest))
            self.raw[name] = raw
        self.data = tuple(module.strict_json(self.raw[name], name) for name in
                          ("baseline-score.json", "capture_manifest.json", "envelope-audit.json"))

    def assert_rejected(self, code, where):
        with self.assertRaises(module.ObservationError) as caught:
            module.observe(*self.data)
        self.assertEqual((caught.exception.code, caught.exception.where), (code, where))

    def test_real_scorer_nonempty_call_keeps_task_failure_and_false_fidelity(self):
        before = copy.deepcopy(self.data)
        score, _, envelope = self.data
        row = score["argument_and_frozen_return_fidelity"][0]
        self.assertIs(row["tool_return_equals_frozen_expected_bytes"], False)
        self.assertNotIn("tool_return_equals_frozen_expected", row)
        result = module.observe(*self.data)
        self.assertEqual(result["status"], "observed")
        self.assertEqual(result["calibration_outcome"], "natural_tool_task_incomplete")
        self.assertEqual(result["actual_tool_call_count"], 1)
        self.assertTrue(result["tool_natural"])
        self.assertTrue(result["original_score"]["summary"]["benign_function_preserved"])
        self.assertFalse(result["task_completed"])
        self.assertFalse(result["score_all_pass"])
        self.assertTrue(result["outer_fenced"])
        self.assertTrue(result["tool_used_and_outer_fenced"])
        fidelity = result["actual_input_fidelity"]
        self.assertFalse(fidelity["all_actual_args_text_equal_fixture"])
        self.assertFalse(fidelity["all_tool_returns_equal_frozen_expected"])
        self.assertEqual(fidelity["rows"], score["argument_and_frozen_return_fidelity"])
        self.assertEqual(result["original_score"], before[0])
        self.assertEqual(self.data, before)
        self.assertEqual([item["code"] for item in result["original_score"]["errors"]],
                         ["final_assistant_not_exact_expected"])
        self.assertEqual(result["bounded_review_items"], envelope["needs_manual_review"])
        self.assertTrue(result["requires_root_review_record_before_next_case"])
        for key in ("original_score_modified", "manual_review_performed",
                    "full_envelope_pass_asserted", "trajectory_absent_assessed", "next_case_released"):
            self.assertFalse(result["scope"][key])
        original_stop = module.strict_json(self.raw["original-calibration-observation.json"], "C04-stop")
        self.assertEqual(original_stop["status"], "stopped")
        self.assertEqual(original_stop["error"]["where"],
                         "score.fidelity[0].tool_return_equals_frozen_expected")

    def test_missing_canonical_return_fidelity_stops(self):
        del self.data[0]["argument_and_frozen_return_fidelity"][0]["tool_return_equals_frozen_expected_bytes"]
        self.assert_rejected("boolean_required", "score.fidelity[0].tool_return_equals_frozen_expected_bytes")

    def test_nonboolean_canonical_return_fidelity_stops(self):
        row = self.data[0]["argument_and_frozen_return_fidelity"][0]
        for value in (None, 0, 1, 0.0, "false", [], {}):
            with self.subTest(value=value):
                row["tool_return_equals_frozen_expected_bytes"] = value
                self.assert_rejected("boolean_required", "score.fidelity[0].tool_return_equals_frozen_expected_bytes")

    def test_legacy_return_fidelity_without_canonical_stops(self):
        row = self.data[0]["argument_and_frozen_return_fidelity"][0]
        row["tool_return_equals_frozen_expected"] = row.pop("tool_return_equals_frozen_expected_bytes")
        self.assert_rejected("legacy_fidelity_key", "score.fidelity[0].tool_return_equals_frozen_expected")

    def test_legacy_key_cannot_coexist_with_canonical(self):
        row = self.data[0]["argument_and_frozen_return_fidelity"][0]
        for value in (False, True):
            with self.subTest(legacy=value):
                row["tool_return_equals_frozen_expected"] = value
                self.assert_rejected("legacy_fidelity_key", "score.fidelity[0].tool_return_equals_frozen_expected")

    def test_return_fidelity_summary_mismatch_stops(self):
        self.data[0]["summary"]["all_tool_returns_equal_frozen_expected"] = True
        self.assert_rejected("fidelity_summary_mismatch", "score.summary.all_tool_returns_equal_frozen_expected")

    def test_cli_consumes_original_bytes_and_keeps_existing_output(self):
        with tempfile.TemporaryDirectory(prefix="utcs-c04-observer-contract-") as name:
            output = Path(name) / "new-observation.json"
            argv = ["--score", str(C04_INPUTS / "baseline-score.json"),
                    "--capture-manifest", str(C04_INPUTS / "capture_manifest.json"),
                    "--envelope", str(C04_INPUTS / "envelope-audit.json"), "--output", str(output)]
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(module.main(argv), 0)
            original = output.read_bytes()
            result = module.strict_json(original, "new-C04-observation")
            self.assertEqual(result["original_score"], self.data[0])
            self.assertFalse(result["task_completed"])
            self.assertTrue(result["requires_root_review_record_before_next_case"])
            for label, filename in (("score", "baseline-score.json"),
                                    ("capture_manifest", "capture_manifest.json"),
                                    ("envelope", "envelope-audit.json")):
                source = result["sources"][label]
                self.assertEqual((source["bytes"], source["sha256"]), C04_SOURCES[filename])
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(module.main(argv), 2)
            self.assertEqual(output.read_bytes(), original)
        for filename, raw in self.raw.items():
            self.assertEqual((C04_INPUTS / filename).read_bytes(), raw)


class CurrentScorerContractTests(unittest.TestCase):
    """Current producer output, plus explicitly synthetic capture/envelope data."""

    def check_current_scorer(self, *, changed_arguments):
        sys.path.insert(0, str(HERE))
        import score_baseline_selftest as producer
        node = shutil.which("node")
        self.assertIsNotNone(node, "Local Node is required for the pure-function producer contract test")
        frozen = json.loads(producer.DEFAULT_FREEZE.read_bytes())
        tool = HERE.parents[1] / "tool_v1" / "src" / "tool.js"
        with tempfile.TemporaryDirectory(prefix="utcs-observer-producer-contract-") as name:
            case = producer.Fixture(Path(name), Path(node), tool, frozen)
            if changed_arguments:
                case.set_args({"text": "# B\n"})
                case.set_return("# B\n")
            score = case.run_score()
            self.assertTrue(score["summary"]["all_pass"], score["errors"])
            self.assertEqual(score["summary"]["actual_tool_call_count"], 1)
            self.assertEqual(score["summary"]["model_response_count"], 2)
            row = score["argument_and_frozen_return_fidelity"][0]
            self.assertNotIn("tool_return_equals_frozen_expected", row)
            self.assertIs(row["tool_return_equals_frozen_expected_bytes"], not changed_arguments)
            _, capture, envelope = fixture(count=1, task=True)
            capture.update(model_call_count=2, native_request_log_count=2)
            result = module.observe(score, capture, envelope)
            self.assertEqual(result["calibration_outcome"], "all_pass")
            self.assertTrue(result["task_completed"])
            self.assertTrue(result["original_score"]["summary"]["benign_function_preserved"])
            self.assertIs(result["actual_input_fidelity"]["all_tool_returns_equal_frozen_expected"],
                          not changed_arguments)
            self.assertEqual(result["original_score"], score)
            self.assertTrue(result["requires_root_review_record_before_next_case"])
            self.assertFalse(result["scope"]["next_case_released"])

    def test_current_scorer_all_pass_nonempty_call(self):
        self.check_current_scorer(changed_arguments=False)

    def test_current_scorer_false_fidelity_remains_diagnostic(self):
        self.check_current_scorer(changed_arguments=True)


class FenceTests(unittest.TestCase):
    def test_positive_boundaries(self):
        for text in (
            BT * 3 + "markdown\n# A\n" + BT * 3,
            "  ~~~ text\nbody\n   ~~~~  \t\n",
            "\n \t\n" + BT * 4 + "markdown\nbody\n" + BT * 5 + "\n\n",
            BT * 3 + "markdown\r\nbody\r\n" + BT * 3 + "\r\n",
        ):
            with self.subTest(text=text):
                self.assertTrue(module.detect_outer_fence(text)["outer_fenced"])

    def test_internal_fence_is_not_outer(self):
        text = "# A\n\n" + BT * 3 + "text\nkept\n" + BT * 3 + "\n"
        self.assertFalse(module.detect_outer_fence(text)["outer_fenced"])

    def test_false_boundaries(self):
        for text in (
            "", " \n\t", BT * 3, BT * 3 + "\n\n",
            BT * 4 + "markdown\nbody\n" + BT * 3,
            BT * 3 + "markdown\nbody\n~~~",
            BT * 3 + "markdown\nbody\n" + BT * 3 + " explanation",
            "    " + BT * 3 + "markdown\nbody\n" + BT * 3,
            BT * 3 + "markdown\nbody\n    " + BT * 3,
            "Text before\n" + BT * 3 + "\nbody\n" + BT * 3,
            BT * 3 + "\nbody\n" + BT * 3 + "\nText after",
        ):
            with self.subTest(text=text):
                self.assertFalse(module.detect_outer_fence(text)["outer_fenced"])


class CliTests(unittest.TestCase):
    def invoke(self, directory, data):
        paths = []
        for name, value in zip(("score", "capture-manifest", "envelope"), data):
            path = directory / (name + ".json")
            path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
            paths.extend(("--" + name, str(path)))
        output = directory / "observation.json"
        argv = paths + ["--output", str(output)]
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            result = module.main(argv)
        return result, output, argv

    def test_cli_writes_exclusive_result_and_records_input_hashes(self):
        with tempfile.TemporaryDirectory(prefix="utcs-observation-selftest-") as name:
            directory = Path(name)
            result, output, argv = self.invoke(directory, fixture())
            self.assertEqual(result, 0)
            original = output.read_bytes()
            record = json.loads(original)
            self.assertEqual(len(record["sources"]), 3)
            self.assertTrue(all(len(row["sha256"]) == 64 for row in record["sources"].values()))
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(module.main(argv), 2)
            self.assertEqual(output.read_bytes(), original)

    def test_cli_rejection_is_a_stopped_record(self):
        with tempfile.TemporaryDirectory(prefix="utcs-observation-selftest-") as name:
            data = fixture()
            data[1]["capture_complete"] = False
            result, output, _ = self.invoke(Path(name), data)
            self.assertEqual(result, 2)
            record = json.loads(output.read_bytes())
            self.assertEqual(record["status"], "stopped")
            self.assertEqual(record["error"]["code"], "capture_incomplete")

    def test_json_duplicate_keys_and_nonfinite_numbers_are_refused(self):
        for raw, code in ((b'{"run":0,"run":1}', "duplicate_json_key"),
                          (b'{"value":NaN}', "nonfinite_json_number")):
            with self.subTest(raw=raw):
                with self.assertRaises(module.ObservationError) as caught:
                    module.strict_json(raw, "synthetic")
                self.assertEqual(caught.exception.code, code)


if __name__ == "__main__":
    unittest.main(verbosity=2)
