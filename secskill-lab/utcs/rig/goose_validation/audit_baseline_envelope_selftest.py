#!/usr/bin/env python3
"""Pure offline fixtures; every firewall command is mocked, no VM/model/network."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
MODULE = HERE / "audit_baseline_envelope.py"
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("envelope_audit_under_test", MODULE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
CHAIN4, CHAIN6 = "UTCS_RIG4_TEST", "UTCS_RIG6_TEST"


def listing(chain=CHAIN4, rejected=3, rejected_bytes=None, accepted=10):
    if rejected_bytes is None:
        rejected_bytes = rejected * 60
    return (
        f"Chain {chain} (1 references)\n"
        "num pkts bytes target prot opt in out source destination\n"
        f"1 {accepted} {accepted * 60} ACCEPT tcp -- * lo 0.0.0.0/0 127.0.0.1 multiport dports 8000,4873,4874\n"
        f"2 {rejected} {rejected_bytes} REJECT all -- * * 0.0.0.0/0 0.0.0.0/0 reject-with icmp-admin-prohibited\n"
    ).encode()


def connect(address="127.0.0.1", port=8000, descriptor="7<TCP:[1001]>"):
    return (f'1789389000.123456 connect({descriptor}, {{sa_family=AF_INET, '
            f'sin_port=htons({port}), sin_addr=inet_addr("{address}")}}, 16) '
            '= -1 EINPROGRESS (Operation now in progress) <0.000010>\n').encode()


EXECVE = b'1789389000.100000 execve("/opt/goose", ["goose", "run"], 0x7fff0000 /* 30 vars */) = 0 <0.001000>\n'


class CounterTests(unittest.TestCase):
    def compare(self, first, second):
        return module.compare_reject_counters(module.parse_firewall_listing(first, CHAIN4),
                                              module.parse_firewall_listing(second, CHAIN4))

    def test_accept_growth_does_not_change_reject_delta(self):
        result = self.compare(listing(), listing(accepted=20))
        self.assertEqual(result["reject_packet_delta"], 0)
        self.assertEqual(result["errors"], [])

    def test_reject_growth_is_measured_exactly(self):
        result = self.compare(listing(), listing(rejected=7))
        self.assertEqual(result["reject_packet_delta"], 4)
        self.assertEqual(result["reject_byte_delta"], 240)

    def test_decreasing_counter_requires_review(self):
        result = self.compare(listing(), listing(rejected=0))
        self.assertTrue(any("decreased" in error for error in result["errors"]))

    def test_rule_replacement_is_not_hidden_by_equal_counts(self):
        altered = listing().replace(b"icmp-admin-prohibited", b"icmp-port-unreachable")
        result = self.compare(listing(), altered)
        self.assertIsNone(result["reject_packet_delta"])
        self.assertTrue(result["errors"])

    def test_wrong_chain_fails_closed(self):
        self.assertTrue(module.parse_firewall_listing(listing(CHAIN6), CHAIN4)["errors"])

    def test_abbreviated_counter_is_not_accepted(self):
        self.assertTrue(module.parse_firewall_listing(listing().replace(b"2 3 180", b"2 3K 180K"), CHAIN4)["errors"])

    def test_no_reject_row_fails_closed(self):
        self.assertTrue(module.parse_firewall_listing(listing().replace(b"REJECT", b"RETURN"), CHAIN4)["errors"])

    def test_noncontiguous_row_number_fails_closed(self):
        self.assertTrue(module.parse_firewall_listing(listing().replace(b"2 3 180", b"3 3 180"), CHAIN4)["errors"])

    def test_raw_hash_and_bytes_are_preserved(self):
        raw = listing()
        result = module.parse_firewall_listing(raw, CHAIN4)
        self.assertEqual(result["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(result["byte_count"], len(raw))


class TraceTests(unittest.TestCase):
    def inspect(self, raw):
        return module.inspect_trace(raw, "/synthetic/strace/goose.100")

    def codes(self, result):
        return [item["code"] for item in result["needs_manual_review"]]

    def test_tcp_loopback_connect_is_decoded(self):
        result = self.inspect(connect())
        self.assertEqual(result["needs_manual_review"], [])
        self.assertEqual(result["violations"], [])
        self.assertTrue(result["network_events"][0]["peers"][0]["allowed"])

    def test_all_three_explicit_allowed_ports(self):
        for port in (8000, 4873, 4874):
            with self.subTest(port=port):
                result = self.inspect(connect(port=port))
                self.assertEqual(result["violations"], [])
                self.assertEqual(result["needs_manual_review"], [])

    def test_other_loopback_port_is_reported(self):
        self.assertEqual(self.inspect(connect(port=22))["violations"][0]["code"], "peer_outside_allowlist")

    def test_nonloopback_peer_is_reported_without_contact(self):
        self.assertFalse(self.inspect(connect("192.0.2.1"))["network_events"][0]["peers"][0]["allowed"])

    def test_udp_is_not_mistaken_for_tcp(self):
        result = self.inspect(connect(descriptor="7<UDP:[1001]>"))
        self.assertEqual(result["network_events"][0]["peers"][0]["transport"], "UDP")
        self.assertTrue(result["violations"])

    def test_unknown_transport_requires_review(self):
        result = self.inspect(connect(descriptor="7"))
        self.assertIn("transport_unresolved", self.codes(result))

    def test_ipv6_sockaddr_is_reported(self):
        raw = (b'1789389000.123456 connect(7<TCPv6:[1001]>, {sa_family=AF_INET6, '
               b'sin6_port=htons(8000), inet_pton(AF_INET6, "::1", &sin6_addr), sin6_scope_id=0}, 28) = 0 <0.0001>\n')
        result = self.inspect(raw)
        self.assertEqual(result["network_events"][0]["peers"][0]["address"], "::1")
        self.assertTrue(result["violations"])

    def test_yy_peer_on_write_is_extracted(self):
        raw = b'1789389000.123456 write(7<TCP:[127.0.0.1:50000->127.0.0.1:8000]>, "hello", 5) = 5 <0.0001>\n'
        result = self.inspect(raw)
        self.assertEqual(result["needs_manual_review"], [])
        self.assertEqual(result["network_events"][0]["peers"][0]["origin"], "strace_yy_peer")

    def test_yy_ipv6_peer_is_parsed_without_being_allowed(self):
        raw = b'1789389000.123456 sendto(7<TCPv6:[[::1]:50000->[::1]:8000]>, "a", 1, 0, NULL, 0) = 1 <0.0001>\n'
        result = self.inspect(raw)
        self.assertEqual(result["network_events"][0]["peers"][0]["address"], "::1")
        self.assertTrue(result["violations"])

    def test_explicit_sendto_destination_is_extracted(self):
        raw = (b'1789389000.123456 sendto(7<UDP:[1001]>, "a", 1, 0, '
               b'{sa_family=AF_INET, sin_port=htons(4873), sin_addr=inet_addr("127.0.0.1")}, 16) = 1 <0.0001>\n')
        result = self.inspect(raw)
        self.assertEqual(len(result["network_events"][0]["peers"]), 1)
        self.assertTrue(result["violations"])

    def test_explicit_sendmsg_destination_is_extracted(self):
        raw = (b'1789389000.123456 sendmsg(7<TCP:[1001]>, {msg_name={sa_family=AF_INET, '
               b'sin_port=htons(4873), sin_addr=inet_addr("127.0.0.1")}, msg_namelen=16, '
               b'msg_iov=[{iov_base="a,b()", iov_len=5}], msg_iovlen=1, msg_controllen=0, msg_flags=0}, 0) = 5 <0.0001>\n')
        result = self.inspect(raw)
        self.assertEqual(result["needs_manual_review"], [])
        self.assertTrue(result["network_events"][0]["peers"][0]["allowed"])

    def test_sendmsg_null_name_uses_yy_peer(self):
        raw = (b'1789389000.123456 sendmsg(7<TCP:[127.0.0.1:50000->127.0.0.1:4874]>, '
               b'{msg_name=NULL, msg_namelen=0, msg_iov=[{iov_base="a", iov_len=1}], msg_iovlen=1}, 0) = 1 <0.0001>\n')
        self.assertEqual(self.inspect(raw)["needs_manual_review"], [])

    def test_unix_log_path_is_not_implicitly_approved(self):
        raw = b'1789389000.123456 connect(7<UNIX-STREAM:[1001]>, {sa_family=AF_UNIX, sun_path="/dev/log"}, 16) = 0 <0.0001>\n'
        self.assertIn("unreviewed_unix_destination", self.codes(self.inspect(raw)))

    def test_unix_socketpair_is_classified_only_as_local_ipc(self):
        raw = b'1789389000.123456 socketpair(AF_UNIX, SOCK_STREAM|SOCK_CLOEXEC, 0, [7<UNIX-STREAM:[10->11]>, 8<UNIX-STREAM:[11->10]>]) = 0 <0.0001>\n'
        result = self.inspect(raw)
        self.assertEqual(result["network_events"][0]["classification"], "local_unix_socketpair_ipc")
        self.assertEqual(result["needs_manual_review"], [])

    def test_unfinished_record_is_retained_for_review(self):
        raw = connect().replace(b") = -1 EINPROGRESS (Operation now in progress) <0.000010>\n", b" <unfinished ...>\n")
        result = self.inspect(raw)
        self.assertIn("network_or_exec_record_fragment", self.codes(result))
        self.assertEqual(result["network_events"][0]["raw"].encode(), raw)

    def test_resumed_record_is_not_declared_complete(self):
        raw = b'1789389000.123456 <... connect resumed>) = 0 <0.0001>\n'
        self.assertIn("network_or_exec_record_fragment", self.codes(self.inspect(raw)))

    def test_payload_truncation_requires_review(self):
        raw = b'1789389000.123456 write(7<TCP:[127.0.0.1:50000->127.0.0.1:8000]>, "short"..., 10000) = 10000 <0.0001>\n'
        self.assertIn("truncated_or_undecoded_record", self.codes(self.inspect(raw)))

    def test_literal_payload_ellipsis_does_not_fake_truncation(self):
        raw = b'1789389000.123456 write(7<TCP:[127.0.0.1:50000->127.0.0.1:8000]>, "...", 3) = 3 <0.0001>\n'
        self.assertEqual(self.inspect(raw)["needs_manual_review"], [])

    def test_payload_cannot_inject_an_observed_peer(self):
        raw = b'1789389000.123456 write(1</local/stdout>, "connect(7<TCP:[192.0.2.2:55->192.0.2.1:8000]>)", 56) = 56 <0.0001>\n'
        self.assertEqual(self.inspect(raw)["network_events"], [])

    def test_pointer_destination_requires_review(self):
        raw = b'1789389000.123456 connect(7<TCP:[1001]>, 0x7fff0000, 16) = -1 EFAULT <0.0001>\n'
        self.assertIn("unparsed_destination", self.codes(self.inspect(raw)))

    def test_unclosed_network_record_requires_review(self):
        raw = b'1789389000.123456 connect(7<TCP:[1001]>, {sa_family=AF_INET\n'
        self.assertIn("unclosed_or_unparsed_record", self.codes(self.inspect(raw)))

    def test_hostname_peer_is_not_resolved_over_network(self):
        raw = b'1789389000.123456 write(7<TCP:[127.0.0.1:50000->backend.local:8000]>, "a", 1) = 1 <0.0001>\n'
        self.assertIn("unparsed_socket_peer", self.codes(self.inspect(raw)))

    def test_undecoded_send_without_peer_is_not_silently_allowed(self):
        raw = b'1789389000.123456 send(7, "a", 1, 0) = 1 <0.0001>\n'
        self.assertIn("outbound_peer_unresolved", self.codes(self.inspect(raw)))

    def test_local_address_operation_is_listed_for_manual_interpretation(self):
        raw = b'1789389000.123456 getsockname(7<TCP:[1001]>, {sa_family=AF_INET, sin_port=htons(50000), sin_addr=inet_addr("127.0.0.1")}, [16]) = 0 <0.0001>\n'
        self.assertIn("address_outside_bounded_extractor", self.codes(self.inspect(raw)))

    def test_execve_and_execveat_are_retained(self):
        raw = EXECVE + b'1789389000.200000 execveat(AT_FDCWD, "/opt/node", ["node"], 0x7fff0000, 0) = 0 <0.001>\n'
        result = self.inspect(raw)
        self.assertEqual([event["syscall"] for event in result["execve_events"]], ["execve", "execveat"])
        self.assertEqual(result["execve_events"][0]["raw"].encode(), EXECVE)

    def test_invalid_trace_encoding_requires_review(self):
        self.assertIn("trace_not_utf8", self.codes(self.inspect(connect() + b"\xff\n")))


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix=".envelope-audit-selftest-", dir=HERE)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.stage = self.root / "stage"
        self.control = self.stage / "control"
        self.control.mkdir(parents=True)
        self.trace_dir = self.stage / "strace"
        self.trace_dir.mkdir()
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        self.output = self.stage / "audit.json"
        self.calls = []
        (self.control / "network-controls-result.json").write_text(json.dumps({
            "status": "passed", "chain4": CHAIN4, "chain6": CHAIN6}))
        for tool, chain in (("iptables", CHAIN4), ("ip6tables", CHAIN6)):
            (self.control / (tool + "-before-goose.txt")).write_bytes(listing(chain))
        (self.trace_dir / "goose.100").write_bytes(EXECVE + connect())
        self.no_real_commands = patch.object(module.subprocess, "run", side_effect=AssertionError("real command forbidden in selftest"))
        self.no_real_commands.start()
        self.addCleanup(self.no_real_commands.stop)

    def fake(self, argv, **kwargs):
        self.calls.append(argv)
        tool = argv[2]
        chain = CHAIN4 if tool == "iptables" else CHAIN6
        self.assertEqual(argv, ["sudo", "-n", tool, "-L", chain, "-n", "-v", "-x", "--line-numbers"])
        self.assertNotIn("shell", kwargs)
        return SimpleNamespace(stdout=listing(chain, accepted=20), stderr=b"", returncode=0)

    def collect(self, runner=None):
        return module.collect_audit(self.stage, self.workspace, runner or self.fake)

    def cli(self, runner=None):
        with patch.object(module.subprocess, "run", side_effect=runner or self.fake), contextlib.redirect_stdout(io.StringIO()) as out:
            code = module.main(["--stage", str(self.stage), "--workspace", str(self.workspace), "--output", str(self.output)])
        return code, json.loads(out.getvalue())

    def test_clean_auxiliary_scope_preserves_raw_snapshots(self):
        record = self.collect()
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(record["summary"]["cgroup_reject_packet_deltas"], {"iptables": 0, "ip6tables": 0})
        self.assertEqual(record["needs_manual_review"], [])
        self.assertEqual(record["errors"], [])
        self.assertEqual(record["violations"], [])
        self.assertTrue(record["summary"]["workspace_unchanged"])
        self.assertTrue(record["summary"]["manual_readthrough_required"])
        self.assertEqual((self.control / "iptables-after-envelope.txt").read_bytes(), listing(CHAIN4, accepted=20))

    def test_nested_workspace_entries_are_reported(self):
        (self.workspace / "nested").mkdir()
        (self.workspace / "nested/file").write_bytes(b"marker")
        record = self.collect()
        self.assertFalse(record["summary"]["workspace_unchanged"])
        self.assertEqual([entry["path"] for entry in record["workspace"]["entries"]], ["nested", "nested/file"])

    def test_workspace_symlink_is_not_followed(self):
        (self.root / "outside").mkdir()
        (self.root / "outside/private").write_bytes(b"not read")
        (self.workspace / "link").symlink_to(self.root / "outside", target_is_directory=True)
        record = self.collect()
        self.assertEqual([entry["path"] for entry in record["workspace"]["entries"]], ["link"])
        self.assertEqual(record["workspace"]["entries"][0]["kind"], "symlink")

    def test_reject_growth_is_a_reported_anomaly(self):
        def runner(argv, **kwargs):
            result = self.fake(argv, **kwargs)
            result.stdout = listing(argv[4], rejected=4)
            return result
        record = self.collect(runner)
        self.assertEqual(record["summary"]["cgroup_reject_packet_deltas"], {"iptables": 1, "ip6tables": 1})
        self.assertEqual([row["code"] for row in record["violations"]], ["reject_counter_increased"] * 2)

    def test_snapshot_command_error_is_preserved(self):
        def runner(argv, **kwargs):
            result = self.fake(argv, **kwargs)
            result.returncode = 1
            result.stderr = b"synthetic permission error\n"
            return result
        record = self.collect(runner)
        self.assertEqual(len(record["errors"]), 2)
        self.assertEqual((self.control / "iptables-after-envelope.stderr.txt").read_bytes(), b"synthetic permission error\n")

    def test_timeout_partial_output_is_preserved(self):
        def runner(argv, **kwargs):
            raise subprocess.TimeoutExpired(argv, 20, output=b"partial\n", stderr=b"timeout\n")
        record = self.collect(runner)
        self.assertEqual(len(record["errors"]), 2)
        self.assertEqual((self.control / "iptables-after-envelope.txt").read_bytes(), b"partial\n")
        self.assertTrue(record["firewall"]["iptables"]["command"]["timed_out"])

    def test_existing_snapshot_is_never_overwritten_or_requeried(self):
        path = self.control / "iptables-after-envelope.txt"
        path.write_bytes(b"previous evidence\n")
        record = self.collect()
        self.assertEqual(path.read_bytes(), b"previous evidence\n")
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0][2], "ip6tables")
        self.assertTrue(record["errors"])

    def test_invalid_chain_option_does_not_execute_a_command(self):
        (self.control / "network-controls-result.json").write_text(json.dumps({"status": "passed", "chain4": "-F", "chain6": CHAIN6}))
        self.assertTrue(self.collect()["errors"])
        self.assertEqual(self.calls, [])

    def test_missing_trace_cannot_be_reported_as_complete(self):
        (self.trace_dir / "goose.100").unlink()
        record = self.collect()
        self.assertIn("strace_sources_missing", [row["code"] for row in record["needs_manual_review"]])

    def test_cli_success_keeps_human_review_required(self):
        code, printed = self.cli()
        self.assertEqual(code, 0)
        self.assertTrue(printed["summary"]["manual_readthrough_required"])
        self.assertEqual(printed["output_sha256"], hashlib.sha256(self.output.read_bytes()).hexdigest())

    def test_cli_review_items_exit_two_and_remain_in_saved_json(self):
        (self.trace_dir / "goose.100").write_bytes(EXECVE + connect(descriptor="7"))
        code, printed = self.cli()
        self.assertEqual(code, 2)
        self.assertTrue(json.loads(self.output.read_bytes())["needs_manual_review"])
        self.assertEqual(printed["exit_code"], 2)

    def test_cli_existing_output_prevents_all_commands(self):
        self.output.write_bytes(b"retain\n")
        code, _ = self.cli()
        self.assertEqual(code, 2)
        self.assertEqual(self.output.read_bytes(), b"retain\n")
        self.assertEqual(self.calls, [])

    def test_cli_refuses_to_write_evidence_inside_workspace(self):
        self.output = self.workspace / "audit.json"
        code, _ = self.cli()
        self.assertEqual(code, 2)
        self.assertFalse(self.output.exists())
        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(cls)
                               for cls in (CounterTests, TraceTests, AuditTests))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({
        "scope": "pure offline trace/listing fixtures and mocked command collection; no VM/iptables/network/Goose/model",
        "run": 0, "tests_run": result.testsRun, "failures": len(result.failures),
        "errors": len(result.errors), "successful": result.wasSuccessful(),
        "module_sha256": hashlib.sha256(MODULE.read_bytes()).hexdigest(),
        "selftest_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python_version": sys.version.split()[0],
    }, indent=2))
    sys.exit(0 if result.wasSuccessful() else 1)
