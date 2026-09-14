#!/usr/bin/env python3
"""Release one prepared T-A baseline, with capture alive until its cgroup drains.

Use repository helpers and the original --freeze-dir / --config-record. All
new evidence stays beneath --stage. OUTPUT --path is cgroup-root-relative.
A failed or completed invocation is never retried by this controller.
"""
import argparse
import json
import os
import pathlib
import re
import shlex
import sqlite3
import subprocess
import sys
import time
import traceback

sys.dont_write_bytecode = True
import yaml
import output_rules
from prepare_controls import (
    HERE, CommandLog, mark_abort, new_bytes, precreate_logs, prepared_inputs, require, sha,
    systemd_state, verify_frozen_baseline, verify_osv_reuse,
    verify_source_manifest, write_json,
)


def tree_empty(cgpath):
    """Kernel populated includes the cgroup and all its descendant cgroups."""
    try:
        fields = dict(line.split() for line in (cgpath / "cgroup.events").read_text().splitlines())
    except FileNotFoundError:
        return not cgpath.exists()
    return fields.get("populated") == "0"


def require_wrapper_running_or_finished(raw, finished_exists):
    state = dict(line.split("=", 1) for line in raw.splitlines() if "=" in line)
    require(finished_exists or (state.get("ActiveState") == "active" and state.get("SubState") == "running"),
            "Wrapper left active/running before completion record: " + raw)


def read_service_env(path):
    """Read the frozen single-line assignments without executing a shell."""
    result = {}
    for number, line in enumerate(pathlib.Path(path).read_text().splitlines(), 1):
        if not line.strip() or line.lstrip().startswith(("#", ";")):
            continue
        fields = shlex.split(line, comments=False, posix=True)
        require(len(fields) == 1 and "=" in fields[0], f"Unsupported service environment syntax at line {number}")
        key, value = fields[0].split("=", 1)
        require(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key) is not None and key not in result,
                f"Invalid or duplicate environment key at line {number}")
        result[key] = value
    result["PYTHONDONTWRITEBYTECODE"] = "1"
    return result


class LaunchController:
    def __init__(self, args):
        self.args = args
        self.stage = pathlib.Path(args.stage).resolve(strict=True)
        self.control = self.stage / "control"
        self.profile = pathlib.Path(args.profile).resolve(strict=True)
        self.network = json.loads((self.control / "network-controls-result.json").read_bytes())
        self.unit = self.network["unit"]
        self.cgpath = pathlib.Path("/sys/fs/cgroup") / self.network["cgroup"].lstrip("/")
        self.commands = CommandLog(self.control / "launch-commands.jsonl")
        self.watcher = self.capture = self.capture_pid = None
        self.capture_ready = self.watch_ready = self.goose_end = None
        self.capture_end = self.watch_result = None
        self.released = False

    def require_capture_alive(self, phase):
        for name, process in (("tcpdump", self.capture), ("watcher", self.watcher)):
            if process is None or process.poll() is not None:
                raise RuntimeError("Premature " + name + " exit at " + phase)

    def wait_file(self, path, seconds=30, process=None):
        path = pathlib.Path(path)
        deadline = time.monotonic() + seconds
        while not path.exists() or not path.stat().st_size:
            if process is not None and process.poll() is not None:
                raise RuntimeError("Process exited before readiness: " + str(path))
            if time.monotonic() > deadline:
                raise TimeoutError(str(path))
            time.sleep(.1)
        return path

    def stop_capture(self):
        if self.capture is None or self.capture_end is not None:
            return
        if self.capture.poll() is not None:
            self.capture_end = {
                "ready_ns": self.capture_ready["ready_ns"] if self.capture_ready else None,
                "finished_ns": None, "observed_exit_ns": time.time_ns(),
                "exit_code": self.capture.returncode, "pid": self.capture_pid, "premature_exit": True,
                "meaning": "Exact early exit time is unknown; do not attest a complete capture window.",
            }
            write_json(self.control / "capture-finished.json", self.capture_end)
            raise RuntimeError("Premature tcpdump exit, including exit code 0, invalidates capture coverage")
        require(self.capture_pid is not None, "Cannot stop an unidentified capture process")
        cmdline = (pathlib.Path("/proc") / str(self.capture_pid) / "cmdline").read_bytes()
        require(b"tcpdump" in cmdline and str(self.stage / "model-api.pcap").encode() in cmdline,
                "Capture PID identity changed")
        self.commands.run(["sudo", "-n", "kill", "-INT", str(self.capture_pid)])
        code = self.capture.wait(timeout=15)
        self.capture_end = {
            "ready_ns": self.capture_ready["ready_ns"] if self.capture_ready else None,
            "finished_ns": time.time_ns(), "exit_code": code, "pid": self.capture_pid,
            "pcap": str(self.stage / "model-api.pcap"), "stderr": str(self.stage / "tcpdump.stderr.log"),
        }
        write_json(self.control / "capture-finished.json", self.capture_end)

    def stop_watcher(self):
        if self.watcher is None or self.watch_result is not None:
            return
        premature = self.watcher.poll() is not None
        new_bytes(self.control / "watcher.stop", b"cgroup drained or baseline unreleased\n")
        code = self.watcher.wait(timeout=15)
        result_path = self.control / "watcher-result.json"
        if result_path.exists():
            self.watch_result = json.loads(result_path.read_bytes())
            require(self.watch_result["exit_code"] == code, "Watcher exit record mismatch")
        else:
            self.watch_result = {
                "ready_ns": self.watch_ready.get("ready_ns") if self.watch_ready else None,
                "finished_ns": time.time_ns(), "exit_code": code, "errors": ["watcher result missing"],
            }
        write_json(self.control / "watcher-process-finished.json",
                   {"exit_code": code, "finished_ns": time.time_ns(), "premature_exit": premature})
        require(not premature, "Premature watcher exit invalidates capture coverage")

    def verify_committed_sources(self, manifest):
        repo = pathlib.Path(self.args.repo).resolve(strict=True)
        relative = HERE.relative_to(repo).as_posix()
        prefix = ["git", "-C", str(repo)]
        status = self.commands.run(prefix + ["status", "--porcelain=v1", "--untracked-files=all", "--", relative]).stdout
        require(status == b"", "Instrumentation source tree is not committed and clean: " + status.decode(errors="replace"))
        tracked = [str(pathlib.Path(relative) / row["relative_path"]) for row in manifest["sources"]]
        tracked.append(pathlib.Path(manifest["manifest"]).relative_to(repo).as_posix())
        self.commands.run(prefix + ["ls-files", "--error-unmatch", "--", *tracked])
        commit = self.commands.run(prefix + ["rev-parse", "HEAD"]).stdout.decode().strip()
        require(re.fullmatch(r"[0-9a-f]{40,64}", commit) is not None, "Invalid source commit")
        return commit

    def execute(self):
        a, stage, control, network = self.args, self.stage, self.control, self.network
        run = self.commands.run
        require(network["status"] == "passed" and network["goose_started"] is False, "Network controls not passed")
        require(not any((control / n).exists() for n in ("abort", "goose.release", "goose-start.json", "gate-error.json")),
                "Stale or failed baseline stage; no automatic retry")
        require(self.cgpath.stat().st_ino == network["cgroup_inode"], "Baseline cgroup inode changed")
        require((pathlib.Path("/proc") / str(network["main_pid"]) / "cgroup").read_text().strip() == "0::" + network["cgroup"],
                "Baseline PID cgroup changed")
        current = systemd_state(self.commands, self.unit)
        require(current["ActiveState"] == "active" and int(current["MainPID"]) == network["main_pid"]
                and current["ControlGroup"] == network["cgroup"], "Baseline unit identity/state changed")
        require(current["Delegate"] == "no" and current["NoNewPrivileges"] == "yes"
                and current["CapabilityBoundingSet"] == "" and current["AmbientCapabilities"] == "",
                "Baseline isolation properties changed")
        for tool, chain in (("iptables", network["chain4"]), ("ip6tables", network["chain6"])):
            proc = run(["sudo", "-n", tool, "-S", "OUTPUT"])
            new_bytes(control / (tool + "-output-before-goose.txt"), proc.stdout)
            new_bytes(control / (tool + "-output-before-goose.stderr"), proc.stderr)
            verified = output_rules.verify_output_rules(proc.stdout, network["cgroup"].lstrip("/"), chain)
            write_json(control / (tool + "-before-goose-verification.json"), verified)
            require(verified["passed"], "OUTPUT rule verification failed: " + json.dumps(verified))
            counters = run(["sudo", "-n", tool, "-L", chain, "-n", "-v", "-x", "--line-numbers"]).stdout
            new_bytes(control / (tool + "-before-goose.txt"), counters)
        manifest = verify_source_manifest(a.source_manifest)
        require(manifest["manifest_sha256"] == network["source_manifest_sha256"], "Source batch changed since controls")
        manifest["git_commit"] = self.verify_committed_sources(manifest)
        write_json(control / "capture-code-freeze.json", manifest)
        require(prepared_inputs(a) == network["prepared_inputs"], "Workspace/environment/binary/config changed since controls")
        require(pathlib.Path(network["gate_ready"]["working_directory"]).resolve() == pathlib.Path(a.workspace).resolve(),
                "Launch workspace differs from actual prepared wrapper working directory")
        require(pathlib.Path(network["gate_ready"]["recorded_environment"]["GOOSE_PATH_ROOT"]).resolve() == self.profile,
                "Launch profile differs from actual prepared wrapper environment")
        osv_dir = control / "osv-prelaunch"
        osv_dir.mkdir(exist_ok=False)
        verify_osv_reuse(self.commands, osv_dir, network["osv"]["ready_path"],
                         network["osv_unit"], network["osv"]["pid"], manifest)
        require(not list((self.profile / "state/logs").glob("llm_request.*.jsonl")), "Profile already contains model requests")
        require(not list(pathlib.Path(a.workspace).iterdir()), "Baseline workspace is no longer empty")
        db = self.profile / "data/sessions/sessions.db"
        if db.exists():
            with sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True) as conn:
                require(conn.execute("SELECT count(*) FROM sessions").fetchone()[0] == 0, "Profile already contains sessions")
        frozen = verify_frozen_baseline(a.freeze_dir, a.calibration_suite, a.calibration_case)
        require(network.get("calibration") == frozen.get("calibration"), "Calibration selection changed since controls")
        if "calibration" in frozen:
            require(str(stage / "grant_event.json") == frozen["grant_capture"]["grant_event_file"],
                    "Calibration stage does not match its frozen grant event path")
        require(str(pathlib.Path(a.freeze_dir).resolve()) == network["freeze_dir"], "Freeze directory changed since controls")
        write_json(control / "frozen-inputs-reuse.json",
                   {"run": 0, "freeze_dir": str(pathlib.Path(a.freeze_dir).resolve()),
                    "record_sha256": sha(pathlib.Path(a.freeze_dir) / "record.json"),
                    "config_record": str(pathlib.Path(a.config_record).resolve()), "config_record_sha256": sha(a.config_record),
                    "prompt": frozen["prompt"], "fixture": frozen["fixture"], "expected": frozen["expected"]})
        service_env = read_service_env(a.service_env)
        require(pathlib.Path(service_env["GOOSE_PATH_ROOT"]).resolve() == self.profile, "Service profile differs from original profile")
        config = pathlib.Path(a.config).resolve(strict=True)
        require(config == (self.profile / "config/config.yaml").resolve(strict=True), "Config is not the original profile config")
        before = config.read_bytes()
        expected_disabled = json.loads(pathlib.Path(a.config_record).read_bytes())["config_sha256"]
        require(sha(config) == expected_disabled == frozen["grant_capture"]["before_config"]["sha256"],
                "Original disabled config hash mismatch")
        old, new = b"  utcs_mdclean:\n    enabled: false\n", b"  utcs_mdclean:\n    enabled: true\n"
        require(before.count(old) == 1, "Cannot identify the single disabled extension bit")
        after = before.replace(old, new, 1)
        bcfg, acfg = yaml.safe_load(before), yaml.safe_load(after)
        bcfg["extensions"]["utcs_mdclean"]["enabled"] = True
        require(bcfg == acfg, "Config change affects more than the authorized enabled bit")
        require(all(not value["enabled"] for name, value in acfg["extensions"].items() if name != "utcs_mdclean"),
                "An unrelated extension is enabled")
        (stage / "request-logs").mkdir(exist_ok=False)
        watcher_cmd = [
            "/usr/bin/python3", str(HERE / "capture_watch.py"), "--logs-dir", str(self.profile / "state/logs"),
            "--output-dir", str(stage / "request-logs"), "--ready-file", str(control / "watcher-ready.json"),
            "--result-file", str(control / "watcher-result.json"), "--stop-file", str(control / "watcher.stop"),
        ]
        with (stage / "watcher.stdout.log").open("xb") as out, (stage / "watcher.stderr.log").open("xb") as err:
            self.watcher = subprocess.Popen(watcher_cmd, stdout=out, stderr=err, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        self.watch_ready = json.loads(self.wait_file(control / "watcher-ready.json", process=self.watcher).read_bytes())
        capture_script, capture_pid_file = control / "tcpdump-launch.sh", control / "capture-tcpdump.pid"
        precreate_logs([capture_pid_file, stage / "model-api.pcap"])
        script = ("#!/bin/bash\nset -euo pipefail\nprintf '%s\\n' \"$$\" > " + shlex.quote(str(capture_pid_file))
                  + "\nexec /usr/bin/tcpdump -n -i lo -s 0 -U -Z ubuntu -w " + shlex.quote(str(stage / "model-api.pcap"))
                  + " 'tcp port 8000'\n")
        new_bytes(capture_script, script.encode())
        with (stage / "tcpdump.stdout.log").open("xb") as out, (stage / "tcpdump.stderr.log").open("xb") as err:
            self.capture = subprocess.Popen(["sudo", "-n", "bash", str(capture_script)], stdout=out, stderr=err)
        self.capture_pid = int(self.wait_file(capture_pid_file, process=self.capture).read_text().strip())
        deadline = time.monotonic() + 20
        while "listening on lo" not in (stage / "tcpdump.stderr.log").read_text(errors="replace"):
            require(self.capture.poll() is None, (stage / "tcpdump.stderr.log").read_text(errors="replace"))
            if time.monotonic() > deadline:
                raise TimeoutError("tcpdump readiness")
            time.sleep(.05)
        self.capture_ready = {"ready_ns": time.time_ns(), "pid": self.capture_pid, "interface": "lo",
                              "filter": "tcp port 8000", "snaplen": 0, "readiness_evidence": str(stage / "tcpdump.stderr.log")}
        write_json(control / "capture-ready.json", self.capture_ready)
        self.require_capture_alive("before-config-enable")
        new_bytes(stage / "config.disabled.yaml", before)
        new_bytes(stage / "config.enabled.yaml", after)
        # Only the authorized enabled bit changes; recheck the exact original bytes.
        with config.open("r+b") as stream:
            require(stream.read() == before, "Config changed before enable")
            stream.seek(0)
            stream.write(after)
            stream.truncate()
            stream.flush()
            os.fsync(stream.fileno())
        grant = {
            "run": 0, "phase": "rig-validation", "recorded_ns": time.time_ns(),
            "authorization_source": "User explicitly authorized enabling the prepared extension for one T-A rig validation.",
            "mechanism": "Persisted Goose extension enabled:false to enabled:true in auto mode; no call-time approval dialog is asserted.",
            "config_path": str(config), "before_sha256": expected_disabled, "after_sha256": sha(config),
            "change": "extensions.utcs_mdclean.enabled false -> true; all other bytes unchanged",
            "command": acfg["extensions"]["utcs_mdclean"]["cmd"], "args": acfg["extensions"]["utcs_mdclean"]["args"],
            "selector": "utcs-mdclean@latest", "tool_artifact_version": "1.0.0",
        }
        write_json(stage / "grant_event.json", grant)
        release = {"run": 0, "created_ns": time.time_ns(), "prompt_sha256": frozen["prompt"]["sha256"],
                   "config_sha256": sha(config), "watcher_ready_ns": self.watch_ready["ready_ns"],
                   "capture_ready_ns": self.capture_ready["ready_ns"]}
        write_json(control / "release.json", release)
        self.require_capture_alive("before-release")
        self.released = True
        new_bytes(control / "goose.release", (str(time.time_ns()) + "\n").encode())
        write_json(control / "baseline-launch.json",
                   {"run": 0, "single_baseline": True, "released_ns": time.time_ns(), "unit": self.unit,
                    "watcher": self.watch_ready, "capture": self.capture_ready})
        print(json.dumps({"run": 0, "state": "single-baseline-started", "unit": self.unit,
                          "capture": self.capture_ready, "watcher": self.watch_ready}, indent=2), flush=True)
        while not (control / "goose-finished.json").exists():
            self.require_capture_alive("during-Goose")
            if (control / "gate-error.json").exists():
                raise RuntimeError((control / "gate-error.json").read_text())
            state = run(["sudo", "-n", "systemctl", "show", self.unit, "-p", "ActiveState", "-p", "SubState", "-p", "ExecMainStatus"]).stdout.decode()
            # Completion can be published while systemctl is reading final state.
            require_wrapper_running_or_finished(state, (control / "goose-finished.json").exists())
            time.sleep(2)
        self.require_capture_alive("after-Goose-completion")
        self.goose_end = json.loads((control / "goose-finished.json").read_bytes())
        deadline = time.monotonic() + 15
        while not tree_empty(self.cgpath):
            self.require_capture_alive("while-cgroup-drains")
            if time.monotonic() > deadline:
                raise TimeoutError("Goose process tree did not drain after completion")
            time.sleep(.1)
        self.require_capture_alive("after-cgroup-drain")
        write_json(control / "process-tree-drained.json",
                   {"drained_ns": time.time_ns(), "cgroup": network["cgroup"], "cgroup_inode_before": network["cgroup_inode"],
                    "cgroup_exists_after": self.cgpath.exists(), "pids_after": []})
        self.stop_capture()
        self.stop_watcher()
        require(self.goose_end["exit_code"] == 0 and self.goose_end.get("exception", "missing") is None,
                "Goose or wrapper failed: " + json.dumps(self.goose_end))
        require(self.goose_end.get("cleanup_actions") == [] and self.goose_end.get("remaining_cgroup_pids") == [],
                "Goose required cleanup or left descendants")
        require(not (control / "gate-error.json").exists(), "Gate error after Goose")
        deadline = time.monotonic() + 10
        while True:
            raw = run(["sudo", "-n", "systemctl", "show", self.unit, "-p", "MainPID", "-p", "ActiveState",
                       "-p", "SubState", "-p", "ExecMainStatus", "-p", "Result"]).stdout.decode()
            final_state = dict(line.split("=", 1) for line in raw.splitlines() if "=" in line)
            if final_state.get("MainPID") == "0" and final_state.get("SubState") == "exited":
                break
            if final_state.get("ActiveState") == "failed" or time.monotonic() > deadline:
                raise RuntimeError("Wrapper did not finish successfully: " + raw)
            time.sleep(.1)
        require(final_state.get("ExecMainStatus") == "0" and final_state.get("Result") == "success", "Wrapper final state not successful")
        require(not (control / "gate-error.json").exists(), "Gate error at final state")
        write_json(control / "wrapper-final-state.json", final_state)
        require(self.capture_end["exit_code"] == 0, "tcpdump shutdown failed")
        require(self.watch_result["exit_code"] == 0 and not self.watch_result["errors"], "Watcher coverage failed")
        backup_path = stage / "sessions.snapshot.db"
        precreate_logs([backup_path])
        with sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True) as conn:
            ids = conn.execute("SELECT id FROM sessions").fetchall()
            require(len(ids) == 1, "Expected exactly one baseline session: " + repr(ids))
            session_id = ids[0][0]
            with sqlite3.connect(backup_path) as backup:
                conn.backup(backup)
        session_path = stage / "goose-session.json"
        require(not session_path.exists(), "Session export already exists")
        exported = run([a.goose_bin, "session", "export", "--session-id", session_id, "--format", "json", "--output", str(session_path)],
                       env=service_env, cwd=a.workspace)
        new_bytes(stage / "session-export.stdout.log", exported.stdout)
        new_bytes(stage / "session-export.stderr.log", exported.stderr)
        require(session_path.is_file(), "Session export is missing")
        completion = {"schema": "utcs_goose_capture_completion_v1", "run": 0, "goose_version": "1.45.0",
                      "expected_model": "qwen3-32b-awq-native-fc",
                      "goose": {"started_ns": self.goose_end["started_ns"], "finished_ns": self.goose_end["finished_ns"],
                                "exit_code": self.goose_end["exit_code"], "session_id": session_id},
                      "capture": self.capture_end, "watcher": self.watch_result,
                      "prompt": {"path": frozen["prompt"]["path"], "sha256": frozen["prompt"]["sha256"]}}
        write_json(stage / "capture-completion.json", completion)
        result = {"run": 0, "state": "execution-completed-pending-offline-validation", "session_id": session_id,
                  "goose": self.goose_end, "capture": self.capture_end, "watcher_files": len(self.watch_result.get("files", [])),
                  "session_export": str(session_path), "completion": str(stage / "capture-completion.json")}
        write_json(control / "baseline-execution-result.json", result)
        return result

    def handle_failure(self, error, original_traceback):
        record = {"run": 0, "state": "stopped", "error": str(error), "traceback": original_traceback,
                  "goose_released": self.released, "no_retry": True}
        try:
            mark_abort(self.control)
        except BaseException as cleanup:
            record["abort_error"] = repr(cleanup)
        safe_to_stop_capture = not self.released
        if self.released:
            try:
                stopped = self.commands.run(["sudo", "-n", "systemctl", "stop", self.unit], check=False)
                record["unit_stop_exit_code"] = stopped.returncode
                record["unit_stop_stderr"] = stopped.stderr.decode(errors="replace")
                deadline = time.monotonic() + 15
                while not tree_empty(self.cgpath):
                    if time.monotonic() > deadline:
                        record["remaining_pids_by_cgroup"] = {str(p): p.read_text().split() for p in self.cgpath.rglob("cgroup.procs")}
                        break
                    time.sleep(.1)
                safe_to_stop_capture = tree_empty(self.cgpath)
                record["failed_execution_tree_drained"] = safe_to_stop_capture
            except BaseException as cleanup:
                record["unit_shutdown_error"] = repr(cleanup)
        if safe_to_stop_capture:
            for name, stop in (("capture", self.stop_capture), ("watcher", self.stop_watcher)):
                try:
                    stop()
                except BaseException as cleanup:
                    record[name + "_shutdown_error"] = repr(cleanup)
        else:
            record["capture_left_running"] = "Unit process tree not proven drained; instrumentation left active."
        write_json(self.control / "baseline-execution-error.json", record)
        print(json.dumps(record, ensure_ascii=False, indent=2), flush=True)

    def run(self):
        try:
            record = self.execute()
            print(json.dumps(record, ensure_ascii=False, indent=2), flush=True)
            return 0
        except BaseException as error:
            original_traceback = traceback.format_exc()
            try:
                self.handle_failure(error, original_traceback)
            except BaseException as recording_error:
                print(json.dumps({"run": 0, "error": str(error), "traceback": original_traceback,
                                  "error_recording_failure": repr(recording_error)}), file=sys.stderr, flush=True)
            raise
        finally:
            self.commands.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("stage", "profile", "workspace", "service-env", "goose-bin", "config", "repo", "freeze-dir", "config-record"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--source-manifest", default=str(HERE / "SHA256SUMS"))
    parser.add_argument("--calibration-suite")
    parser.add_argument("--calibration-case")
    args = parser.parse_args(argv)
    if (args.calibration_suite is None) != (args.calibration_case is None):
        parser.error("--calibration-suite and --calibration-case must be supplied together")
    os.umask(0o077)
    return LaunchController(args).run()


if __name__ == "__main__":
    raise SystemExit(main())
