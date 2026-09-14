#!/usr/bin/env python3
"""Prepare one fresh, held Goose unit; reuse the already running OSV helper.

All evidence is exclusive beneath --stage. Source paths are relative to this
file. Firewall --path values are cgroup-root-relative (no leading slash).
This entry point never releases Goose or restarts the existing OSV helper.
"""
import argparse
import base64
import datetime
import hashlib
import json
import os
import pathlib
import pwd
import re
import subprocess
import sys
import time
import traceback

sys.dont_write_bytecode = True
import output_rules

HERE = pathlib.Path(__file__).resolve().parent
FROZEN_FILES = {
    "prompt": ("prompt.txt", "T-A.prompt.txt"),
    "fixture": ("input.md", "T-A.input.md"),
    "expected": ("expected.md", "T-A.expected.md"),
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def new_bytes(path, data):
    """Publish a complete file atomically, never replacing an existing name."""
    path = pathlib.Path(path)
    temp = path.with_name("." + path.name + f".{os.getpid()}.{time.time_ns()}.tmp")
    try:
        with temp.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def write_json(path, value):
    new_bytes(path, (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())


def mark_abort(control):
    try:
        new_bytes(control / "abort", b"STOP; no automatic retry\n")
    except FileExistsError:
        pass


def precreate_logs(paths):
    """systemd appends to user-owned files instead of making root:0600 logs."""
    for path in paths:
        with pathlib.Path(path).open("xb"):
            pass
        require(pathlib.Path(path).stat().st_uid == os.geteuid(), "Log owner mismatch: " + str(path))


def prepared_inputs(args):
    record = {"workspace": str(pathlib.Path(args.workspace).resolve(strict=True))}
    for name in ("service_env", "goose_bin", "config"):
        path = pathlib.Path(getattr(args, name)).resolve(strict=True)
        record[name] = {"path": str(path), "sha256": sha(path)}
    return record


def verify_source_manifest(manifest_path, source_dir=HERE):
    source_dir = pathlib.Path(source_dir).resolve(strict=True)
    manifest_path = pathlib.Path(manifest_path).resolve(strict=True)
    raw = manifest_path.read_bytes()
    entries = {}
    for number, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        match = re.fullmatch(r"([0-9a-f]{64}) [ *](.+)", line)
        require(match is not None, f"Malformed SHA256SUMS line {number}")
        digest, relative = match.groups()
        path = pathlib.PurePosixPath(relative)
        require(not path.is_absolute() and ".." not in path.parts,
                "Manifest path outside source directory: " + relative)
        require(path.as_posix() == relative and relative not in entries,
                "Noncanonical or duplicate manifest path: " + relative)
        actual = source_dir / relative
        resolved = actual.resolve(strict=True)
        require(resolved.is_relative_to(source_dir) and not actual.is_symlink() and actual.is_file(),
                "Manifest source is not a regular in-tree file: " + relative)
        require(resolved != manifest_path, "SHA256SUMS cannot include itself")
        require(sha(actual) == digest, "Source hash mismatch: " + relative)
        entries[relative] = digest
    code = {p.relative_to(source_dir).as_posix() for p in source_dir.rglob("*")
            if p.is_file() and p.suffix in {".py", ".sh", ".jinja"}}
    require(code and code <= entries.keys(), "Manifest omits helper code: " + repr(sorted(code - entries.keys())))
    return {"run": 0, "verified_ns": time.time_ns(), "manifest": str(manifest_path),
            "manifest_sha256": hashlib.sha256(raw).hexdigest(), "source_dir": str(source_dir),
            "sources": [{"relative_path": name, "path": str(source_dir / name), "sha256": digest}
                        for name, digest in sorted(entries.items())]}


def verify_frozen_baseline(freeze_dir, calibration_suite=None, calibration_case=None):
    require((calibration_suite is None) == (calibration_case is None),
            "--calibration-suite and --calibration-case must be supplied together")
    if calibration_suite is not None:
        from calibration_contract import verify_calibration_baseline
        return verify_calibration_baseline(freeze_dir, calibration_suite, calibration_case)
    # The original no-argument lock remains byte-for-byte strict.
    freeze_dir = pathlib.Path(freeze_dir).resolve(strict=True)
    record_path = freeze_dir / "record.json"
    require(record_path.read_bytes() == (HERE / "baseline/original-freeze-record.json").read_bytes(),
            "Original baseline freeze record changed")
    frozen = json.loads(record_path.read_bytes())
    for key, (name, source_name) in FROZEN_FILES.items():
        path = (freeze_dir / name).resolve(strict=True)
        require(path == pathlib.Path(frozen[key]["path"]).resolve(strict=True), "Frozen path mismatch: " + key)
        data = path.read_bytes()
        require(hashlib.sha256(data).hexdigest() == frozen[key]["sha256"], "Frozen hash mismatch: " + key)
        require(len(data) == frozen[key]["bytes"], "Frozen byte count mismatch: " + key)
        require(data == (HERE / "baseline" / source_name).read_bytes(), "Committed baseline differs: " + key)
    require(frozen["run"] == 0 and frozen["zero_name_leakage"]["passed"] is True,
            "Baseline must retain run=0 and its frozen name-leakage check")
    return frozen


class CommandLog:
    def __init__(self, path):
        self.log = pathlib.Path(path).open("x")

    def run(self, cmd, check=True, env=None, cwd=None):
        began = time.time_ns()
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, cwd=cwd)
        row = {"started_ns": began, "finished_ns": time.time_ns(), "argv": cmd, "exit_code": proc.returncode}
        for name in ("stdout", "stderr"):
            raw = getattr(proc, name)
            row[name] = raw.decode("utf-8", errors="replace")
            row[name + "_base64"] = base64.b64encode(raw).decode("ascii")
            row[name + "_sha256"] = hashlib.sha256(raw).hexdigest()
        self.log.write(json.dumps(row, ensure_ascii=False) + "\n")
        self.log.flush()
        if check and proc.returncode:
            raise RuntimeError(json.dumps(row, ensure_ascii=False))
        return proc

    def close(self):
        self.log.close()


def systemd_state(commands, unit):
    fields = ["LoadState", "ControlGroup", "MainPID", "ActiveState", "SubState", "Delegate",
              "NoNewPrivileges", "CapabilityBoundingSet", "AmbientCapabilities"]
    cmd = ["sudo", "-n", "systemctl", "show", unit]
    for field in fields:
        cmd.extend(["-p", field])
    raw = commands.run(cmd).stdout
    return dict(line.split("=", 1) for line in raw.decode().splitlines() if "=" in line)


def verify_osv_reuse(commands, control, ready_path, unit, expected_pid, manifest, proc_root=pathlib.Path("/proc")):
    ready_path = pathlib.Path(ready_path).resolve(strict=True)
    ready_raw = ready_path.read_bytes()
    ready = json.loads(ready_raw)
    require(ready.get("pid") == expected_pid and expected_pid > 1, "OSV ready PID mismatch")
    require(ready.get("bind") == ["127.0.0.1", 4874], "OSV ready binding mismatch")
    require(ready.get("response_status") == 503 and ready.get("no_upstream_requests") is True,
            "OSV must report unavailable, without upstream requests or a clean verdict")
    state = systemd_state(commands, unit)
    require(state.get("LoadState") == "loaded" and state.get("ActiveState") == "active"
            and state.get("SubState") == "running" and int(state.get("MainPID", 0)) == expected_pid,
            "Existing OSV unit is not the recorded running PID: " + repr(state))
    proc = pathlib.Path(proc_root) / str(expected_pid)
    cmdline = (proc / "cmdline").read_bytes()
    argv = [part.decode("utf-8") for part in cmdline.rstrip(b"\0").split(b"\0")]
    require(len(argv) == 4 and pathlib.Path(argv[1]).name == "osv_unavailable.py" and argv[2] == "--stage",
            "Unexpected actual OSV process command line: " + repr(argv))
    source = pathlib.Path(argv[1]).resolve(strict=True)
    require(pathlib.Path(argv[3]).resolve(strict=True) == ready_path.parent.parent,
            "OSV process stage differs from its existing ready record")
    sources = {row["relative_path"]: row["sha256"] for row in manifest["sources"]}
    source_hash = sha(source)
    require(source_hash == sources["osv_unavailable.py"], "Actual OSV source differs from committed batch")
    require((proc / "cgroup").read_text().strip() == "0::" + state["ControlGroup"], "OSV systemd/proc cgroup mismatch")
    listeners = commands.run(["sudo", "-n", "ss", "-H", "-ltnp"]).stdout
    new_bytes(control / "osv-listeners.txt", listeners)
    rows = [line for line in listeners.decode().splitlines()
            if len(line.split()) >= 5 and line.split()[3].rsplit(":", 1)[-1] == "4874"]
    require(len(rows) == 1 and rows[0].split()[3] == "127.0.0.1:4874" and f"pid={expected_pid}," in rows[0],
            "OSV actual listener is not solely 127.0.0.1:4874: " + repr(rows))
    new_bytes(control / "osv-existing-ready.json", ready_raw)
    new_bytes(control / "osv-existing-cmdline.bin", cmdline)
    record = {"run": 0, "reused": True, "restarted": False, "unit": unit, "pid": expected_pid,
              "ready_path": str(ready_path), "ready_sha256": hashlib.sha256(ready_raw).hexdigest(),
              "ready": ready, "state": state, "actual_argv": argv,
              "source_path_from_proc_cmdline": str(source), "source_sha256_on_disk": source_hash,
              "listeners": rows, "verified_ns": time.time_ns()}
    write_json(control / "osv-reuse-verification.json", record)
    return record


class PrepareController:
    def __init__(self, args):
        self.args = args
        self.stage = pathlib.Path(args.stage).resolve()
        self.stage.mkdir(exist_ok=True)
        self.control = self.stage / "control"
        self.control.mkdir(exist_ok=False)
        self.commands = CommandLog(self.control / "prepare-commands.jsonl")

    def wait_file(self, name, seconds=30):
        path = self.control / name
        deadline = time.monotonic() + seconds
        while not path.exists():
            if (self.control / "gate-error.json").exists():
                raise RuntimeError((self.control / "gate-error.json").read_text())
            if time.monotonic() > deadline:
                raise TimeoutError(str(path))
            time.sleep(.1)
        return json.loads(path.read_bytes())

    def counts(self, tool, chain, label):
        raw = self.commands.run(["sudo", "-n", tool, "-L", chain, "-n", "-v", "-x", "--line-numbers"]).stdout
        new_bytes(self.control / (label + ".txt"), raw)
        rows = []
        for line in raw.decode().splitlines():
            words = line.split()
            if words and words[0].isdigit():
                rows.append({"num": int(words[0]), "packets": int(words[1]), "bytes": int(words[2]), "target": words[3]})
        return rows

    def execute(self):
        a, control, run = self.args, self.control, self.commands.run
        require(pwd.getpwuid(os.geteuid()).pw_name == "ubuntu", "Run controller as ubuntu, not sudo/root")
        require(re.fullmatch(r"[A-Za-z0-9_-]+\.service", a.unit) is not None, "Invalid fresh unit name")
        require(re.fullmatch(r"[A-Za-z0-9_-]+\.service", a.osv_unit) is not None and a.osv_unit != a.unit,
                "OSV unit must be distinct from baseline unit")
        for chain in (a.chain4, a.chain6):
            require(re.fullmatch(r"UTCS_[A-Z0-9_]{1,22}", chain) is not None, "Invalid fresh chain name: " + chain)
        require(a.chain4 != a.chain6, "IPv4 and IPv6 chain names must be distinct")
        manifest = verify_source_manifest(a.source_manifest)
        write_json(control / "prepare-source-freeze.json", manifest)
        frozen = verify_frozen_baseline(a.freeze_dir, a.calibration_suite, a.calibration_case)
        if "calibration" in frozen:
            require(str(self.stage / "grant_event.json") == frozen["grant_capture"]["grant_event_file"],
                    "Calibration stage does not match its frozen grant event path")
        inputs = prepared_inputs(a)
        state = run(["sudo", "-n", "systemctl", "show", a.unit, "-p", "LoadState", "--value"]).stdout.decode().strip()
        require(state == "not-found", "Refuse to reuse baseline unit: " + state)
        for tool, chain in (("iptables", a.chain4), ("ip6tables", a.chain6)):
            existing = run(["sudo", "-n", tool, "-S"]).stdout.decode().splitlines()
            require("-N " + chain not in existing, "Refuse to reuse network chain: " + chain)
        osv = verify_osv_reuse(self.commands, control, a.osv_ready, a.osv_unit, a.osv_pid, manifest)
        precreate_logs([control / "gate.stdout.log", control / "gate.stderr.log"])
        props = ["--uid=ubuntu", "--property=NoNewPrivileges=yes", "--property=CapabilityBoundingSet=",
                 "--property=AmbientCapabilities=", "--property=Delegate=no", "--property=UMask=0077",
                 "--property=KillMode=control-group", "--property=Type=exec"]
        run(["sudo", "-n", "systemd-run", "--unit=" + a.unit, *props, "--property=RemainAfterExit=yes",
             "--property=WorkingDirectory=" + str(pathlib.Path(a.workspace).resolve(strict=True)),
             "--property=EnvironmentFile=" + str(pathlib.Path(a.service_env).resolve(strict=True)),
             "--setenv=PYTHONDONTWRITEBYTECODE=1",
             "--property=StandardOutput=append:" + str(control / "gate.stdout.log"),
             "--property=StandardError=append:" + str(control / "gate.stderr.log"),
             "/usr/bin/python3", str(HERE / "rig_gate.py"), "--stage", str(self.stage),
             "--prompt", frozen["prompt"]["path"], "--goose-bin", str(pathlib.Path(a.goose_bin).resolve(strict=True)),
             "--config", str(pathlib.Path(a.config).resolve(strict=True))])
        ready = self.wait_file("gate-ready.json")
        wrapper = self.wait_file("gate-started.json")
        source_hashes = {row["relative_path"]: row["sha256"] for row in manifest["sources"]}
        require(wrapper["wrapper_sha256"] == source_hashes["rig_gate.py"], "Actual wrapper source hash mismatch")
        require(ready["working_directory"] == inputs["workspace"], "Actual wrapper working directory mismatch")
        state = systemd_state(self.commands, a.unit)
        write_json(control / "systemd-before-controls.json", state)
        main_pid = int(state["MainPID"])
        require(main_pid == ready["pid"] and main_pid > 0, "Baseline PID mismatch")
        require(state["ActiveState"] == "active" and state["Delegate"] == "no" and state["NoNewPrivileges"] == "yes",
                "Baseline isolation properties changed")
        require(state["CapabilityBoundingSet"] == "" and state["AmbientCapabilities"] == "", "Baseline capabilities not empty")
        cg = state["ControlGroup"]
        require(cg == "/system.slice/" + a.unit, "Unexpected baseline cgroup: " + cg)
        proc_cgroup = pathlib.Path("/proc") / str(main_pid) / "cgroup"
        require(proc_cgroup.read_text().strip() == "0::" + cg, "Baseline /proc cgroup mismatch")
        cgpath = pathlib.Path("/sys/fs/cgroup") / cg.lstrip("/")
        cg_inode = cgpath.stat().st_ino
        require(not os.access(cgpath / "cgroup.procs", os.W_OK), "cgroup.procs must not be writable by ubuntu")
        run(["sudo", "-n", "iptables", "-N", a.chain4])
        run(["sudo", "-n", "iptables", "-A", a.chain4, "-o", "lo", "-d", "127.0.0.1/32", "-p", "tcp",
             "-m", "multiport", "--dports", "8000,4873,4874", "-j", "ACCEPT"])
        run(["sudo", "-n", "iptables", "-A", a.chain4, "-j", "REJECT", "--reject-with", "icmp-admin-prohibited"])
        run(["sudo", "-n", "ip6tables", "-N", a.chain6])
        run(["sudo", "-n", "ip6tables", "-A", a.chain6, "-j", "REJECT", "--reject-with", "icmp6-adm-prohibited"])
        for tool, chain in (("iptables", a.chain4), ("ip6tables", a.chain6)):
            run(["sudo", "-n", tool, "-I", "OUTPUT", "1", "-m", "cgroup", "--path", cg.lstrip("/"), "-j", chain])
            proc = run(["sudo", "-n", tool, "-S", "OUTPUT"])
            new_bytes(control / (tool + "-output-before.txt"), proc.stdout)
            new_bytes(control / (tool + "-output-before.stderr"), proc.stderr)
            verified = output_rules.verify_output_rules(proc.stdout, cg.lstrip("/"), chain)
            write_json(control / (tool + "-output-verification.json"), verified)
            require(verified["passed"], "OUTPUT rule verification failed: " + json.dumps(verified))
        before4 = self.counts("iptables", a.chain4, "ipv4-control-initial")
        before6 = self.counts("ip6tables", a.chain6, "ipv6-control-initial")
        results = []
        for number in range(1, 5):
            require(cgpath.stat().st_ino == cg_inode and proc_cgroup.read_text().strip() == "0::" + cg,
                    "Baseline cgroup identity changed before control")
            new_bytes(control / f"control-{number:02}.go", (str(time.time_ns()) + "\n").encode())
            result = self.wait_file(f"control-{number:02}.result.json", 15)
            require(result["passed"] is True, "Local control failed: " + json.dumps(result))
            after4 = self.counts("iptables", a.chain4, f"ipv4-after-control-{number:02}")
            after6 = self.counts("ip6tables", a.chain6, f"ipv6-after-control-{number:02}")
            target = "ACCEPT" if number == 1 else "REJECT"
            before, after = (before6, after6) if number == 3 else (before4, after4)
            delta = sum(r["packets"] for r in after if r["target"] == target) - sum(r["packets"] for r in before if r["target"] == target)
            require(delta > 0, f"Control {number} did not increment actual {target} counter: {delta}")
            results.append({"number": number, "result": result, "verified_counter_target": target, "counter_packet_delta": delta})
            before4, before6 = after4, after6
        awaiting = self.wait_file("awaiting-goose.json")
        state_after = systemd_state(self.commands, a.unit)
        require(int(state_after["MainPID"]) == main_pid and cgpath.stat().st_ino == cg_inode, "Baseline identity changed")
        require(not (control / "goose-start.json").exists(), "Goose started before release")
        record = {"run": 0, "status": "passed", "completed_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  "unit": a.unit, "osv_unit": a.osv_unit, "main_pid": main_pid, "cgroup": cg, "cgroup_inode": cg_inode,
                  "chain4": a.chain4, "chain6": a.chain6, "osv": osv, "controls": results, "state": state_after,
                  "gate_ready": ready, "awaiting_goose": awaiting, "goose_started": False,
                  "source_manifest_sha256": manifest["manifest_sha256"], "freeze_dir": str(pathlib.Path(a.freeze_dir).resolve()),
                  "prepared_inputs": inputs,
                  **({"calibration": frozen["calibration"]} if "calibration" in frozen else {}),
                  "boundary": "Rules restrict new IP sockets in this Goose cgroup. Existing local backend/registry processes use their separately verified offline/no-uplink configurations. No public probe was made. Native OSV returns 503; scanner unavailable, not scan-passed."}
        write_json(control / "network-controls-result.json", record)
        return record

    def run(self):
        try:
            record = self.execute()
            print(json.dumps(record, ensure_ascii=False, indent=2))
            return 0
        except BaseException as error:
            record = {"run": 0, "status": "stopped", "error": str(error), "traceback": traceback.format_exc(),
                      "unit": self.args.unit, "osv_unit": self.args.osv_unit,
                      "no_goose_release": not (self.control / "goose.release").exists(), "no_retry": True}
            try:
                mark_abort(self.control)
            except BaseException as cleanup:
                record["abort_error"] = repr(cleanup)
            write_json(self.control / "prepare-error.json", record)
            print(json.dumps(record, ensure_ascii=False, indent=2))
            raise
        finally:
            self.commands.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("stage", "workspace", "service-env", "goose-bin", "config", "freeze-dir", "unit", "chain4", "chain6", "osv-ready", "osv-unit"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--osv-pid", required=True, type=int)
    parser.add_argument("--source-manifest", default=str(HERE / "SHA256SUMS"))
    parser.add_argument("--calibration-suite")
    parser.add_argument("--calibration-case")
    args = parser.parse_args(argv)
    if (args.calibration_suite is None) != (args.calibration_case is None):
        parser.error("--calibration-suite and --calibration-case must be supplied together")
    os.umask(0o077)
    return PrepareController(args).run()


if __name__ == "__main__":
    raise SystemExit(main())
