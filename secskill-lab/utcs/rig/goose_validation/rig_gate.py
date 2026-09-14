#!/usr/bin/env python3
"""Single-use UTCS baseline gate. No network or model work before explicit gates.

Run inside the pre-created restricted systemd unit. This wrapper never changes
systemd or firewall state. --selftest exercises pure/mocked logic only.
"""
from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import select
import shutil
import signal
import socket
import subprocess
import sys
import time
import traceback

VERSION = "1.0.0"
POLL_SECONDS = 0.1
CONTROL_TIMEOUT_SECONDS = 3.0
CAPABILITY_FIELDS = ("CapInh", "CapPrm", "CapEff", "CapBnd", "CapAmb")
DENIAL_ERRNOS = {errno.ECONNREFUSED, errno.EACCES, errno.EPERM,
                 errno.ENETUNREACH, errno.EHOSTUNREACH}
PENDING_ERRNOS = {errno.EINPROGRESS, errno.EALREADY, errno.EWOULDBLOCK, errno.EINTR}
TRACE_EXPRESSION = "%network,%process,%file,write,pwrite64,ftruncate,truncate,mmap,msync"


class GateFailure(Exception):
    def __init__(self, code, detail):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


class AbortRequested(GateFailure):
    def __init__(self):
        super().__init__("abort_requested", "control/abort exists; no further gate is permitted")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def atomic_new_json(path, value):
    path = Path(path)
    encoded = (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode()
    temp = path.with_name("." + path.name + f".{os.getpid()}.{time.time_ns()}.tmp")
    try:
        with temp.open("xb") as output:
            output.write(encoded)
            output.flush()
            os.fsync(output.fileno())
        os.link(temp, path)
        temp.unlink()
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if temp.exists():
            temp.unlink()
    return digest(encoded)


def strict_json_bytes(data):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise GateFailure("json_duplicate_key", key)
            out[key] = value
        return out
    def constant(value):
        raise GateFailure("json_nonfinite_number", value)
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)
    except (ValueError, UnicodeError) as error:
        raise GateFailure("json_invalid", str(error)) from error


def check_abort(control):
    if (control / "abort").exists():
        raise AbortRequested()


def wait_gate(control, name):
    gate = control / name
    while True:
        check_abort(control)
        if gate.exists():
            if gate.is_symlink() or not gate.is_file():
                raise GateFailure("gate_not_regular_file", str(gate))
            check_abort(control)
            return {"gate": str(gate), "observed_ns": time.time_ns(),
                    "gate_sha256": digest(gate.read_bytes())}
        time.sleep(POLL_SECONDS)


def read_status():
    raw = Path("/proc/self/status").read_text()
    values = {}
    for line in raw.splitlines():
        if ":" in line:
            name, value = line.split(":", 1)
            if name in CAPABILITY_FIELDS or name in ("NoNewPrivs", "Uid", "Gid"):
                values[name] = value.strip()
    return values


def parse_cgroup_text(text):
    rows = [line for line in text.splitlines() if line]
    if len(rows) != 1 or not rows[0].startswith("0::/"):
        raise GateFailure("unexpected_cgroup_layout", text)
    relative = rows[0][3:]
    parts = Path(relative).parts
    if relative == "/" or ".." in parts:
        raise GateFailure("not_isolated_cgroup", relative)
    return relative


def cgroup_state():
    text = Path("/proc/self/cgroup").read_text()
    relative = parse_cgroup_text(text)
    root = Path("/sys/fs/cgroup").resolve(strict=True)
    directory = (root / relative.lstrip("/")).resolve(strict=True)
    if not directory.is_relative_to(root):
        raise GateFailure("cgroup_path_outside_mount", str(directory))
    procs = directory / "cgroup.procs"
    if not procs.is_file():
        raise GateFailure("cgroup_procs_missing", str(procs))
    members = [int(line) for line in procs.read_text().splitlines() if line.strip()]
    if os.getpid() not in members:
        raise GateFailure("wrapper_missing_from_cgroup", str(members))
    info = directory.stat()
    return {
        "cgroup": text, "cgroup_path": relative, "cgroup_directory": str(directory),
        "cgroup_inode": info.st_ino, "cgroup_device": info.st_dev,
        "cgroup_procs_path": str(procs), "cgroup_members": members,
        "cgroup_procs_writable": os.access(procs, os.W_OK, effective_ids=True),
    }


def socket_address_record(value):
    if isinstance(value, bytes):
        return {"bytes_hex": value.hex()}
    if isinstance(value, (tuple, list)):
        return [socket_address_record(item) for item in value]
    if value is None or isinstance(value, (str, int)):
        return value
    raise GateFailure("socket_address_type_unknown", type(value).__name__)


def fd_inventory():
    links, sockets, vanished = {}, [], []
    fds = sorted((int(p.name) for p in Path("/proc/self/fd").iterdir() if p.name.isdigit()))
    for fd in fds:
        try:
            link = os.readlink(f"/proc/self/fd/{fd}")
        except FileNotFoundError:
            vanished.append(fd)
            continue
        links[str(fd)] = link
        if not link.startswith("socket:["):
            continue
        duplicate = None
        probe = None
        try:
            duplicate = os.dup(fd)
            probe = socket.socket(fileno=duplicate)
            duplicate = None
            domain = probe.getsockopt(socket.SOL_SOCKET, socket.SO_DOMAIN)
            kind = probe.getsockopt(socket.SOL_SOCKET, socket.SO_TYPE)
            sockets.append({
                "fd": fd, "link": link, "domain": domain,
                "domain_name": socket.AddressFamily(domain).name,
                "socket_type": kind,
                "local_address": socket_address_record(probe.getsockname()),
            })
        except (OSError, ValueError) as error:
            raise GateFailure("inherited_socket_inventory_failed", f"fd={fd}: {error}") from error
        finally:
            if probe is not None:
                probe.close()
            if duplicate is not None:
                os.close(duplicate)
    return {"fd_links": links, "socket_inventory": sockets, "enumeration_fds_vanished": vanished}


def validate_initial_security(cgroup, status, inventory):
    if status.get("NoNewPrivs") != "1":
        raise GateFailure("no_new_privileges_missing", repr(status.get("NoNewPrivs")))
    for name in CAPABILITY_FIELDS:
        value = status.get(name)
        if not isinstance(value, str) or re.fullmatch(r"[0-9a-fA-F]+", value) is None or int(value, 16) != 0:
            raise GateFailure("capabilities_not_empty", f"{name}={value}")
    if cgroup.get("cgroup_procs_writable") is not False:
        raise GateFailure("cgroup_procs_writable", str(cgroup.get("cgroup_procs_path")))
    for item in inventory["socket_inventory"]:
        if item["domain"] in (socket.AF_INET, socket.AF_INET6):
            raise GateFailure("inherited_inet_socket", repr(item))
        if item["domain"] != socket.AF_UNIX:
            raise GateFailure("inherited_unknown_socket_family", repr(item))


def same_cgroup(original):
    current = cgroup_state()
    for key in ("cgroup", "cgroup_path", "cgroup_inode", "cgroup_device", "cgroup_procs_path"):
        if current[key] != original[key]:
            raise GateFailure("cgroup_identity_changed", key)
    if current["cgroup_procs_writable"]:
        raise GateFailure("cgroup_procs_became_writable", current["cgroup_procs_path"])
    return current


def operation_record(name, began, status, **extra):
    return {"operation": name, "started_ns": began, "finished_ns": time.time_ns(),
            "status": status, **extra}


def err_status(number):
    if number == errno.ETIMEDOUT:
        return "timeout"
    if number == errno.ECONNREFUSED:
        return "refused"
    if number in (errno.EACCES, errno.EPERM):
        return "rejected"
    if number in (errno.ENETUNREACH, errno.EHOSTUNREACH):
        return "unreachable"
    return "os_error"


def wait_socket(sock, writable, deadline, abort):
    while True:
        abort()
        left = deadline - time.monotonic()
        if left <= 0:
            raise OSError(errno.ETIMEDOUT, "control socket deadline exceeded")
        readers, writers, errors = select.select(
            [] if writable else [sock], [sock] if writable else [], [sock],
            min(POLL_SECONDS, left))
        abort()
        if readers or writers or errors:
            return


def connect_once(sock, address, deadline, abort):
    abort()
    number = sock.connect_ex(address)
    if number in (0, errno.EISCONN):
        return
    if number not in PENDING_ERRNOS:
        raise OSError(number, os.strerror(number))
    wait_socket(sock, True, deadline, abort)
    number = sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
    if number:
        raise OSError(number, os.strerror(number))


def send_one(sock, payload, deadline, abort):
    while True:
        abort()
        try:
            return sock.send(payload)
        except BlockingIOError:
            wait_socket(sock, True, deadline, abort)


def recv_one(sock, deadline, abort):
    while True:
        abort()
        try:
            return sock.recv(256)
        except BlockingIOError:
            wait_socket(sock, False, deadline, abort)


def control_spec(number):
    specs = {
        1: {"family": socket.AF_INET, "kind": socket.SOCK_STREAM, "host": "127.0.0.1", "port": 8000, "expected": "success"},
        2: {"family": socket.AF_INET, "kind": socket.SOCK_STREAM, "host": "127.0.0.1", "port": 40000, "expected": "explicit_denial"},
        3: {"family": socket.AF_INET6, "kind": socket.SOCK_STREAM, "host": "::1", "port": 40000, "expected": "explicit_denial"},
        4: {"family": socket.AF_INET, "kind": socket.SOCK_DGRAM, "host": "127.0.0.1", "port": 53, "expected": "send_or_recv_explicit_denial"},
    }
    if number not in specs:
        raise GateFailure("unknown_control", str(number))
    return specs[number]


def run_control(number, abort, socket_factory=socket.socket):
    spec = control_spec(number)
    began = time.time_ns()
    result = {
        "schema": "utcs_rig_local_control_v1", "run": 0, "control_number": number,
        "started_ns": began, "finished_ns": None, "family": socket.AddressFamily(spec["family"]).name,
        "socket_type": "TCP" if spec["kind"] == socket.SOCK_STREAM else "UDP",
        "endpoint": [spec["host"], spec["port"]], "expected": spec["expected"],
        "timeout_seconds": CONTROL_TIMEOUT_SECONDS, "operations": [],
        "status": None, "errno": None, "errno_name": None, "passed": False,
        "dns_query": False, "public_probe": False,
    }
    sock = None
    step = "socket"
    deadline = time.monotonic() + CONTROL_TIMEOUT_SECONDS
    try:
        abort()
        sock = socket_factory(spec["family"], spec["kind"])
        sock.setblocking(False)
        step = "connect"
        tick = time.time_ns()
        connect_once(sock, (spec["host"], spec["port"]), deadline, abort)
        result["operations"].append(operation_record(step, tick, "success", errno=0))
        result["local_address"] = socket_address_record(sock.getsockname())
        if number == 4:
            payload = b"\x00"  # One byte cannot constitute a DNS header or query.
            result["payload_hex"] = payload.hex()
            step = "send"
            tick = time.time_ns()
            count = send_one(sock, payload, deadline, abort)
            result["operations"].append(operation_record(step, tick, "success", bytes_sent=count, errno=0))
            if count != len(payload):
                raise GateFailure("udp_control_short_send", f"{count}/{len(payload)}")
            step = "recv"
            tick = time.time_ns()
            data = recv_one(sock, deadline, abort)
            result["operations"].append(operation_record(step, tick, "success", data_hex=data.hex(), errno=0))
            result["status"] = "unexpected_data"
        else:
            result["status"] = "success"
        result["passed"] = number == 1 and result["status"] == "success"
    except OSError as error:
        number_errno = error.errno
        result["status"] = err_status(number_errno)
        result["errno"] = number_errno
        result["errno_name"] = errno.errorcode.get(number_errno, "UNKNOWN")
        result["error"] = repr(error)
        result["failure_operation"] = step
        result["operations"].append(operation_record(
            step, locals().get("tick", began), result["status"],
            errno=number_errno, errno_name=result["errno_name"], error=repr(error)))
        if number in (2, 3):
            result["passed"] = step == "connect" and number_errno in DENIAL_ERRNOS
        elif number == 4:
            result["passed"] = step in ("send", "recv") and number_errno in DENIAL_ERRNOS
    finally:
        if sock is not None:
            sock.close()
        result["socket_closed"] = True
        result["finished_ns"] = time.time_ns()
    return result


def checked_file(path, expected_hash):
    if not isinstance(expected_hash, str) or re.fullmatch(r"[0-9a-f]{64}", expected_hash) is None:
        raise GateFailure("release_hash_invalid", str(path))
    with Path(path).open("rb") as source:
        before = os.fstat(source.fileno())
        data = source.read()
        after = os.fstat(source.fileno())
    keys = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
    if any(getattr(before, key) != getattr(after, key) for key in keys):
        raise GateFailure("release_file_changed_during_read", str(path))
    actual = digest(data)
    if actual != expected_hash:
        raise GateFailure("release_file_hash_mismatch", f"{path}: {actual} != {expected_hash}")
    return {"path": str(Path(path).resolve()), "sha256": actual, "bytes": len(data),
            "device": after.st_dev, "inode": after.st_ino, "mtime_ns": after.st_mtime_ns}


def validate_release_shape(release):
    if not isinstance(release, dict):
        raise GateFailure("release_not_object", type(release).__name__)
    for key in ("prompt_sha256", "config_sha256"):
        value = release.get(key)
        if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
            raise GateFailure("release_hash_invalid", key)


def command_for(strace_binary, goose_binary, stage, prompt):
    return [str(strace_binary), "-ff", "-ttt", "-T", "-yy", "-s", "4096",
            "-e", "trace=" + TRACE_EXPRESSION, "-o", str(stage / "strace" / "goose"),
            str(goose_binary), "run", "--instructions", str(prompt),
            "--name", "utcs-rig-ta-20260914", "--output-format", "stream-json"]


def descendants_in_cgroup(original):
    same_cgroup(original)
    root = Path(original["cgroup_directory"])
    members = set()
    for path in [root / "cgroup.procs", *root.glob("**/cgroup.procs")]:
        try:
            members.update(int(line) for line in path.read_text().splitlines() if line.strip())
        except FileNotFoundError:
            continue
    members.discard(os.getpid())
    return sorted(members)


def terminate_owned_children(original, process):
    """Abort cleanup is limited to this unchanged unit cgroup and same-UID PIDs."""
    actions = []
    for signum, seconds in ((signal.SIGTERM, 3.0), (signal.SIGKILL, 2.0)):
        for pid in descendants_in_cgroup(original):
            try:
                owner = Path(f"/proc/{pid}").stat().st_uid
                if owner != os.geteuid():
                    actions.append({"pid": pid, "error": "different UID; not signalled"})
                    continue
                os.kill(pid, signum)
                actions.append({"pid": pid, "signal": signum})
            except ProcessLookupError:
                pass
        deadline = time.monotonic() + seconds
        while descendants_in_cgroup(original) and time.monotonic() < deadline:
            process.poll()
            time.sleep(POLL_SECONDS)
        if not descendants_in_cgroup(original):
            break
    process.poll()
    return actions


def run_goose(stage, control, prompt, goose_binary, config, original, gate):
    check_abort(control)
    release_path = control / "release.json"
    if not release_path.is_file() or release_path.is_symlink():
        raise GateFailure("release_record_missing_or_symlink", str(release_path))
    release_raw = release_path.read_bytes()
    release = strict_json_bytes(release_raw)
    validate_release_shape(release)
    prompt_record = checked_file(prompt, release["prompt_sha256"])
    config_record = checked_file(config, release["config_sha256"])
    profile = os.environ.get("GOOSE_PATH_ROOT")
    if not profile or not Path(profile).is_absolute():
        raise GateFailure("goose_path_root_missing_or_relative", repr(profile))
    actual_config = (Path(profile) / "config" / "config.yaml").resolve(strict=True)
    if actual_config != config:
        raise GateFailure("actual_goose_config_mismatch", f"{actual_config} != {config}")
    same_cgroup(original)
    inventory = fd_inventory()
    validate_initial_security(original, read_status(), inventory)
    strace_binary = shutil.which("strace")
    if not strace_binary:
        raise GateFailure("strace_missing", "No strace executable in recorded service PATH")
    if not goose_binary.is_file() or not os.access(goose_binary, os.X_OK):
        raise GateFailure("goose_binary_not_executable", str(goose_binary))
    trace_dir = stage / "strace"
    trace_dir.mkdir(exist_ok=True)
    if any(trace_dir.iterdir()):
        raise GateFailure("strace_directory_not_empty", str(trace_dir))
    if (control / "goose-start.json").exists() or (control / "goose-finished.json").exists():
        raise GateFailure("goose_already_claimed", "Never rerun the baseline")
    command = command_for(Path(strace_binary).resolve(), goose_binary, stage, prompt)
    stdout_path, stderr_path = stage / "goose.stdout.jsonl", stage / "goose.stderr.log"
    process = None
    began = None
    failure = None
    cleanup = []
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        check_abort(control)
        began = time.time_ns()
        atomic_new_json(control / "goose-start.json", {
            "schema": "utcs_rig_goose_start_v1", "run": 0, "started_ns": began,
            "pid": os.getpid(), "wrapper_cgroup": original["cgroup"],
            "cgroup_inode": original["cgroup_inode"], "command": command,
            "working_directory": os.getcwd(), "gate": gate,
            "prompt": prompt_record, "config": config_record,
            "release_sha256": digest(release_raw),
            "stdout_path": str(stdout_path), "stderr_path": str(stderr_path),
        })
        try:
            check_abort(control)
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                                       stdout=stdout, stderr=stderr, close_fds=True)
            while process.poll() is None:
                check_abort(control)
                time.sleep(POLL_SECONDS)
            deadline = time.monotonic() + 10.0
            while descendants_in_cgroup(original):
                check_abort(control)
                if time.monotonic() >= deadline:
                    raise GateFailure("descendants_outlived_strace",
                                      repr(descendants_in_cgroup(original)))
                time.sleep(POLL_SECONDS)
        except BaseException as error:
            failure = error
            if process is not None:
                try:
                    cleanup = terminate_owned_children(original, process)
                except BaseException as cleanup_error:
                    cleanup.append({"error": repr(cleanup_error)})
        finally:
            stdout.flush()
            stderr.flush()
            os.fsync(stdout.fileno())
            os.fsync(stderr.fileno())
    finished = time.time_ns()
    exit_code = process.poll() if process is not None else None
    final = {
        "schema": "utcs_rig_goose_finished_v1", "run": 0,
        "started_ns": began, "finished_ns": finished, "exit_code": exit_code,
        "command": command, "wrapper_pid": os.getpid(), "wrapper_cgroup": Path("/proc/self/cgroup").read_text(),
        "cgroup_inode": original["cgroup_inode"], "strace_pid": process.pid if process is not None else None,
        "cleanup_actions": cleanup, "exception": repr(failure) if failure is not None else None,
        "remaining_cgroup_pids": descendants_in_cgroup(original),
        "stdout_path": str(stdout_path), "stderr_path": str(stderr_path),
        "stdout_sha256": digest(stdout_path.read_bytes()), "stderr_sha256": digest(stderr_path.read_bytes()),
    }
    atomic_new_json(control / "goose-finished.json", final)
    if failure is not None:
        raise failure
    if exit_code != 0:
        raise GateFailure("goose_or_strace_nonzero_exit", repr(exit_code))
    if final["remaining_cgroup_pids"]:
        raise GateFailure("cgroup_children_remaining", repr(final["remaining_cgroup_pids"]))
    return 0


def wrapper(args):
    stage = Path(args.stage).resolve(strict=True)
    control = stage / "control"
    control.mkdir(exist_ok=True)
    prompt = Path(args.prompt).resolve(strict=True)
    config = Path(args.config).resolve(strict=True)
    goose_binary = Path(args.goose_bin).resolve(strict=True)
    atomic_new_json(control / "gate-started.json", {
        "schema": "utcs_rig_gate_claim_v1", "run": 0, "pid": os.getpid(),
        "claimed_ns": time.time_ns(), "wrapper_version": VERSION,
        "wrapper_sha256": digest(Path(__file__).read_bytes()),
    })
    # Never accept gate tokens left by an earlier/partially completed launch.
    stale = [name for name in ("goose.release", "release.json", "gate-ready.json", "gate-error.json", "awaiting-goose.json",
             *[f"control-{n:02d}.go" for n in range(1, 5)],
             *[f"control-{n:02d}.result.json" for n in range(1, 5)])
             if (control / name).exists()]
    if stale:
        raise GateFailure("stale_gate_artifacts", repr(stale))
    check_abort(control)
    if any(Path.cwd().iterdir()):
        raise GateFailure("baseline_workspace_not_empty", os.getcwd())
    original, status, inventory = cgroup_state(), read_status(), fd_inventory()
    validate_initial_security(original, status, inventory)
    env = {key: os.environ.get(key) for key in (
        "GOOSE_PATH_ROOT", "GOOSE_PROVIDER", "GOOSE_MODEL", "GOOSE_MODE",
        "OPENAI_HOST", "OPENAI_BASE_PATH", "OSV_ENDPOINT",
        "GOOSE_TELEMETRY_OFF", "GOOSE_DISABLE_SESSION_NAMING", "OTEL_SDK_DISABLED")}
    ready = {"schema": "utcs_rig_gate_ready_v1", "run": 0, "ready_ns": time.time_ns(),
             "pid": os.getpid(), "working_directory": os.getcwd(), **original,
             "proc_status": status, **inventory, "recorded_environment": env}
    atomic_new_json(control / "gate-ready.json", ready)
    for number in range(1, 5):
        gate = wait_gate(control, f"control-{number:02d}.go")
        current = same_cgroup(original)
        result = run_control(number, lambda: check_abort(control))
        result.update({"gate": gate, "wrapper_pid": os.getpid(), "wrapper_cgroup": current["cgroup"],
                       "cgroup_inode": current["cgroup_inode"]})
        atomic_new_json(control / f"control-{number:02d}.result.json", result)
        if not result["passed"]:
            raise GateFailure("local_control_failed", json.dumps(result, sort_keys=True))
        same_cgroup(original)
    check_abort(control)
    atomic_new_json(control / "awaiting-goose.json", {
        "schema": "utcs_rig_awaiting_goose_v1", "run": 0, "ready_ns": time.time_ns(),
        "pid": os.getpid(), "wrapper_cgroup": original["cgroup"], "cgroup_inode": original["cgroup_inode"],
        "local_controls_passed": [1, 2, 3, 4], "goose_started": False,
        "boundary": "Parent must independently verify each firewall counter increment before release.",
    })
    gate = wait_gate(control, "goose.release")
    return run_goose(stage, control, prompt, goose_binary, config, original, gate)


def selftest():
    records = []
    def test(name, function):
        try:
            function()
            records.append({"name": name, "passed": True})
        except BaseException as error:
            records.append({"name": name, "passed": False, "error": repr(error)})
    class FakeSocket:
        def __init__(self, connect_errno=0, send_errno=None, recv_errno=None, recv_data=b"x"):
            self.connect_errno, self.send_errno, self.recv_errno = connect_errno, send_errno, recv_errno
            self.recv_data, self.closed, self.sent = recv_data, False, []
        def setblocking(self, value):
            assert value is False
        def connect_ex(self, address):
            self.address = address
            return self.connect_errno
        def getsockname(self):
            return ("127.0.0.1", 41000)
        def send(self, data):
            if self.send_errno is not None:
                raise OSError(self.send_errno, "mock denial")
            self.sent.append(data)
            return len(data)
        def recv(self, count):
            if self.recv_errno is not None:
                raise OSError(self.recv_errno, "mock denial")
            return self.recv_data
        def close(self):
            self.closed = True
    def check(condition):
        if not condition:
            raise AssertionError("condition failed")
    def fake_control(number, fake):
        result = run_control(number, lambda: None, socket_factory=lambda *_: fake)
        check(fake.closed)
        return result
    def assert_failure(function, code):
        try:
            function()
        except GateFailure as error:
            check(error.code == code)
            return
        raise AssertionError("expected GateFailure")
    good_status = {name: "0000000000000000" for name in CAPABILITY_FIELDS}
    good_status["NoNewPrivs"] = "1"
    good_cg = {"cgroup_procs_writable": False, "cgroup_procs_path": "/synthetic/cgroup.procs"}
    test("tcp_positive_success", lambda: check(fake_control(1, FakeSocket())["passed"]))
    test("tcp_positive_refusal_fails", lambda: check(not fake_control(1, FakeSocket(errno.ECONNREFUSED))["passed"]))
    test("tcp_negative_refusal_passes", lambda: check(fake_control(2, FakeSocket(errno.ECONNREFUSED))["passed"]))
    test("tcp_negative_admin_denial_passes", lambda: check(fake_control(2, FakeSocket(errno.EACCES))["passed"]))
    test("ipv6_negative_admin_denial_passes", lambda: check(fake_control(3, FakeSocket(errno.EHOSTUNREACH))["passed"]))
    test("tcp_negative_success_fails", lambda: check(not fake_control(2, FakeSocket())["passed"]))
    test("tcp_negative_timeout_fails", lambda: check(not fake_control(2, FakeSocket(errno.ETIMEDOUT))["passed"]))
    test("tcp_negative_unrelated_errno_fails", lambda: check(not fake_control(2, FakeSocket(errno.EINVAL))["passed"]))
    test("udp_send_denial_passes", lambda: check(fake_control(4, FakeSocket(send_errno=errno.EACCES))["passed"]))
    def udp_receive():
        fake = FakeSocket(recv_errno=errno.ECONNREFUSED)
        result = fake_control(4, fake)
        check(result["passed"] and fake.sent == [b"\x00"] and len(fake.sent[0]) < 12)
    test("udp_receive_denial_non_dns_payload", udp_receive)
    test("udp_connect_denial_insufficient", lambda: check(not fake_control(4, FakeSocket(errno.EACCES))["passed"]))
    test("udp_returned_data_fails", lambda: check(not fake_control(4, FakeSocket())["passed"]))
    test("udp_receive_timeout_fails", lambda: check(not fake_control(4, FakeSocket(recv_errno=errno.ETIMEDOUT))["passed"]))
    test("cgroup_v2_path", lambda: check(parse_cgroup_text("0::/system.slice/test.service\n") == "/system.slice/test.service"))
    test("root_cgroup_rejected", lambda: assert_failure(lambda: parse_cgroup_text("0::/\n"), "not_isolated_cgroup"))
    test("cgroup_v1_rejected", lambda: assert_failure(lambda: parse_cgroup_text("1:name=systemd:/test\n"), "unexpected_cgroup_layout"))
    test("abstract_unix_address_preserved", lambda: check(socket_address_record(b"\x00journal") == {"bytes_hex": "006a6f75726e616c"}))
    test("unix_fd_allowed", lambda: validate_initial_security(good_cg, good_status, {"socket_inventory": [{"domain": socket.AF_UNIX}]}))
    test("inherited_ipv4_rejected", lambda: assert_failure(lambda: validate_initial_security(
        good_cg, good_status, {"socket_inventory": [{"domain": socket.AF_INET}]}), "inherited_inet_socket"))
    test("inherited_ipv6_rejected", lambda: assert_failure(lambda: validate_initial_security(
        good_cg, good_status, {"socket_inventory": [{"domain": socket.AF_INET6}]}), "inherited_inet_socket"))
    test("privilege_requirement", lambda: assert_failure(lambda: validate_initial_security(
        good_cg, {**good_status, "NoNewPrivs": "0"}, {"socket_inventory": []}), "no_new_privileges_missing"))
    test("capability_requirement", lambda: assert_failure(lambda: validate_initial_security(
        good_cg, {**good_status, "CapEff": "1"}, {"socket_inventory": []}), "capabilities_not_empty"))
    test("writable_cgroup_rejected", lambda: assert_failure(lambda: validate_initial_security(
        {**good_cg, "cgroup_procs_writable": True}, good_status, {"socket_inventory": []}), "cgroup_procs_writable"))
    test("release_hash_required", lambda: assert_failure(lambda: validate_release_shape({}), "release_hash_invalid"))
    test("release_valid_hashes", lambda: validate_release_shape({"prompt_sha256": "a"*64, "config_sha256": "b"*64}))
    test("release_duplicate_json_rejected", lambda: assert_failure(
        lambda: strict_json_bytes(b'{"a":1,"a":2}'), "json_duplicate_key"))
    def abort_before_socket():
        calls = []
        def abort():
            raise AbortRequested()
        try:
            run_control(1, abort, socket_factory=lambda *_: calls.append(True))
        except AbortRequested:
            check(calls == [])
            return
        raise AssertionError("abort did not raise")
    test("abort_prevents_socket_creation", abort_before_socket)
    report = {"schema": "utcs_rig_gate_selftest_v1", "run": 0, "wrapper_version": VERSION,
              "fixtures": "pure functions and mocked sockets only", "tests": records,
              "passed": sum(item["passed"] for item in records), "total": len(records),
              "all_pass": all(item["passed"] for item in records)}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["all_pass"] else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage")
    parser.add_argument("--prompt")
    parser.add_argument("--goose-bin")
    parser.add_argument("--config")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()
    if not all((args.stage, args.prompt, args.goose_bin, args.config)):
        parser.error("--stage, --prompt, --goose-bin and --config are required")
    try:
        return wrapper(args)
    except BaseException as error:
        record = {
            "schema": "utcs_rig_gate_error_v1", "run": 0, "error_ns": time.time_ns(),
            "pid": os.getpid(), "error": repr(error),
            "code": getattr(error, "code", "wrapper_exception"),
            "detail": str(getattr(error, "detail", error)), "traceback": traceback.format_exc(),
        }
        try:
            control = Path(args.stage).resolve() / "control"
            record["goose_start_record_exists"] = (control / "goose-start.json").exists()
            record["goose_finished_record_exists"] = (control / "goose-finished.json").exists()
            atomic_new_json(control / "gate-error.json", record)
        except BaseException as write_error:
            record["error_record_write_failed"] = repr(write_error)
        print(json.dumps(record, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
