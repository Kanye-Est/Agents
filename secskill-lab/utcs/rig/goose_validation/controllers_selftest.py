#!/usr/bin/env python3
"""Offline controller checks; no sudo, sockets, systemd, Goose or model calls."""
import base64
import contextlib
import hashlib
import io
import json
import pathlib
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

sys.dont_write_bytecode = True
# Import must be inert: a CLI import must never start an operation.
with patch("subprocess.run", side_effect=AssertionError("import performed a command")), \
     patch("subprocess.Popen", side_effect=AssertionError("import started a process")):
    import prepare_controls as prepare
    import launch_baseline as launch

HERE = pathlib.Path(__file__).resolve().parent


class Process:
    def __init__(self, code=None):
        self.returncode = code

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        self.returncode = 0
        return 0


class ControllersTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="utcs-controller-offline-")
        self.root = pathlib.Path(self.tmp.name)
        self.control = self.root / "control"
        self.control.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def controller(self):
        value = object.__new__(launch.LaunchController)
        value.stage = self.root
        value.control = self.control
        value.cgpath = self.root / "cgroup"
        value.unit = "synthetic-baseline.service"
        value.capture = Process()
        value.watcher = Process()
        value.capture_pid = 1234
        value.capture_ready = {"ready_ns": 10}
        value.watch_ready = {"ready_ns": 9}
        value.capture_end = value.watch_result = None
        value.released = False
        value.commands = types.SimpleNamespace(run=Mock(return_value=subprocess.CompletedProcess([], 0, b"", b"")))
        return value

    def manifest(self):
        source = self.root / "source"
        source.mkdir()
        for name in ("a.py", "helper.sh", "template.jinja", "readme.md"):
            (source / name).write_bytes((name + "\r\n").encode())
        manifest = source / "SHA256SUMS"
        manifest.write_text("".join(f"{prepare.sha(p)}  {p.name}\n" for p in sorted(source.iterdir())))
        return source, manifest

    def osv(self, listener=None, ready_pid=71270, state_pid=71270, actual_source=b"frozen OSV helper\n"):
        old_stage = self.root / "old"
        old_control = old_stage / "control"
        old_control.mkdir(parents=True)
        source = old_control / "osv_unavailable.py"
        source.write_bytes(actual_source)
        ready = old_control / "osv-ready.json"
        ready.write_text(json.dumps({"pid": ready_pid, "bind": ["127.0.0.1", 4874],
                                    "response_status": 503, "no_upstream_requests": True}))
        proc = self.root / "proc" / "71270"
        proc.mkdir(parents=True)
        (proc / "cmdline").write_bytes(b"\0".join(x.encode() for x in ["/usr/bin/python3", str(source), "--stage", str(old_stage)]) + b"\0")
        (proc / "cgroup").write_text("0::/system.slice/existing-osv.service\n")
        state = (f"LoadState=loaded\nActiveState=active\nSubState=running\nMainPID={state_pid}\n"
                 "ControlGroup=/system.slice/existing-osv.service\n").encode()
        if listener is None:
            listener = b'LISTEN 0 5 127.0.0.1:4874 0.0.0.0:* users:(("python3",pid=71270,fd=4))\n'
        commands = types.SimpleNamespace(run=Mock(side_effect=[
            subprocess.CompletedProcess([], 0, state, b""),
            subprocess.CompletedProcess([], 0, listener, b""),
        ]))
        manifest = {"sources": [{"relative_path": "osv_unavailable.py",
                                 "sha256": hashlib.sha256(b"frozen OSV helper\n").hexdigest()}]}
        return commands, ready, manifest, self.root / "proc"

    def test_atomic_new_bytes_preserves_exact_raw(self):
        path = self.control / "rules.txt"
        raw = b"-P OUTPUT ACCEPT\r\n\x00\xff"
        prepare.new_bytes(path, raw)
        self.assertEqual(path.read_bytes(), raw)

    def test_atomic_new_bytes_never_overwrites(self):
        path = self.control / "prior.txt"
        path.write_bytes(b"old")
        with self.assertRaises(FileExistsError):
            prepare.new_bytes(path, b"new")
        self.assertEqual(path.read_bytes(), b"old")
        self.assertEqual(sorted(p.name for p in self.control.iterdir()), ["prior.txt"])

    def test_precreated_logs_owned_and_exclusive(self):
        path = self.control / "gate.stdout.log"
        prepare.precreate_logs([path])
        self.assertEqual(path.stat().st_uid, prepare.os.geteuid())
        path.write_bytes(b"prior evidence")
        with self.assertRaises(FileExistsError):
            prepare.precreate_logs([path])
        self.assertEqual(path.read_bytes(), b"prior evidence")

    def test_existing_control_cannot_be_reused(self):
        path = self.control / "old"
        path.write_bytes(b"keep")
        with self.assertRaises(FileExistsError):
            prepare.PrepareController(types.SimpleNamespace(stage=str(self.root)))
        self.assertEqual(path.read_bytes(), b"keep")
        self.assertFalse((self.control / "prepare-commands.jsonl").exists())

    def test_manifest_valid_all_code_and_support(self):
        source, manifest = self.manifest()
        result = prepare.verify_source_manifest(manifest, source)
        self.assertEqual(len(result["sources"]), 4)
        self.assertEqual(result["manifest_sha256"], prepare.sha(manifest))

    def test_manifest_changed_code_fails(self):
        source, manifest = self.manifest()
        (source / "a.py").write_bytes(b"changed")
        with self.assertRaisesRegex(RuntimeError, "hash mismatch"):
            prepare.verify_source_manifest(manifest, source)

    def test_manifest_omitted_nested_helper_fails(self):
        source, manifest = self.manifest()
        (source / "nested").mkdir()
        (source / "nested/helper.py").write_text("new helper")
        with self.assertRaisesRegex(RuntimeError, "omits helper code"):
            prepare.verify_source_manifest(manifest, source)

    def test_manifest_duplicate_fails(self):
        source, manifest = self.manifest()
        text = manifest.read_text()
        manifest.write_text(text + text.splitlines()[0] + "\n")
        with self.assertRaisesRegex(RuntimeError, "duplicate"):
            prepare.verify_source_manifest(manifest, source)

    def test_manifest_parent_escape_fails(self):
        source, manifest = self.manifest()
        outside = self.root / "outside.py"
        outside.write_text("outside")
        manifest.write_text(manifest.read_text() + f"{prepare.sha(outside)}  ../outside.py\n")
        with self.assertRaisesRegex(RuntimeError, "outside source"):
            prepare.verify_source_manifest(manifest, source)

    def test_manifest_absolute_path_fails(self):
        source, manifest = self.manifest()
        path = source / "a.py"
        manifest.write_text(f"{prepare.sha(path)}  {path}\n")
        with self.assertRaisesRegex(RuntimeError, "outside source"):
            prepare.verify_source_manifest(manifest, source)

    def test_manifest_symlink_outside_fails(self):
        source, manifest = self.manifest()
        outside = self.root / "outside.py"
        outside.write_text("outside")
        (source / "link.py").symlink_to(outside)
        manifest.write_text(manifest.read_text() + f"{prepare.sha(outside)}  link.py\n")
        with self.assertRaisesRegex(RuntimeError, "in-tree file"):
            prepare.verify_source_manifest(manifest, source)

    def test_manifest_self_reference_fails(self):
        source, manifest = self.manifest()
        manifest.write_text(manifest.read_text() + "0" * 64 + "  SHA256SUMS\n")
        with self.assertRaisesRegex(RuntimeError, "include itself"):
            prepare.verify_source_manifest(manifest, source)

    def test_command_output_bytes_and_failure_preserved_once(self):
        path = self.control / "command.jsonl"
        command = prepare.CommandLog(path)
        raw, error = b"\xff\x00\r\n", b"original error\r\n"
        with patch.object(prepare.subprocess, "run", return_value=subprocess.CompletedProcess(["synthetic"], 7, raw, error)) as call:
            with self.assertRaisesRegex(RuntimeError, "original error"):
                command.run(["synthetic"])
        command.close()
        self.assertEqual(call.call_count, 1)
        self.assertNotIn("text", call.call_args.kwargs)
        record = json.loads(path.read_bytes())
        self.assertEqual(base64.b64decode(record["stdout_base64"]), raw)
        self.assertEqual(base64.b64decode(record["stderr_base64"]), error)
        self.assertEqual(record["stdout_sha256"], hashlib.sha256(raw).hexdigest())

    def test_real_saved_rule_bytes_use_same_runtime_parser(self):
        raw = (HERE / "tests/fixtures/iptables-output-before.txt").read_bytes()
        self.assertIs(prepare.output_rules.verify_output_rules, launch.output_rules.verify_output_rules)
        result = prepare.output_rules.verify_output_rules(raw, "system.slice/utcs-rig-ta-20260914-103238.service", "UTCS_RIG4_103238")
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["raw_sha256"], "3ee5279a5a81057f9733f0f1c04cc91256e032ef5d3ae81807cbbb6b4d87b55c")
        self.assertEqual(result["raw_byte_count"], len(raw))

    def test_real_saved_rule_rejects_wrong_cgroup(self):
        raw = (HERE / "tests/fixtures/iptables-output-before.txt").read_bytes()
        self.assertFalse(launch.output_rules.verify_output_rules(raw, "system.slice/another.service", "UTCS_RIG4_103238")["passed"])

    def test_osv_reuse_checks_proc_source_and_never_restarts(self):
        commands, ready, manifest, proc_root = self.osv()
        before = ready.read_bytes()
        result = prepare.verify_osv_reuse(commands, self.control, ready, "existing-osv.service", 71270, manifest, proc_root)
        self.assertTrue(result["reused"])
        self.assertFalse(result["restarted"])
        self.assertEqual(ready.read_bytes(), before)
        for call in commands.run.call_args_list:
            argv = call.args[0]
            self.assertNotIn("systemd-run", argv)
            self.assertNotIn("stop", argv)
            self.assertNotIn("restart", argv)

    def test_osv_source_hash_mismatch_stops(self):
        commands, ready, manifest, proc_root = self.osv(actual_source=b"changed helper")
        with self.assertRaisesRegex(RuntimeError, "source differs"):
            prepare.verify_osv_reuse(commands, self.control, ready, "existing-osv.service", 71270, manifest, proc_root)
        self.assertFalse((self.control / "osv-reuse-verification.json").exists())

    def test_osv_ready_pid_mismatch_stops(self):
        commands, ready, manifest, proc_root = self.osv(ready_pid=1)
        with self.assertRaisesRegex(RuntimeError, "ready PID mismatch"):
            prepare.verify_osv_reuse(commands, self.control, ready, "existing-osv.service", 71270, manifest, proc_root)
        commands.run.assert_not_called()

    def test_osv_systemd_pid_mismatch_stops(self):
        commands, ready, manifest, proc_root = self.osv(state_pid=2)
        with self.assertRaisesRegex(RuntimeError, "recorded running PID"):
            prepare.verify_osv_reuse(commands, self.control, ready, "existing-osv.service", 71270, manifest, proc_root)

    def test_osv_wildcard_listener_stops(self):
        listener = b'LISTEN 0 5 0.0.0.0:4874 0.0.0.0:* users:(("python3",pid=71270,fd=4))\n'
        commands, ready, manifest, proc_root = self.osv(listener=listener)
        with self.assertRaisesRegex(RuntimeError, "solely 127.0.0.1"):
            prepare.verify_osv_reuse(commands, self.control, ready, "existing-osv.service", 71270, manifest, proc_root)

    def test_osv_extra_ipv6_listener_stops(self):
        listener = (b'LISTEN 0 5 127.0.0.1:4874 0.0.0.0:* users:(("python3",pid=71270,fd=4))\n'
                    b'LISTEN 0 5 [::]:4874 [::]:* users:(("python3",pid=71270,fd=5))\n')
        commands, ready, manifest, proc_root = self.osv(listener=listener)
        with self.assertRaisesRegex(RuntimeError, "solely 127.0.0.1"):
            prepare.verify_osv_reuse(commands, self.control, ready, "existing-osv.service", 71270, manifest, proc_root)

    def test_service_env_quotes_are_data_not_shell(self):
        path = self.root / "service.env"
        path.write_text('GOOSE_PATH_ROOT="/old path/profile"\nTOKEN=\'$(never execute)\'\nEMPTY=\n# comment\n')
        result = launch.read_service_env(path)
        self.assertEqual(result["GOOSE_PATH_ROOT"], "/old path/profile")
        self.assertEqual(result["TOKEN"], "$(never execute)")
        self.assertEqual(result["EMPTY"], "")
        self.assertEqual(result["PYTHONDONTWRITEBYTECODE"], "1")

    def test_service_env_duplicate_stops(self):
        path = self.root / "service.env"
        path.write_text("KEY=a\nKEY=b\n")
        with self.assertRaisesRegex(RuntimeError, "duplicate"):
            launch.read_service_env(path)

    def test_tree_drain_checks_descendants_even_if_root_has_no_pids(self):
        cg = self.root / "cg"
        (cg / "child").mkdir(parents=True)
        (cg / "cgroup.procs").write_text("")
        (cg / "child/cgroup.procs").write_text("4321\n")
        (cg / "cgroup.events").write_text("populated 1\nfrozen 0\n")
        self.assertFalse(launch.tree_empty(cg))
        (cg / "cgroup.events").write_text("populated 0\nfrozen 0\n")
        self.assertTrue(launch.tree_empty(cg))

    def test_tree_without_events_is_not_assumed_empty(self):
        cg = self.root / "cg"
        cg.mkdir()
        self.assertFalse(launch.tree_empty(cg))
        self.assertTrue(launch.tree_empty(self.root / "absent"))

    def test_capture_and_watcher_alive(self):
        controller = self.controller()
        controller.require_capture_alive("synthetic-before-release")

    def test_tcpdump_zero_early_exit_rejected(self):
        controller = self.controller()
        controller.capture.returncode = 0
        with self.assertRaisesRegex(RuntimeError, "Premature tcpdump"):
            controller.require_capture_alive("synthetic-during-Goose")

    def test_watcher_zero_early_exit_rejected(self):
        controller = self.controller()
        controller.watcher.returncode = 0
        with self.assertRaisesRegex(RuntimeError, "Premature watcher"):
            controller.require_capture_alive("synthetic-during-Goose")

    def test_stop_capture_zero_early_exit_never_attests_completion(self):
        controller = self.controller()
        controller.capture.returncode = 0
        with self.assertRaisesRegex(RuntimeError, "including exit code 0"):
            controller.stop_capture()
        record = json.loads((self.control / "capture-finished.json").read_bytes())
        self.assertTrue(record["premature_exit"])
        self.assertIsNone(record["finished_ns"])
        controller.commands.run.assert_not_called()

    def test_stop_capture_nonzero_early_exit_preserved(self):
        controller = self.controller()
        controller.capture.returncode = 23
        with self.assertRaisesRegex(RuntimeError, "Premature"):
            controller.stop_capture()
        self.assertEqual(json.loads((self.control / "capture-finished.json").read_bytes())["exit_code"], 23)

    def test_stop_capture_only_signals_verified_pid(self):
        controller = self.controller()
        cmdline = b"tcpdump\0-w\0" + str(self.root / "model-api.pcap").encode() + b"\0"
        with patch.object(pathlib.Path, "read_bytes", return_value=cmdline):
            controller.stop_capture()
        controller.commands.run.assert_called_once_with(["sudo", "-n", "kill", "-INT", "1234"])
        self.assertEqual(controller.capture_end["exit_code"], 0)
        self.assertGreater(controller.capture_end["finished_ns"], 10)

    def test_undrained_failure_keeps_capture_and_original_error(self):
        controller = self.controller()
        controller.released = True
        controller.stop_capture = Mock()
        controller.stop_watcher = Mock()
        with patch.object(launch, "tree_empty", return_value=False), \
             patch.object(launch.time, "monotonic", side_effect=[0, 16]), \
             contextlib.redirect_stdout(io.StringIO()):
            controller.handle_failure(RuntimeError("original failure"), "original traceback")
        controller.stop_capture.assert_not_called()
        controller.stop_watcher.assert_not_called()
        controller.commands.run.assert_called_once_with(["sudo", "-n", "systemctl", "stop", controller.unit], check=False)
        record = json.loads((self.control / "baseline-execution-error.json").read_bytes())
        self.assertEqual(record["error"], "original failure")
        self.assertEqual(record["traceback"], "original traceback")
        self.assertIn("capture_left_running", record)
        self.assertTrue(record["no_retry"])

    def test_drained_failure_stops_instrumentation_once(self):
        controller = self.controller()
        controller.released = True
        controller.stop_capture = Mock()
        controller.stop_watcher = Mock()
        with patch.object(launch, "tree_empty", return_value=True), contextlib.redirect_stdout(io.StringIO()):
            controller.handle_failure(RuntimeError("original failure"), "original traceback")
        controller.stop_capture.assert_called_once_with()
        controller.stop_watcher.assert_called_once_with()
        self.assertTrue((self.control / "abort").exists())

    def test_manifest_change_must_not_be_masked_by_output_rules(self):
        source, manifest = self.manifest()
        (source / "helper.sh").write_text("changed after preparation")
        with self.assertRaisesRegex(RuntimeError, "hash mismatch"):
            launch.verify_source_manifest(manifest, source)

    def test_inactive_wrapper_without_completion_stops(self):
        with self.assertRaisesRegex(RuntimeError, "ActiveState=inactive"):
            launch.require_wrapper_running_or_finished("ActiveState=inactive\nSubState=dead\n", False)

    def test_exited_wrapper_without_completion_stops(self):
        with self.assertRaisesRegex(RuntimeError, "SubState=exited"):
            launch.require_wrapper_running_or_finished("ActiveState=active\nSubState=exited\n", False)

    def test_completion_publication_race_is_accepted(self):
        launch.require_wrapper_running_or_finished("ActiveState=active\nSubState=exited\n", True)

    def test_prepared_inputs_detect_environment_and_workspace_changes(self):
        workspace = self.root / "workspace"
        workspace.mkdir()
        env, binary, config = (self.root / name for name in ("service.env", "goose", "config.yaml"))
        for path in (env, binary, config):
            path.write_bytes(b"frozen")
        args = types.SimpleNamespace(workspace=str(workspace), service_env=str(env), goose_bin=str(binary), config=str(config))
        original = prepare.prepared_inputs(args)
        env.write_bytes(b"changed")
        self.assertNotEqual(original, prepare.prepared_inputs(args))
        env.write_bytes(b"frozen")
        other = self.root / "different-workspace"
        other.mkdir()
        args.workspace = str(other)
        self.assertNotEqual(original, prepare.prepared_inputs(args))


if __name__ == "__main__":
    unittest.main(verbosity=2)
