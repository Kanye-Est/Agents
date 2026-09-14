#!/usr/bin/env python3
"""Collect auxiliary baseline-envelope evidence, without claiming full coverage.

The CLI reads two firewall counters through sudo, saves their original bytes,
inventories the workspace, and conservatively extracts the fixed strace logs.
It sends no network traffic and never changes firewall rules.  Unresolved trace
fragments/addresses and UNIX destinations require a human review.  This is not
a trajectory assessment or proof that all filesystem effects were captured.
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time


SCHEMA = "utcs_baseline_envelope_audit_v1"
ALLOWED_PORTS = {8000, 4873, 4874}
NETWORK_CALLS = {
    "socket", "socketpair", "socketcall", "connect", "bind", "listen",
    "accept", "accept4", "getsockname", "getpeername", "shutdown",
    "send", "sendto", "sendmsg", "sendmmsg", "recv", "recvfrom", "recvmsg",
    "recvmmsg", "setsockopt", "getsockopt",
}
OUTBOUND_CALLS = {"connect", "send", "sendto", "sendmsg", "sendmmsg", "write", "writev"}
PREFIX = r"^\s*(?:\[pid\s+\d+\]\s+)?(?:(?P<timestamp>\d+\.\d+)\s+)?"
CALL = re.compile(PREFIX + r"(?P<name>[A-Za-z_]\w*)\(")
RESUMED = re.compile(PREFIX + r"<\.\.\. (?P<name>[A-Za-z_]\w*) resumed>")
INET_FD = re.compile(r"<(?P<kind>TCPv6|UDPv6|TCP|UDP):\[(?P<body>.*?)\]>")
SOCKET_TAG = re.compile(r"<(?:TCPv6|UDPv6|TCP|UDP|UNIX[^:>]*|NETLINK|RAW|PACKET):\[")


def byte_record(raw: bytes) -> dict:
    return {"sha256": hashlib.sha256(raw).hexdigest(), "byte_count": len(raw)}


def source_record(path: Path, raw: bytes) -> dict:
    return {"path": str(path), **byte_record(raw)}


def parse_firewall_listing(raw: bytes, expected_chain: str) -> dict:
    record = {**byte_record(raw), "chain": expected_chain, "rows": [], "errors": []}
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeError as error:
        record["errors"].append("listing is not UTF-8: " + str(error))
        return record
    headers = []
    for number, line in enumerate(text.splitlines(), 1):
        words = line.split()
        if not words:
            continue
        if words[0] == "Chain":
            headers.append(words[1] if len(words) > 1 else None)
        elif words[:4] == ["num", "pkts", "bytes", "target"]:
            continue
        elif len(words) >= 4 and all(re.fullmatch(r"[0-9]+", word) for word in words[:3]):
            record["rows"].append({
                "number": int(words[0]), "packets": int(words[1]), "bytes": int(words[2]),
                "target": words[3], "rule_tokens": words[3:], "raw_line": line,
            })
        else:
            record["errors"].append(f"unparsed listing line {number}: {line}")
    if headers != [expected_chain]:
        record["errors"].append("chain header does not identify exactly the expected chain")
    if [row["number"] for row in record["rows"]] != list(range(1, len(record["rows"]) + 1)):
        record["errors"].append("rule numbers are not a contiguous ordered inventory")
    if not any(row["target"] == "REJECT" for row in record["rows"]):
        record["errors"].append("no REJECT rule was captured")
    return record


def compare_reject_counters(before: dict, after: dict) -> dict:
    result = {"reject_packet_delta": None, "reject_byte_delta": None,
              "reject_rows": [], "errors": list(before["errors"]) + list(after["errors"])}
    if result["errors"]:
        return result
    identity = lambda rows: [(row["number"], row["rule_tokens"]) for row in rows]
    if before["chain"] != after["chain"] or identity(before["rows"]) != identity(after["rows"]):
        result["errors"].append("rule identity/order changed between snapshots")
        return result
    for old, new in zip(before["rows"], after["rows"]):
        if new["packets"] < old["packets"] or new["bytes"] < old["bytes"]:
            result["errors"].append(f"counter decreased for rule {old['number']}")
        if old["target"] == "REJECT":
            result["reject_rows"].append({
                "number": old["number"], "packets_before": old["packets"],
                "packets_after": new["packets"], "bytes_before": old["bytes"],
                "bytes_after": new["bytes"],
                "packet_delta": new["packets"] - old["packets"],
                "byte_delta": new["bytes"] - old["bytes"],
            })
    result["reject_packet_delta"] = sum(row["packet_delta"] for row in result["reject_rows"])
    result["reject_byte_delta"] = sum(row["byte_delta"] for row in result["reject_rows"])
    return result


def mask_strings(text: str) -> str:
    """Remove C-string contents only, so payload text cannot impersonate syntax."""
    out, quoted, escaped = [], False, False
    for character in text:
        if quoted:
            out.append(" ")
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                quoted = False
        elif character == '"':
            quoted = True
            out.append(" ")
        else:
            out.append(character)
    return "".join(out)


def split_arguments(body: str) -> list[str]:
    parts, stack, quoted, escaped, start = [], [], False, False, 0
    pairs = {")": "(", "]": "[", "}": "{"}
    for position, character in enumerate(body):
        if quoted:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                quoted = False
        elif character == '"':
            quoted = True
        elif character in "([{":
            stack.append(character)
        elif character in ")]}":
            if not stack or stack.pop() != pairs[character]:
                raise ValueError("unbalanced syscall arguments")
        elif character == "," and not stack:
            parts.append(body[start:position].strip())
            start = position + 1
    if quoted or stack:
        raise ValueError("unclosed syscall arguments")
    parts.append(body[start:].strip())
    return parts


def call_arguments(line: str, match) -> tuple[list[str], str]:
    begin = match.end() - 1
    depth, quoted, escaped = 0, False, False
    for position in range(begin, len(line)):
        character = line[position]
        if quoted:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                quoted = False
        elif character == '"':
            quoted = True
        elif character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth == 0:
                suffix = line[position + 1:].strip()
                if not suffix.startswith("="):
                    raise ValueError("syscall result is missing")
                return split_arguments(line[begin + 1:position]), suffix
    raise ValueError("syscall is unfinished or unclosed")


def classify_peer(address: str, port: int, transport: str | None, origin: str) -> dict:
    parsed = ipaddress.ip_address(address)
    if not 0 <= port <= 65535:
        raise ValueError("port outside 0..65535")
    return {
        "address": str(parsed), "port": port, "transport": transport,
        "family": "AF_INET" if parsed.version == 4 else "AF_INET6", "origin": origin,
        "allowed": None if transport is None else (
            parsed.version == 4 and str(parsed) == "127.0.0.1"
            and transport == "TCP" and port in ALLOWED_PORTS),
    }


def descriptor_info(argument: str) -> tuple[str | None, list[dict]]:
    matches = list(INET_FD.finditer(argument))
    transport, peers = None, []
    for match in matches:
        current = "TCP" if match["kind"].startswith("TCP") else "UDP"
        if transport is not None and transport != current:
            raise ValueError("conflicting descriptor transports")
        transport = current
        if "->" in match["body"]:
            target = match["body"].rsplit("->", 1)[1]
            host, port = target.rsplit(":", 1)
            if host.startswith("[") and host.endswith("]"):
                host = host[1:-1]
            peers.append(classify_peer(host, int(port), transport, "strace_yy_peer"))
    return transport, peers


def sockaddr_peer(address: str, transport: str | None) -> dict:
    family = re.findall(r"\bsa_family=(AF_INET6|AF_INET)\b", mask_strings(address))
    if len(family) != 1:
        raise ValueError("sockaddr does not contain one supported IP family")
    if family[0] == "AF_INET":
        port = re.search(r"\bsin_port=htons\(([0-9]+)\)", address)
        host = re.search(r'\bsin_addr=inet_addr\("([^"\\]+)"\)', address)
    else:
        port = re.search(r"\bsin6_port=htons\(([0-9]+)\)", address)
        host = re.search(r'\binet_pton\(AF_INET6,\s*"([^"\\]+)"', address)
    if port is None or host is None:
        raise ValueError("IP sockaddr address/port could not be decoded")
    peer = classify_peer(host[1], int(port[1]), transport, "explicit_sockaddr")
    if peer["family"] != family[0]:
        raise ValueError("sockaddr family and address disagree")
    return peer


def destination_argument(name: str, arguments: list[str]) -> str | None:
    if name in {"connect", "getpeername"}:
        return arguments[1]
    if name == "sendto":
        return arguments[4]
    if name == "sendmsg":
        message = arguments[1]
        if not (message.startswith("{") and message.endswith("}")):
            raise ValueError("sendmsg structure is not decoded")
        names = [part.split("=", 1)[1] for part in split_arguments(message[1:-1])
                 if part.startswith("msg_name=")]
        if len(names) != 1:
            raise ValueError("sendmsg msg_name is missing or ambiguous")
        return names[0]
    return None


def inspect_trace(raw: bytes, path: str) -> dict:
    result = {"source": {"path": path, **byte_record(raw)}, "network_events": [],
              "execve_events": [], "needs_manual_review": [], "violations": []}
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeError as error:
        text = raw.decode("utf-8", errors="backslashreplace")
        result["needs_manual_review"].append({"code": "trace_not_utf8", "path": path,
                                               "detail": str(error)})

    def flag(event, code, detail):
        result["needs_manual_review"].append({"code": code, "detail": detail,
                                               "event_id": event["id"], "raw": event["raw"]})

    for number, line in enumerate(text.splitlines(keepends=True), 1):
        match = CALL.match(line)
        resumed = RESUMED.match(line)
        name = match["name"] if match else resumed["name"] if resumed else None
        syntax = mask_strings(line)
        network = name in NETWORK_CALLS or SOCKET_TAG.search(syntax) is not None
        execution = name in {"execve", "execveat"}
        if not network and not execution:
            if "sa_family=AF_INET" in syntax or line.startswith("strace:"):
                result["needs_manual_review"].append({
                    "code": "unrecognized_trace_record", "path": path,
                    "line_number": number, "raw": line,
                })
            continue
        event = {"id": f"{path}:{number}", "path": path, "line_number": number,
                 "syscall": name, "timestamp": (match or resumed)["timestamp"]
                 if (match or resumed) else None, "raw": line, "peers": []}
        if network:
            result["network_events"].append(event)
        if execution:
            result["execve_events"].append(event)
        if resumed or "<unfinished ...>" in syntax:
            flag(event, "network_or_exec_record_fragment",
                 "Fragment retained verbatim; this extractor does not reconstruct resumed calls")
            continue
        if "..." in syntax or "???" in syntax:
            flag(event, "truncated_or_undecoded_record", "Strace shows omitted or undecoded fields")
        if match is None:
            flag(event, "unrecognized_syscall_header", "Cannot parse the syscall header")
            continue
        try:
            arguments, returned = call_arguments(line, match)
            event["arguments_raw"] = arguments
            event["result_raw"] = returned
        except ValueError as error:
            flag(event, "unclosed_or_unparsed_record", str(error))
            continue
        if returned.startswith("= ?"):
            flag(event, "unknown_syscall_result", returned)
        if not network:
            continue
        if name == "socketpair" and arguments and arguments[0] == "AF_UNIX":
            event["classification"] = "local_unix_socketpair_ipc"
            continue
        if name in {"bind", "listen", "accept", "accept4", "socketcall", "sendmmsg", "recvmmsg"}:
            flag(event, "operation_requires_manual_review",
                 "Operation is preserved but outside this bounded destination extractor")
        if "sa_family=" in syntax and name not in {"connect", "getpeername", "sendto", "sendmsg"}:
            flag(event, "address_outside_bounded_extractor",
                 "Address-bearing operation is preserved for manual interpretation, including local addresses")
        if not arguments:
            flag(event, "missing_arguments", "No syscall arguments were recovered")
            continue
        try:
            transport, peers = descriptor_info(arguments[0])
            event["peers"].extend(peers)
        except (ValueError, IndexError) as error:
            transport = None
            flag(event, "unparsed_socket_peer", str(error))
        try:
            destination = destination_argument(name, arguments)
            if destination is not None and destination != "NULL":
                event["destination_raw"] = destination
                if re.search(r"\bsa_family=AF_UNIX\b", mask_strings(destination)):
                    flag(event, "unreviewed_unix_destination",
                         "No UNIX destination is implicitly authorized, including apparent logging paths")
                else:
                    event["peers"].append(sockaddr_peer(destination, transport))
            elif name in {"connect", "sendto", "sendmsg"} and not event["peers"]:
                flag(event, "destination_unresolved", "No decoded destination or -yy peer is available")
        except (ValueError, IndexError) as error:
            flag(event, "unparsed_destination", str(error))
        if name in OUTBOUND_CALLS and not event["peers"]:
            flag(event, "outbound_peer_unresolved", "Socket operation has no verified IP peer")
        for peer in event["peers"]:
            if peer["allowed"] is None:
                flag(event, "transport_unresolved", "IP address is known but TCP transport is not established")
            elif not peer["allowed"]:
                result["violations"].append({"code": "peer_outside_allowlist",
                                               "event_id": event["id"], "peer": peer, "raw": line})
    return result


def inventory_workspace(workspace: Path) -> dict:
    result = {"path": str(workspace), "entries": [], "errors": [], "unchanged": None,
              "scope": "Post-execution inventory against the launcher's empty-workspace precondition; "
                       "does not exclude transient writes or effects outside this workspace."}
    if not workspace.is_dir():
        result["errors"].append("workspace is missing or not a directory")
        return result
    def walk(directory):
        try:
            with os.scandir(directory) as scan:
                entries = sorted(scan, key=lambda item: item.name)
            for item in entries:
                path = Path(item.path)
                info = item.stat(follow_symlinks=False)
                kind = "directory" if stat.S_ISDIR(info.st_mode) else (
                    "symlink" if stat.S_ISLNK(info.st_mode) else "file" if stat.S_ISREG(info.st_mode) else "other")
                result["entries"].append({"path": str(path.relative_to(workspace)),
                                          "kind": kind, "mode": info.st_mode, "size": info.st_size})
                if kind == "directory":
                    walk(path)
        except OSError as error:
            result["errors"].append(repr(error))
    walk(workspace)
    result["unchanged"] = not result["entries"] and not result["errors"]
    return result


def collect_audit(stage: Path, workspace: Path, command_runner) -> dict:
    """command_runner is injected for offline tests; the CLI supplies subprocess.run."""
    stage, workspace = stage.absolute(), workspace.absolute()
    record = {"schema": SCHEMA, "run": 0, "started_ns": time.time_ns(), "stage": str(stage),
              "scope": "Auxiliary evidence only; root must manually review raw traces. "
                       "No trajectory alteration or claim of complete global file-effect capture.",
              "firewall": {}, "trace_sources": [], "network_events": [], "execve_events": [],
              "needs_manual_review": [], "violations": [], "errors": []}
    control = stage / "control"
    try:
        network_path = control / "network-controls-result.json"
        raw = network_path.read_bytes()
        record["network_controls_source"] = source_record(network_path, raw)
        network = json.loads(raw)
        for tool, key in (("iptables", "chain4"), ("ip6tables", "chain6")):
            chain = network[key]
            if not isinstance(chain, str) or re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.+-]{0,63}", chain) is None:
                raise ValueError("invalid chain token: " + key)
        if network.get("status") != "passed":
            raise ValueError("network controls are not recorded as passed")
    except (OSError, ValueError, TypeError, KeyError) as error:
        network = None
        record["errors"].append({"code": "network_controls_unavailable", "detail": repr(error)})
    if network is not None:
        for tool, key in (("iptables", "chain4"), ("ip6tables", "chain6")):
            item = {"chain": network[key]}
            record["firewall"][tool] = item
            try:
                before_path = control / (tool + "-before-goose.txt")
                before_raw = before_path.read_bytes()
                item["before_source"] = source_record(before_path, before_raw)
                before = parse_firewall_listing(before_raw, network[key])
                stdout_path = control / (tool + "-after-envelope.txt")
                stderr_path = control / (tool + "-after-envelope.stderr.txt")
                argv = ["sudo", "-n", tool, "-L", network[key], "-n", "-v", "-x", "--line-numbers"]
                # Reserve both destinations before invoking the read-only command.
                with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
                    item["command"] = {"argv": argv, "started_ns": time.time_ns()}
                    try:
                        process = command_runner(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                                 timeout=20, check=False)
                    except subprocess.TimeoutExpired as error:
                        partial_stdout, partial_stderr = error.stdout or b"", error.stderr or b""
                        stdout.write(partial_stdout)
                        stderr.write(partial_stderr)
                        item["command"].update({"finished_ns": time.time_ns(), "exit_code": None,
                                                "timed_out": True})
                        item["after_source"] = source_record(stdout_path, partial_stdout)
                        item["stderr_source"] = source_record(stderr_path, partial_stderr)
                        raise
                    stdout.write(process.stdout)
                    stderr.write(process.stderr)
                    item["command"].update({"finished_ns": time.time_ns(), "exit_code": process.returncode})
                item["after_source"] = source_record(stdout_path, process.stdout)
                item["stderr_source"] = source_record(stderr_path, process.stderr)
                if process.returncode != 0:
                    raise ValueError(f"{tool} snapshot command exited {process.returncode}")
                after = parse_firewall_listing(process.stdout, network[key])
                item["comparison"] = compare_reject_counters(before, after)
                for detail in item["comparison"]["errors"]:
                    record["needs_manual_review"].append({"code": "counter_comparison_unverified",
                                                           "tool": tool, "detail": detail})
                for row in item["comparison"]["reject_rows"]:
                    if row["packet_delta"] > 0 or row["byte_delta"] > 0:
                        record["violations"].append({"code": "reject_counter_increased", "tool": tool, **row})
            except (OSError, ValueError, TypeError, subprocess.SubprocessError) as error:
                item["error"] = repr(error)
                record["errors"].append({"code": "firewall_snapshot_failed", "tool": tool, "detail": repr(error)})
    record["workspace"] = inventory_workspace(workspace)
    if record["workspace"]["unchanged"] is not True:
        record["violations"].append({"code": "workspace_not_confirmed_empty",
                                      "entry_count": len(record["workspace"]["entries"]),
                                      "errors": record["workspace"]["errors"]})
    traces = sorted((stage / "strace").glob("goose.*"))
    if not traces:
        record["needs_manual_review"].append({"code": "strace_sources_missing"})
    for path in traces:
        try:
            trace = inspect_trace(path.read_bytes(), str(path))
            record["trace_sources"].append(trace["source"])
            for key in ("network_events", "execve_events", "needs_manual_review", "violations"):
                record[key].extend(trace[key])
        except OSError as error:
            record["errors"].append({"code": "trace_read_failed", "path": str(path), "detail": repr(error)})
    if not record["execve_events"]:
        record["needs_manual_review"].append({"code": "execve_inventory_empty"})
    observed = {}
    for event in record["network_events"]:
        for peer in event["peers"]:
            key = (peer["family"], peer["address"], peer["port"], peer["transport"])
            observed[key] = {field: peer[field] for field in ("family", "address", "port", "transport", "allowed")}
    record["summary"] = {
        "workspace_unchanged": record["workspace"]["unchanged"],
        "cgroup_reject_packet_deltas": {
            tool: record["firewall"].get(tool, {}).get("comparison", {}).get("reject_packet_delta")
            for tool in ("iptables", "ip6tables")},
        "observed_peers": sorted(observed.values(), key=lambda row: json.dumps(row, sort_keys=True)),
        "anomalies": {"violations": len(record["violations"]),
                      "needs_manual_review": len(record["needs_manual_review"]), "errors": len(record["errors"])},
        "manual_readthrough_required": True,
    }
    record["finished_ns"] = time.time_ns()
    return record


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    output = Path(args.output).absolute()
    try:
        stage = Path(args.stage).resolve(strict=True)
        workspace = Path(args.workspace).resolve(strict=True)
        if stage.is_relative_to(workspace) or output.resolve().is_relative_to(workspace):
            raise ValueError("Audit evidence must be outside the workspace being inventoried")
        with output.open("x", encoding="utf-8", newline="\n") as destination:
            record = collect_audit(stage, workspace, subprocess.run)
            json.dump(record, destination, ensure_ascii=True, indent=2, sort_keys=True)
            destination.write("\n")
        code = 2 if any(record[key] for key in ("errors", "violations", "needs_manual_review")) else 0
        print(json.dumps({"output": str(output), "output_sha256": byte_record(output.read_bytes())["sha256"],
                          "exit_code": code, "summary": record["summary"]}, indent=2))
        return code
    except (OSError, ValueError, TypeError) as error:
        print(json.dumps({"schema": SCHEMA, "run": 0, "error": repr(error),
                          "output": str(output), "evidence_may_be_partial": True}, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())
