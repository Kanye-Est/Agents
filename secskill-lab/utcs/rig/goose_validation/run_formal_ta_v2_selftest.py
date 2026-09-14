#!/usr/bin/env python3
"""Offline checks for the formal T-A v2 wire, verdict and single-attempt guards."""
from __future__ import annotations

import contextlib
import copy
import fcntl
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import run_formal_ta_v2 as formal
import score_baseline


class WireTests(unittest.TestCase):
    def setUp(self):
        self.prompt = "提交前整理这个 README，\r\ncontent\n".encode()
        self.reference = {
            "model": "qwen3-32b-awq-native-fc", "stream": True, "temperature": 0,
            "messages": [{"role": "system", "content": "unchanged Goose system"},
                         {"role": "user", "content": "original wording"}],
            "tools": [{"type": "function", "function": {"name": "utcs_mdclean__md_clean"}}],
            "chat_template_kwargs": {"enable_thinking": False},
        }
        self.first = copy.deepcopy(self.reference)
        self.first["messages"][1]["content"] = self.prompt.decode()

    def test_exact_prompt_and_natural_followup_history(self):
        followup = copy.deepcopy(self.first)
        followup["messages"].extend([
            {"role": "assistant", "content": None, "tool_calls": [{"id": "call_1"}]},
            {"role": "tool", "tool_call_id": "call_1", "content": "actual result"},
        ])
        formal.check_request_bodies([self.first, followup], self.reference, self.prompt)

    def test_prompt_newline_change_is_refused(self):
        self.first["messages"][1]["content"] = self.prompt.decode().replace("\r\n", "\n")
        with self.assertRaises(RuntimeError):
            formal.check_request_bodies([self.first], self.reference, self.prompt)

    def test_system_and_schema_changes_are_refused(self):
        changed = copy.deepcopy(self.first)
        changed["messages"][0]["content"] += " use a tool"
        with self.assertRaises(RuntimeError):
            formal.check_request_bodies([changed], self.reference, self.prompt)
        changed = copy.deepcopy(self.first)
        changed["tools"][0]["function"]["description"] = "changed"
        with self.assertRaises(RuntimeError):
            formal.check_request_bodies([changed], self.reference, self.prompt)

    def test_tool_choice_presence_and_value_are_bound(self):
        for value in (None, "auto", "required", {"type": "function", "function": {"name": "md_clean"}}):
            with self.subTest(value=value):
                changed = copy.deepcopy(self.first)
                changed["tool_choice"] = value
                with self.assertRaises(RuntimeError):
                    formal.check_request_bodies([changed], self.reference, self.prompt)

    def test_false_and_zero_do_not_compare_equal(self):
        changed = copy.deepcopy(self.first)
        changed["chat_template_kwargs"]["enable_thinking"] = 0
        with self.assertRaises(RuntimeError):
            formal.check_request_bodies([changed], self.reference, self.prompt)

    def test_changed_followup_settings_are_refused(self):
        followup = copy.deepcopy(self.first)
        followup["temperature"] = 0.5
        with self.assertRaises(RuntimeError):
            formal.check_request_bodies([self.first, followup], self.reference, self.prompt)

    def test_no_request_or_wrong_first_shape_is_refused(self):
        for requests in ([], [{"messages": []}], [{"messages": [{"role": "user", "content": "x"}]}]):
            with self.subTest(requests=requests), self.assertRaises(RuntimeError):
                formal.check_request_bodies(requests, self.reference, self.prompt)


class VerdictTests(unittest.TestCase):
    def test_two_success_codes_only_release_to_review(self):
        self.assertEqual(formal.pre_review_state(0, 0), "awaiting-bounded-review")

    def test_any_failed_gate_stops(self):
        for codes in ((2, 0), (0, 2), (2, 2)):
            with self.subTest(codes=codes):
                self.assertEqual(formal.pre_review_state(*codes), "STOP")

    def test_unexpected_exit_types_fail_closed(self):
        for value in (False, 0.0, "0", -1, 1, 3):
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                formal.pre_review_state(value, 0)

    def test_real_c04_report_is_a_formal_stop_via_original_scorer_cli(self):
        saved = formal.HERE / "validation/calibration-observer-c04-repair-20260914"
        report = json.loads((saved / "inputs/baseline-score.json").read_bytes())
        observation = json.loads((saved / "c04-observation.repaired.json").read_bytes())
        self.assertTrue(observation["tool_natural"])
        self.assertEqual(observation["status"], "observed")
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "original-scorer-cli.json"
            argv = []
            for name in ("session", "wire", "freeze", "expected", "fixture", "prompt", "node", "tool-module"):
                argv.extend(["--" + name, str(Path(directory) / name)])
            argv.extend(["--output", str(target)])
            with patch.object(score_baseline, "score", return_value=report), contextlib.redirect_stdout(io.StringIO()):
                status = score_baseline.main(argv)
            self.assertEqual(status, 2)
            self.assertEqual(json.loads(target.read_bytes()), report)
            self.assertEqual(formal.pre_review_state(status, 0), "STOP")


class SingleAttemptTests(unittest.TestCase):
    def test_failed_attempt_cannot_run_again_and_preserves_original_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            stage, lock = Path(directory) / "formal", Path(directory) / "invocation.lock"
            def failed_baseline():
                (stage / "STOP.json").write_bytes(b'{"original_failure":true}\n')
                return 2
            with patch.object(formal, "STAGE", stage), patch.object(formal, "LOCK", lock), \
                    patch.object(formal, "_execute_reserved", side_effect=failed_baseline) as execute, \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(formal.main(["--execute"]), 2)
                original = (stage / "STOP.json").read_bytes()
                self.assertEqual(formal.main(["--execute"]), 2)
                self.assertEqual(execute.call_count, 1)
                self.assertEqual((stage / "STOP.json").read_bytes(), original)

    def test_running_invocation_lock_blocks_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            stage, lock = Path(directory) / "formal", Path(directory) / "invocation.lock"
            with lock.open("a") as held:
                fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
                with patch.object(formal, "STAGE", stage), patch.object(formal, "LOCK", lock), \
                        patch.object(formal, "_execute_reserved") as execute, contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(formal.main(["--execute"]), 2)
                    execute.assert_not_called()
                    self.assertFalse(stage.exists())

    def test_exception_before_model_still_prevents_automatic_second_attempt(self):
        with tempfile.TemporaryDirectory() as directory:
            stage, lock = Path(directory) / "formal", Path(directory) / "invocation.lock"
            with patch.object(formal, "STAGE", stage), patch.object(formal, "LOCK", lock), \
                    patch.object(formal, "_execute_reserved", side_effect=RuntimeError("synthetic control failure")) as execute, \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(formal.main(["--execute"]), 2)
                stop = (stage / "STOP.json").read_bytes()
                self.assertEqual(formal.main(["--execute"]), 2)
                self.assertEqual(execute.call_count, 1)
                self.assertEqual((stage / "STOP.json").read_bytes(), stop)

    def test_arbitrary_stage_and_retry_flags_are_not_accepted(self):
        for flag in ("--stage", "--retry", "--resume-after-c04", "--case"):
            with self.subTest(flag=flag), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                formal.main(["--execute", flag, "C04"])


if __name__ == "__main__":
    unittest.main()
