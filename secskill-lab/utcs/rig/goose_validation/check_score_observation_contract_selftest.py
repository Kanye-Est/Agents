#!/usr/bin/env python3
"""Offline AST/index/hook tests; no producer, consumer, model or VM execution."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SPEC = importlib.util.spec_from_file_location("ast_contract_checker", HERE / "check_score_observation_contract.py")
checker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)

GOOD_PRODUCER = '''
def score():
    report = {"schema": "synthetic"}
    rows = []
    for item in source:
        rows.append({"tool_return_equals_frozen_expected_bytes": True})
    report["summary"] = {"all_tool_returns_equal_frozen_expected": True,
                         "tool_return_equals_frozen_expected": True}
    report["final_assistant"] = {"text": ""}
    report["argument_and_frozen_return_fidelity"] = rows
    return report
'''
GOOD_CONSUMER = '''
def observe(score):
    summary = score["summary"]
    rows = score["argument_and_frozen_return_fidelity"]
    final = score["final_assistant"]
    final_text = final["text"]
    for summary_key, row_key in (("all_tool_returns_equal_frozen_expected",
                                  "tool_return_equals_frozen_expected_bytes"),):
        aggregate = summary[summary_key]
        actual = all(row[row_key] for row in rows)
    return True
'''
BAD_CONSUMER = GOOD_CONSUMER.replace('"tool_return_equals_frozen_expected_bytes"',
                                     '"tool_return_equals_frozen_expected"')


class SyntaxContractTests(unittest.TestCase):
    def check(self, producer=GOOD_PRODUCER, consumer=GOOD_CONSUMER):
        return checker.check_sources(producer.encode(), consumer.encode())

    def test_separate_scopes_and_constant_tuple_comprehension(self):
        code, result = self.check()
        self.assertEqual(code, 0, result)
        self.assertEqual(set(result["checked_scopes"]), {
            "score", "score.summary", "score.final_assistant", "score.argument_and_frozen_return_fidelity[]"})

    def test_original_mismatch_not_hidden_by_same_key_in_summary(self):
        code, result = self.check(consumer=BAD_CONSUMER)
        self.assertEqual(code, 1, result)
        self.assertTrue(all(d["scope"] == "score.argument_and_frozen_return_fidelity[]"
                            and d["key"] == "tool_return_equals_frozen_expected" for d in result["diagnostics"]))

    def test_missing_summary_key_is_not_satisfied_by_row_key(self):
        text = GOOD_CONSUMER.replace('"all_tool_returns_equal_frozen_expected",',
                                     '"tool_return_equals_frozen_expected_bytes",')
        code, result = self.check(consumer=text)
        self.assertEqual(code, 1, result)
        self.assertEqual(result["diagnostics"][0]["scope"], "score.summary")

    def test_aliases_and_enumerated_rows_keep_scope(self):
        text = GOOD_CONSUMER.replace("    return True", '''    alias = rows
    for index, row in enumerate(alias):
        row_alias = row
        value = row_alias.get("tool_return_equals_frozen_expected")
    return True''')
        code, result = self.check(consumer=text)
        self.assertEqual(code, 1, result)
        self.assertEqual(result["diagnostics"][0]["scope"], "score.argument_and_frozen_return_fidelity[]")

    def test_negative_membership_is_not_a_value_read(self):
        text = GOOD_CONSUMER.replace("    return True", '''    for row in rows:
        assert "arbitrary_forbidden_key" not in row
    return True''')
        code, result = self.check(consumer=text)
        self.assertEqual(code, 0, result)
        self.assertNotIn("arbitrary_forbidden_key", [r["key"] for r in result["consumer_reads"]])

    def test_all_emitted_row_shapes_must_supply_key(self):
        text = GOOD_PRODUCER.replace('    report["summary"]', '    rows.append({"different": True})\n    report["summary"]')
        code, result = self.check(producer=text)
        self.assertEqual(code, 1, result)
        self.assertEqual(result["checked_scopes"]["score.argument_and_frozen_return_fidelity[]"], [])

    def test_computed_consumer_key_fails_closed(self):
        text = GOOD_CONSUMER.replace("    return True", "    value = summary[dynamic_key]\n    return True")
        code, result = self.check(consumer=text)
        self.assertEqual(code, 2, result)
        self.assertEqual(result["diagnostics"][0]["code"], "consumer_key_unresolved")

    def test_opaque_alias_call_fails_closed(self):
        text = GOOD_CONSUMER.replace('summary = score["summary"]', 'summary = unknown(score["summary"])')
        code, result = self.check(consumer=text)
        self.assertEqual(code, 2, result)
        self.assertEqual(result["diagnostics"][0]["code"], "consumer_call_unresolved")

    def test_producer_dictionary_unpacking_fails_closed(self):
        text = GOOD_PRODUCER.replace('{"all_tool_returns_equal_frozen_expected": True,',
                                     '{**dynamic_keys, "all_tool_returns_equal_frozen_expected": True,')
        code, result = self.check(producer=text)
        self.assertEqual(code, 2, result)
        self.assertEqual(result["diagnostics"][0]["code"], "producer_mapping_unpacking")

    def test_producer_list_extend_fails_closed(self):
        text = GOOD_PRODUCER.replace('    report["summary"]', '    rows.extend(external_rows)\n    report["summary"]')
        code, result = self.check(producer=text)
        self.assertEqual(code, 2, result)
        self.assertEqual(result["diagnostics"][0]["code"], "producer_rows_mutation")

    def test_producer_nested_mapping_alias_fails_closed(self):
        text = GOOD_PRODUCER.replace("    return report", '    alias = report["summary"]\n    alias.clear()\n    return report')
        code, result = self.check(producer=text)
        self.assertEqual(code, 2, result)
        self.assertEqual(result["diagnostics"][0]["code"], "producer_nested_scope_escape")

    def test_syntax_error_is_unresolved(self):
        code, result = self.check(consumer="def observe(:")
        self.assertEqual(code, 2, result)
        self.assertEqual(result["diagnostics"][0]["source"], checker.CONSUMER)

    def test_real_producer_and_current_consumer(self):
        code, result = checker.check_sources((REPO / checker.PRODUCER).read_bytes(),
                                             (REPO / checker.CONSUMER).read_bytes())
        self.assertEqual(code, 0, result)

    def test_real_sources_with_original_read_typo_are_rejected(self):
        raw = (REPO / checker.CONSUMER).read_bytes()
        self.assertIn(b'"tool_return_equals_frozen_expected_bytes"', raw)
        mutated = raw.replace(b'"tool_return_equals_frozen_expected_bytes"', b'"tool_return_equals_frozen_expected"')
        code, result = checker.check_sources((REPO / checker.PRODUCER).read_bytes(), mutated)
        self.assertEqual(code, 1, result)
        self.assertTrue(any(d["scope"] == "score.argument_and_frozen_return_fidelity[]"
                            and d["key"] == "tool_return_equals_frozen_expected" for d in result["diagnostics"]))


class IndexAndHookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="utcs-ast-contract-")
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.env = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null",
                    "PYTHONDONTWRITEBYTECODE": "1"}
        self.git("init", "-q")
        for path, raw in ((checker.PRODUCER, GOOD_PRODUCER.encode()),
                          (checker.CONSUMER, GOOD_CONSUMER.encode()),
                          (checker.CHECKER, (REPO / checker.CHECKER).read_bytes()),
                          (".githooks/pre-commit", (REPO / ".githooks/pre-commit").read_bytes())):
            self.write(path, raw)
        (self.repo / ".githooks/pre-commit").chmod(0o755)
        self.git("add", "--", checker.PRODUCER, checker.CONSUMER, checker.CHECKER, ".githooks/pre-commit")
        self.git("config", "--local", "core.hooksPath", ".githooks")

    def write(self, path, raw):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)

    def git(self, *args, check=True):
        return subprocess.run(["git", "-C", str(self.repo), *args], env=self.env,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check)

    def invoke(self, staged=True):
        argv = [sys.executable, "-B", str(REPO / checker.CHECKER), "--repo", str(self.repo), "--json"]
        if staged:
            argv.append("--staged")
        result = subprocess.run(argv, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode, json.loads(result.stdout)

    def test_bad_index_good_worktree_remains_rejected(self):
        self.write(checker.CONSUMER, BAD_CONSUMER.encode())
        self.git("add", "--", checker.CONSUMER)
        self.write(checker.CONSUMER, GOOD_CONSUMER.encode())
        code, result = self.invoke()
        self.assertEqual(code, 1, result)
        self.assertEqual(result["source"], "index-stage-0")
        self.assertEqual(self.invoke(staged=False)[0], 0)

    def test_good_index_bad_worktree_remains_compatible(self):
        self.write(checker.CONSUMER, BAD_CONSUMER.encode())
        self.assertEqual(self.invoke()[0], 0)
        self.assertEqual(self.invoke(staged=False)[0], 1)

    def test_missing_index_source_fails_closed(self):
        self.git("rm", "--cached", "--", checker.CONSUMER)
        code, result = self.invoke()
        self.assertEqual(code, 2, result)
        self.assertEqual(result["diagnostics"][0]["code"], "source_read_error")

    def test_git_hook_uses_staged_checker_and_staged_inputs(self):
        self.write(checker.CHECKER, b"raise SystemExit(77)\n")
        self.write(checker.CONSUMER, BAD_CONSUMER.encode())
        result = self.git("hook", "run", "pre-commit", check=False)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        # `git hook run` redirects hook stdout into stderr (verified on git
        # 2.55.0 by minimal repro); assert the staged-source marker there.
        self.assertIn(b"index-stage-0", result.stderr)

    def test_git_hook_rejects_bad_index_despite_unstaged_repair(self):
        self.write(checker.CONSUMER, BAD_CONSUMER.encode())
        self.git("add", "--", checker.CONSUMER)
        self.write(checker.CONSUMER, GOOD_CONSUMER.encode())
        result = self.git("hook", "run", "pre-commit", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"missing_producer_key", result.stderr)

    def test_git_hook_refuses_missing_staged_checker(self):
        self.git("rm", "--cached", "--", checker.CHECKER)
        result = self.git("hook", "run", "pre-commit", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"staged AST contract checker is missing", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
