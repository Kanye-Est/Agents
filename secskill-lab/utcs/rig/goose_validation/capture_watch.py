#!/usr/bin/env python3
"""Preserve Goose v1.45.0 request-log inodes without modifying their contents.

Goose creates state/logs/llm_request.<UUID-v4>.jsonl, closes/flushed its
BufWriter, then rotates names llm_request.0.jsonl through .9.jsonl.  This
collector watches that directory directly (CLI logs in child directories
are unrelated).  Hard links keep each captured inode after rotation.

Start before Goose and wait for ready-file.  Create stop-file only after
the Goose process tree has exited.  Capture/ordering/overflow/closure
errors produce a nonzero result.  This preserves provider logs; it does
not claim those logs are raw HTTP or sufficient trajectory evidence.
"""
import argparse
import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import select
import signal
import stat
import struct
import sys
import time

IN_MODIFY = 0x00000002
IN_CLOSE_WRITE = 0x00000008
IN_MOVED_FROM = 0x00000040
IN_MOVED_TO = 0x00000080
IN_CREATE = 0x00000100
IN_DELETE = 0x00000200
IN_DELETE_SELF = 0x00000400
IN_MOVE_SELF = 0x00000800
IN_UNMOUNT = 0x00002000
IN_Q_OVERFLOW = 0x00004000
IN_IGNORED = 0x00008000
IN_ISDIR = 0x40000000
IN_ONLYDIR = 0x01000000
IN_DONT_FOLLOW = 0x02000000
WATCH_MASK = (IN_MODIFY | IN_CLOSE_WRITE | IN_MOVED_FROM | IN_MOVED_TO |
              IN_CREATE | IN_DELETE | IN_DELETE_SELF | IN_MOVE_SELF |
              IN_UNMOUNT | IN_ONLYDIR | IN_DONT_FOLLOW)
HEADER = struct.Struct("iIII")
UUID_RE = re.compile(
    r"^llm_request\.([0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12})\.jsonl$")
SLOT_RE = re.compile(r"^llm_request\.([0-9])\.jsonl$")
AT_FDCWD = -100
AT_SYMLINK_FOLLOW = 0x400
LIBC = ctypes.CDLL(None, use_errno=True)
LIBC.inotify_init1.argtypes = [ctypes.c_int]
LIBC.inotify_init1.restype = ctypes.c_int
LIBC.inotify_add_watch.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
LIBC.inotify_add_watch.restype = ctypes.c_int
LIBC.linkat.argtypes = [
    ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
LIBC.linkat.restype = ctypes.c_int


def candidate(name):
    return name.startswith("llm_request.") and name.endswith(".jsonl")


def request_name(name):
    return bool(UUID_RE.fullmatch(name) or SLOT_RE.fullmatch(name))


def parse_events(data):
    result, pos = [], 0
    while pos < len(data):
        if len(data) - pos < HEADER.size:
            raise ValueError("truncated inotify event header")
        wd, mask, cookie, length = HEADER.unpack_from(data, pos)
        pos += HEADER.size
        if len(data) - pos < length:
            raise ValueError("truncated inotify event name")
        raw = data[pos:pos + length]
        if length and b"\0" not in raw:
            raise ValueError("unterminated inotify event name")
        name = os.fsdecode(raw.split(b"\0", 1)[0])
        result.append((wd, mask, cookie, name))
        pos += length
    return result


def atomic_json(path, value):
    path = Path(path)
    temp = path.with_name(path.name + "." + str(os.getpid()) + ".writing")
    with temp.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)
    directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


class Capture:
    def __init__(self, logs_dir, output_dir, ready_file, result_file, stop_file):
        self.logs = Path(logs_dir).absolute()
        self.output = Path(output_dir).absolute()
        self.ready_file = Path(ready_file).absolute()
        self.result_file = Path(result_file).absolute()
        self.stop_file = Path(stop_file).absolute()
        self.fd = None
        self.wd = None
        self.ready_ns = None
        self.initial_source_files = []
        self.errors = []
        self.locations = {}      # current source name -> logical request ID
        self.objects = {}        # request ID -> {inode, closed}
        self.moves = {}          # inotify rename cookie -> request ID
        self.captured = {}       # (device, inode) -> preserved path/provenance
        self.owners = {}         # (device, inode) -> request ID
        self.uuid_hints = {}     # UUID names cannot be reused by this producer
        self.final_scan_complete = False
        self.files = []
        self.interrupted = None

    def error(self, message):
        if message not in self.errors:
            self.errors.append(message)

    def prepare(self):
        if sys.platform != "linux":
            raise RuntimeError("Linux inotify is required")
        if not stat.S_ISDIR(self.logs.lstat().st_mode):
            raise RuntimeError("logs-dir must be an existing real directory")
        self.logs = self.logs.resolve(strict=True)
        self.output.mkdir(parents=True, exist_ok=True)
        if not stat.S_ISDIR(self.output.lstat().st_mode):
            raise RuntimeError("output-dir must be a real directory")
        self.output = self.output.resolve(strict=True)
        if self.output == self.logs or self.output.is_relative_to(self.logs):
            raise RuntimeError("output-dir must be outside logs-dir")
        if any(self.output.iterdir()):
            raise RuntimeError("output-dir must be empty")
        if self.logs.stat().st_dev != self.output.stat().st_dev:
            raise RuntimeError("hard-link evidence must be on the same filesystem")
        for path in (self.ready_file, self.result_file, self.stop_file):
            if path.exists() or path.is_symlink():
                raise RuntimeError("control/result path already exists: " + str(path))
            if path.resolve().is_relative_to(self.logs):
                raise RuntimeError("control/result files must be outside logs-dir")
            path.parent.mkdir(parents=True, exist_ok=True)
        if len({self.ready_file, self.result_file, self.stop_file}) != 3:
            raise RuntimeError("control/result paths must be distinct")
        self.fd = LIBC.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
        if self.fd < 0:
            raise OSError(ctypes.get_errno(), "inotify_init1")
        self.wd = LIBC.inotify_add_watch(
            self.fd, os.fsencode(self.logs), WATCH_MASK)
        if self.wd < 0:
            raise OSError(ctypes.get_errno(), "inotify_add_watch")
        initial = self.snapshot()
        self.initial_source_files = sorted(str(self.logs / name) for name in initial)
        for name, key in initial.items():
            token = self.owners.get(key, "initial:" + name)
            if token not in self.objects:
                self.objects[token] = {
                    "inode": None, "closed": bool(SLOT_RE.fullmatch(name))}
            self.locations[name] = token
            self.bind(token, key)
        events = self.read_all()
        if any(mask & (IN_Q_OVERFLOW | IN_DELETE_SELF | IN_MOVE_SELF |
                       IN_UNMOUNT | IN_IGNORED) or candidate(name)
               for _, mask, _, name in events):
            self.error("source changed during bootstrap; readiness not established")
        if self.errors:
            raise RuntimeError("bootstrap did not establish a stable source")
        self.ready_ns = time.time_ns()
        atomic_json(self.ready_file, {"ready_ns": self.ready_ns, "pid": os.getpid()})

    def capture_name(self, name):
        path = self.logs / name
        try:
            source_fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
        except FileNotFoundError:
            return None  # Resolve a concurrent rename using cookies and a later scan.
        except OSError as exc:
            self.error("open failed for " + str(path) + ": " + repr(exc))
            return None
        try:
            observed = os.fstat(source_fd)
            if not stat.S_ISREG(observed.st_mode):
                self.error("request log is not a regular file: " + str(path))
                return None
            key = (observed.st_dev, observed.st_ino)
            if key not in self.captured:
                preserved = self.output / (
                    "llm_request.d" + str(key[0]) + ".i" + str(key[1]) + ".jsonl")
                # linkat follows this process's fd magic link.  It therefore links
                # the inode we opened, even if the source name was rotated/reused.
                rc = LIBC.linkat(
                    AT_FDCWD, os.fsencode("/proc/self/fd/" + str(source_fd)),
                    AT_FDCWD, os.fsencode(preserved), AT_SYMLINK_FOLLOW)
                if rc != 0:
                    err = ctypes.get_errno()
                    self.error("hard-link failed for " + str(path) +
                               " inode=" + repr(key) + ": " +
                               repr(OSError(err, os.strerror(err))))
                    return None
                linked = preserved.lstat()
                if (linked.st_dev, linked.st_ino) != key or not stat.S_ISREG(linked.st_mode):
                    self.error("preserved inode identity mismatch: " + str(preserved))
                    return None
                self.captured[key] = {"path": preserved, "source_paths": set()}
            self.captured[key]["source_paths"].add(str(path))
            if UUID_RE.fullmatch(name):
                previous = self.uuid_hints.get(name)
                if previous is not None and previous != key:
                    self.error("UUID filename reused for another inode: " + name)
                self.uuid_hints[name] = key
            return key
        finally:
            os.close(source_fd)

    def bind(self, token, key):
        obj = self.objects[token]
        if obj["inode"] is not None and obj["inode"] != key:
            self.error("request mapped to inconsistent inodes: " + token)
            return
        owner = self.owners.get(key)
        if owner is not None and owner != token:
            self.error("distinct request IDs share an inode: " + token + " / " + owner)
            return
        obj["inode"] = key
        self.owners[key] = token

    def snapshot(self):
        found = {}
        try:
            entries = list(os.scandir(self.logs))
        except OSError as exc:
            self.error("source directory scan failed: " + repr(exc))
            return found
        for entry in sorted(entries, key=lambda item: item.name):
            name = entry.name
            if not candidate(name):
                continue
            if not request_name(name):
                self.error("unexpected request-log filename: " + name)
                continue
            key = self.capture_name(name)
            if key is not None:
                found[name] = key
        return found

    def read_all(self):
        events = []
        while self.fd is not None:
            try:
                data = os.read(self.fd, 65536)
            except BlockingIOError:
                break
            except InterruptedError:
                continue
            if not data:
                self.error("unexpected EOF from inotify")
                break
            events.extend(parse_events(data))
        return events

    def process(self, events):
        for wd, mask, cookie, name in events:
            if mask & IN_Q_OVERFLOW:
                self.error("IN_Q_OVERFLOW: event continuity lost")
                continue
            if wd != self.wd:
                self.error("unexpected inotify watch descriptor: " + str(wd))
                continue
            if mask & (IN_DELETE_SELF | IN_MOVE_SELF | IN_UNMOUNT | IN_IGNORED):
                self.error("watched directory changed or watch lost: mask=" + hex(mask))
                continue
            if not candidate(name):
                continue
            if not request_name(name) or mask & IN_ISDIR:
                self.error("unexpected request-log object: " + name)
                continue
            if mask & IN_CREATE:
                if not UUID_RE.fullmatch(name):
                    self.error("numeric slot created outside normal rotation: " + name)
                    continue
                if name in self.objects or name in self.locations:
                    self.error("duplicate request creation: " + name)
                    continue
                self.objects[name] = {"inode": None, "closed": False}
                self.locations[name] = name
                key = self.uuid_hints.get(name)
                if key is None:
                    key = self.capture_name(name)
                if key is not None:
                    self.bind(name, key)
            if mask & IN_MODIFY:
                token = self.locations.get(name)
                if token is None:
                    self.error("modification without a tracked request: " + name)
                elif self.objects[token]["closed"]:
                    self.error("request modified after writer closed: " + token)
            if mask & IN_CLOSE_WRITE:
                token = self.locations.get(name)
                if token is None:
                    self.error("writer-close without a tracked request: " + name)
                else:
                    self.objects[token]["closed"] = True
            if mask & IN_MOVED_FROM:
                token = self.locations.pop(name, None)
                if token is None or not cookie or cookie in self.moves:
                    self.error("unresolved rename source/cookie: " + name)
                else:
                    self.moves[cookie] = token
            if mask & IN_MOVED_TO:
                token = self.moves.pop(cookie, None)
                if token is None:
                    self.error("rename destination lacks its source: " + name)
                else:
                    # A rename may replace an old numeric slot.  Its captured
                    # inode remains in evidence even though that name is lost.
                    self.locations[name] = token
            if mask & IN_DELETE:
                self.locations.pop(name, None)

    def stable_scan(self, timeout=5.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.process(self.read_all())
            found = self.snapshot()
            after = self.read_all()
            if after:
                self.process(after)
                if self.errors:
                    return None
                continue
            if self.errors:
                return None
            if self.moves or set(found) != set(self.locations):
                # The filesystem mutation and delivery of its event can straddle
                # this scan.  Do not attribute a reused numeric name prematurely.
                select.select([self.fd], [], [], 0.01)
                continue
            for name, key in found.items():
                self.bind(self.locations[name], key)
            return found if not self.errors else None
        self.error("could not reconcile event history with a stable directory scan")
        return None

    def hash_file(self, key, record):
        path = record["path"]
        fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
        try:
            before = os.fstat(fd)
            if (before.st_dev, before.st_ino) != key or not stat.S_ISREG(before.st_mode):
                raise RuntimeError("preserved inode changed")
            digest = hashlib.sha256()
            while True:
                block = os.read(fd, 1024 * 1024)
                if not block:
                    break
                digest.update(block)
            after = os.fstat(fd)
            signature = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
            if signature(before) != signature(after):
                raise RuntimeError("file changed while computing its digest")
            return {
                "path": str(path), "sha256": digest.hexdigest(),
                "device": key[0], "inode": key[1], "size": after.st_size,
                "source_paths": sorted(record["source_paths"]),
            }
        finally:
            os.close(fd)

    def finish(self):
        before = self.stable_scan() if self.fd is not None and self.wd is not None else None
        if self.moves:
            self.error("unpaired rename cookies at completion")
        for token, obj in self.objects.items():
            if obj["inode"] is None:
                self.error("request inode was not recoverable: " + token)
            if not obj["closed"]:
                self.error("request writer closure not observed: " + token)
        for key in self.captured:
            if key not in self.owners:
                self.error("captured inode cannot be attributed to a request: " + repr(key))
        self.files = []
        for key, record in sorted(self.captured.items()):
            try:
                self.files.append(self.hash_file(key, record))
            except Exception as exc:
                self.error("final evidence hash failed: " + repr(key) + ": " + repr(exc))
        if self.fd is not None:
            late = self.read_all()
            if late:
                self.process(late)
                self.error("source events arrived during final hashing")
            after = self.snapshot()
            late_after_scan = self.read_all()
            if late_after_scan:
                self.process(late_after_scan)
                self.error("source events arrived during final verification")
            if before is None or after != before:
                self.error("final source scan did not remain stable")
        self.final_scan_complete = (
            self.ready_ns is not None and before is not None and
            len(self.files) == len(self.captured) and not self.errors)

    def result(self):
        return {
            "ready_ns": self.ready_ns,
            "finished_ns": time.time_ns(),
            "exit_code": 0 if self.final_scan_complete and not self.errors else 1,
            "initial_source_files": self.initial_source_files,
            "final_scan_complete": self.final_scan_complete,
            "errors": self.errors,
            "files": self.files,
        }

    def run(self):
        try:
            self.prepare()
            while not self.stop_file.exists() and not self.errors:
                if self.interrupted is not None:
                    self.error("collector interrupted by signal " + str(self.interrupted))
                    break
                self.stable_scan()
                if not self.errors:
                    select.select([self.fd], [], [], 0.05)
        except Exception as exc:
            self.error("capture exception: " + repr(exc))
        try:
            self.finish()
        except Exception as exc:
            self.error("completion exception: " + repr(exc))
            self.final_scan_complete = False
        finally:
            if self.fd is not None:
                os.close(self.fd)
                self.fd = None
        result = self.result()
        try:
            if self.result_file.exists() or self.result_file.is_symlink():
                raise RuntimeError("refusing to overwrite existing result")
            atomic_json(self.result_file, result)
        except Exception as exc:
            print("could not write capture result: " + repr(exc), file=sys.stderr)
            return 1
        print(json.dumps(result, ensure_ascii=False))
        return result["exit_code"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("logs-dir", "output-dir", "ready-file", "result-file", "stop-file"):
        parser.add_argument("--" + option, required=True)
    args = parser.parse_args(argv)
    os.umask(0o077)
    watch = Capture(args.logs_dir, args.output_dir, args.ready_file,
                    args.result_file, args.stop_file)
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda received, frame: setattr(watch, "interrupted", received))
    return watch.run()


if __name__ == "__main__":
    sys.exit(main())
