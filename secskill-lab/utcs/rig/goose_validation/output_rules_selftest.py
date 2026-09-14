#!/usr/bin/env python3
"""Replay saved rule stdout and exercise negative fixtures; no VM/network/model."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
MODULE = HERE / "output_rules.py"
FIXTURE = HERE / "tests/fixtures/iptables-output-before.txt"
PROVENANCE = HERE / "tests/fixtures/iptables-output-before.provenance.json"
FIXTURE_SHA256 = "3ee5279a5a81057f9733f0f1c04cc91256e032ef5d3ae81807cbbb6b4d87b55c"
CGROUP = "system.slice/utcs-rig-ta-20260914-103238.service"
CHAIN = "UTCS_RIG4_103238"
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("output_rules_under_test", MODULE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def rule(path=CGROUP, chain=CHAIN, extra="", ending="\n"):
    return (f"-A OUTPUT -m cgroup --path {path}{extra} -j {chain}" + ending).encode()


class OutputRulesTests(unittest.TestCase):
    def verify(self, raw, passed, code=None, cgroup=CGROUP, chain=CHAIN):
        result = module.verify_output_rules(raw, cgroup, chain)
        self.assertIs(result["passed"], passed, result)
        if isinstance(raw, bytes):
            self.assertEqual(result["raw_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(result["raw_byte_count"], len(raw))
        if code:
            self.assertIn(code, [item["code"] for item in result["errors"]], result)
        return result

    def test_saved_stdout_direct_replay_and_provenance(self):
        raw = FIXTURE.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), FIXTURE_SHA256)
        self.assertEqual(len(raw), 115)
        event = json.loads(PROVENANCE.read_bytes())["event"]
        self.assertEqual(event["argv"], ["sudo", "-n", "iptables", "-S", "OUTPUT"])
        self.assertEqual(event["exit_code"], 0)
        self.assertEqual(raw, event["stdout"].encode("utf-8"))
        result = self.verify(raw, True)
        self.assertEqual(result["first_rule_line_number"], 2)
        self.assertEqual(result["first_rule_raw"].encode(), raw.splitlines(keepends=True)[1])
        self.assertEqual(result["first_rule_tokens"], result["expected_tokens"])
        self.assertEqual(FIXTURE.read_bytes(), raw)

    def test_quoted_and_unquoted_paths_have_identical_tokens(self):
        quoted = self.verify(FIXTURE.read_bytes(), True)
        unquoted = self.verify(b"-P OUTPUT ACCEPT\n" + rule(), True)
        self.assertEqual(quoted["first_rule_tokens"], unquoted["first_rule_tokens"])
        self.assertNotEqual(quoted["raw_sha256"], unquoted["raw_sha256"])

    def test_single_quoted_path_is_equivalent(self):
        self.verify(rule(path="'" + CGROUP + "'"), True)

    def test_quoted_chain_is_equivalent(self):
        self.verify(rule(chain='"' + CHAIN + '"'), True)

    def test_original_rule_whitespace_and_crlf_are_retained(self):
        raw = b"-P OUTPUT ACCEPT\r\n  " + rule(ending="\r\n")
        result = self.verify(raw, True)
        self.assertEqual(result["first_rule_raw"].encode(), raw.splitlines(keepends=True)[1])

    def test_missing_final_newline_is_not_synthesized(self):
        raw = rule(ending="")
        result = self.verify(raw, True)
        self.assertEqual(result["first_rule_raw"].encode(), raw)

    def test_subsequent_output_rules_do_not_change_first_rule(self):
        self.verify(rule() + b"-A OUTPUT -j ACCEPT\n", True)

    def test_wrong_path_is_rejected(self):
        self.verify(rule(path=CGROUP + "-other"), False, "first_output_rule_mismatch")

    def test_path_prefix_cannot_match(self):
        self.verify(rule(path="system.slice"), False, "first_output_rule_mismatch")

    def test_leading_slash_is_not_normalized(self):
        self.verify(rule(path="/" + CGROUP), False, "first_output_rule_mismatch")

    def test_wrong_chain_is_rejected(self):
        self.verify(rule(chain=CHAIN + "_OTHER"), False, "first_output_rule_mismatch")

    def test_prior_accept_is_rejected(self):
        result = self.verify(b"-A OUTPUT -j ACCEPT\n" + rule(), False,
                             "first_output_rule_mismatch")
        self.assertEqual(result["first_rule_line_number"], 1)
        self.assertEqual(result["first_rule_tokens"], ["-A", "OUTPUT", "-j", "ACCEPT"])

    def test_protocol_restriction_is_rejected(self):
        self.verify(rule(extra=" -p tcp"), False, "first_output_rule_mismatch")

    def test_explicit_all_protocol_option_is_not_accepted(self):
        self.verify(rule(extra=" -p all"), False, "first_output_rule_mismatch")

    def test_destination_restriction_is_rejected(self):
        self.verify(rule(extra=" -d 127.0.0.1/32"), False, "first_output_rule_mismatch")

    def test_negated_cgroup_is_rejected(self):
        raw = rule().replace(b"--path", b"! --path")
        self.verify(raw, False, "first_output_rule_mismatch")

    def test_goto_instead_of_jump_is_rejected(self):
        self.verify(rule().replace(b" -j ", b" -g "), False, "first_output_rule_mismatch")

    def test_duplicate_path_option_is_rejected(self):
        self.verify(rule(extra=" --path " + CGROUP), False, "first_output_rule_mismatch")

    def test_reordered_tokens_are_rejected(self):
        raw = f"-A OUTPUT -j {CHAIN} -m cgroup --path {CGROUP}\n".encode()
        self.verify(raw, False, "first_output_rule_mismatch")

    def test_trailing_comment_is_not_stripped(self):
        raw = rule(ending=" # extra\n")
        self.verify(raw, False, "first_output_rule_mismatch")

    def test_empty_output_is_rejected(self):
        self.verify(b"", False, "output_rule_missing")

    def test_policy_only_is_rejected(self):
        self.verify(b"-P OUTPUT ACCEPT\n", False, "output_rule_missing")

    def test_other_chain_does_not_supply_an_output_rule(self):
        self.verify(rule().replace(b"-A OUTPUT", b"-A FORWARD"), False,
                    "output_rule_missing")

    def test_unclosed_quote_before_valid_rule_fails_closed(self):
        raw = b'-A OUTPUT --path "unfinished\n' + rule()
        self.verify(raw, False, "rule_parse_error")

    def test_unclosed_quote_after_valid_rule_fails_closed(self):
        self.verify(rule() + b'-A OUTPUT -m comment --comment "unfinished\n',
                    False, "rule_parse_error")

    def test_invalid_utf8_preserves_hash_and_fails_closed(self):
        self.verify(b"\xff" + rule(), False, "source_not_utf8")

    def test_nul_is_rejected(self):
        self.verify(rule() + b"\x00", False, "source_contains_nul")

    def test_empty_expected_path_is_rejected(self):
        self.verify(rule(), False, "invalid_expectation", cgroup="")

    def test_expected_values_are_not_trimmed(self):
        self.verify(rule(), False, "invalid_expectation", chain=CHAIN + " ")

    def test_string_source_is_not_silently_encoded(self):
        self.verify(rule().decode(), False, "source_not_bytes")

    def test_ipv6_chain_uses_same_exact_verifier(self):
        self.verify(rule(chain="UTCS_RIG6_103238"), True, chain="UTCS_RIG6_103238")


class OutputRulesCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix=".output-rules-selftest-", dir=HERE)
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.output = self.root / "result.json"

    def call(self, source):
        return subprocess.run([
            sys.executable, "-B", str(MODULE), "--rules-file", str(source),
            "--expected-cgroup", CGROUP, "--expected-chain", CHAIN,
            "--output", str(self.output),
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)

    def test_cli_direct_replay_preserves_saved_source(self):
        before = FIXTURE.read_bytes()
        proc = self.call(FIXTURE)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertTrue(result["passed"])
        self.assertEqual(result["raw_sha256"], FIXTURE_SHA256)
        self.assertEqual(json.loads(self.output.read_bytes()), result)
        self.assertEqual(FIXTURE.read_bytes(), before)

    def test_cli_failure_exits_two_and_saves_error(self):
        source = self.root / "incorrect.rules"
        source.write_bytes(b"-A OUTPUT -j ACCEPT\n" + rule())
        proc = self.call(source)
        self.assertEqual(proc.returncode, 2)
        result = json.loads(self.output.read_bytes())
        self.assertFalse(result["passed"])
        self.assertEqual(result["errors"][0]["code"], "first_output_rule_mismatch")
        self.assertEqual(json.loads(proc.stdout), result)
        self.assertTrue(proc.stderr)

    def test_cli_never_overwrites_existing_output(self):
        preserved = b"existing evidence; must remain byte-identical\n"
        self.output.write_bytes(preserved)
        proc = self.call(FIXTURE)
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(self.output.read_bytes(), preserved)
        result = json.loads(proc.stdout)
        self.assertFalse(result["passed"])
        self.assertEqual(result["errors"][-1]["code"], "output_write_error")

    def test_cli_does_not_follow_output_symlink(self):
        target = self.root / "existing-target"
        target.write_bytes(b"keep\n")
        self.output.symlink_to(target)
        proc = self.call(FIXTURE)
        self.assertEqual(proc.returncode, 2)
        self.assertTrue(self.output.is_symlink())
        self.assertEqual(target.read_bytes(), b"keep\n")

    def test_cli_missing_source_saves_read_error(self):
        proc = self.call(self.root / "missing.rules")
        self.assertEqual(proc.returncode, 2)
        result = json.loads(self.output.read_bytes())
        self.assertIsNone(result["raw_sha256"])
        self.assertEqual(result["errors"][0]["code"], "source_read_error")

    def test_cli_source_cannot_be_overwritten_as_output(self):
        source = self.root / "source.rules"
        source.write_bytes(rule())
        self.output = source
        proc = self.call(source)
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(source.read_bytes(), rule())


if __name__ == "__main__":
    suite = unittest.TestSuite([
        unittest.defaultTestLoader.loadTestsFromTestCase(OutputRulesTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(OutputRulesCliTests),
    ])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {
        "scope": "saved stdout replay and synthetic local parser/CLI fixtures; no VM/network/Goose/model",
        "run": 0,
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "successful": result.wasSuccessful(),
        "fixture_sha256": hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
        "provenance_sha256": hashlib.sha256(PROVENANCE.read_bytes()).hexdigest(),
        "module_sha256": hashlib.sha256(MODULE.read_bytes()).hexdigest(),
        "selftest_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python_version": sys.version.split()[0],
    }
    print(json.dumps(report, indent=2))
    sys.exit(0 if result.wasSuccessful() else 1)
