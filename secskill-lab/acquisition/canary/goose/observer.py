#!/usr/bin/env python3
"""
Process-tree observer for the Goose activation-binding canary.

Protocol freeze: idea/48_GOOSE_CANARY_PROTOCOL_FREEZE.md §3.2

Ground truth for the `process_spawned` event.  Deliberately external: the protocol
forbids instrumenting the spawn by rewriting the artifact, because that would make the
artifact non-representative of what a real extension looks like.  So we watch /proc.

Stdlib only, no psutil, so the rig stays reproducible on a bare host.

Records, for every process whose cmdline matches the watch pattern:
  first-seen wall + monotonic timestamp, pid, ppid, full cmdline, and the ancestor
  chain up to init.  The ancestor chain is what lets a run attribute a spawn to Goose
  rather than to the harness.

Usage:
  observer.py --out <path.jsonl> [--pattern goose-activation-canary] [--interval-ms 5]

Stop with SIGINT/SIGTERM; it flushes and writes a summary line.
"""

import argparse
import json
import os
import signal
import sys
import time

DEFAULT_PATTERN = "goose-activation-canary"


def stamp():
    return {
        "wall_ns": time.time_ns(),
        "monotonic_ns": time.monotonic_ns(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
    }


def read_proc(pid):
    """Return (cmdline, ppid) or None if the process vanished mid-read."""
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            raw = f.read()
        cmdline = raw.replace(b"\x00", b" ").decode("utf-8", "replace").strip()
        ppid = None
        with open(f"/proc/{pid}/status", "r") as f:
            for line in f:
                if line.startswith("PPid:"):
                    ppid = int(line.split()[1])
                    break
        return cmdline, ppid
    except (FileNotFoundError, ProcessLookupError, PermissionError, ValueError):
        return None


def ancestry(pid, limit=12):
    """Walk up the parent chain. Attribution depends on this: a spawn under Goose is a
    different observation from a spawn under the harness shell."""
    chain = []
    cur = pid
    for _ in range(limit):
        info = read_proc(cur)
        if info is None:
            break
        cmdline, ppid = info
        chain.append({"pid": cur, "cmdline": cmdline[:400]})
        if not ppid or ppid == cur or ppid == 0:
            break
        cur = ppid
    return chain


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--pattern", default=DEFAULT_PATTERN)
    ap.add_argument("--interval-ms", type=float, default=5.0)
    args = ap.parse_args()

    interval = args.interval_ms / 1000.0
    seen = set()
    running = {"flag": True}
    count = {"n": 0}

    def stop(signum, frame):
        running["flag"] = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    out = open(args.out, "a", buffering=1)
    out.write(json.dumps({**stamp(), "event": "observer_start",
                          "pattern": args.pattern,
                          "interval_ms": args.interval_ms}) + "\n")

    sys.stderr.write(f"GOOSE-CANARY-OBSERVER watching pattern={args.pattern} out={args.out}\n")
    sys.stderr.flush()

    while running["flag"]:
        try:
            pids = [e for e in os.listdir("/proc") if e.isdigit()]
        except OSError:
            break

        for entry in pids:
            pid = int(entry)
            if pid in seen:
                continue
            info = read_proc(pid)
            if info is None:
                continue
            cmdline, ppid = info
            if args.pattern not in cmdline:
                continue
            # Mark before writing so a slow write cannot double-record.
            seen.add(pid)
            count["n"] += 1
            out.write(json.dumps({
                **stamp(),
                "event": "process_spawned",
                "pid": pid,
                "ppid": ppid,
                "cmdline": cmdline[:2000],
                "ancestry": ancestry(ppid) if ppid else [],
            }) + "\n")

        time.sleep(interval)

    out.write(json.dumps({**stamp(), "event": "observer_stop",
                          "matched_processes": count["n"]}) + "\n")
    out.close()
    sys.stderr.write(f"GOOSE-CANARY-OBSERVER stopped, matched={count['n']}\n")


if __name__ == "__main__":
    main()
