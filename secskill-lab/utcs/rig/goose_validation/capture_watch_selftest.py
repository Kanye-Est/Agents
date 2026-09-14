#!/usr/bin/env python3
"""Synthetic-only tests for capture_watch.py. No Goose, model, or network."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
import uuid

HERE = Path(__file__).resolve().parent
WATCHER = HERE / "capture_watch.py"
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("capture_watch_under_test", WATCHER)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def await_condition(predicate, timeout=8):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.01)
    raise AssertionError("condition did not become true before timeout")


class Fixture:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory(prefix="watch-selftest-", dir=HERE)
        self.root = Path(self.temp.name)
        self.logs = self.root / "logs"
        self.logs.mkdir()
        self.output = self.root / "preserved"
        self.ready = self.root / "ready.json"
        self.result = self.root / "result.json"
        self.stop = self.root / "stop"
        self.proc = None
        self.stdout = None
        self.stderr = None

    def start(self, expect_ready=True):
        self.stdout = (self.root / "collector.stdout").open("w")
        self.stderr = (self.root / "collector.stderr").open("w")
        command = [
            sys.executable, "-B", str(WATCHER),
            "--logs-dir", str(self.logs),
            "--output-dir", str(self.output),
            "--ready-file", str(self.ready),
            "--result-file", str(self.result),
            "--stop-file", str(self.stop),
        ]
        self.proc = subprocess.Popen(command, stdout=self.stdout, stderr=self.stderr)
        if expect_ready:
            await_condition(lambda: self.ready.exists() or self.proc.poll() is not None)
            if not self.ready.exists():
                raise AssertionError("watcher failed before ready: " + self.debug())
            ready = json.loads(self.ready.read_text())
            if not isinstance(ready["ready_ns"], int) or ready["pid"] != self.proc.pid:
                raise AssertionError("invalid readiness record")
        return self

    def debug(self):
        parts = []
        for name in ("collector.stdout", "collector.stderr", "result.json"):
            path = self.root / name
            if path.exists():
                parts.append(name + ": " + path.read_text())
        return "\n".join(parts)

    def pause(self):
        os.kill(self.proc.pid, signal.SIGSTOP)
        waited, status = os.waitpid(self.proc.pid, os.WUNTRACED)
        if waited != self.proc.pid or not os.WIFSTOPPED(status):
            raise AssertionError("could not pause synthetic collector")

    def resume(self):
        os.kill(self.proc.pid, signal.SIGCONT)

    def finish(self, expected=0, stopped_already=False):
        if not stopped_already:
            self.stop.write_text("synthetic producer finished\n")
        code = self.proc.wait(timeout=10)
        if code != expected:
            raise AssertionError("unexpected exit " + str(code) + "\n" + self.debug())
        if not self.result.exists():
            raise AssertionError("missing completion result\n" + self.debug())
        result = json.loads(self.result.read_text())
        if result["exit_code"] != code:
            raise AssertionError("result/OS exit mismatch")
        return result

    def produce(self, index, wait_for_link=True):
        name = "llm_request." + str(uuid.uuid4()) + ".jsonl"
        path = self.logs / name
        first = json.dumps({
            "model_config": {"model_name": "synthetic-only"},
            "input": {"messages": [{"role": "user", "content": "fixture " + str(index)}]},
        }, sort_keys=True) + "\n"
        second = json.dumps({"data": {"text": "complete " + str(index)}, "usage": None},
                            sort_keys=True) + "\n"
        with path.open("w", encoding="utf-8") as stream:
            stream.write(first)  # Intentionally buffered: inode is captured while empty.
            if wait_for_link:
                await_condition(lambda: path.stat().st_nlink >= 2)
            stream.write(second)
            stream.flush()
        for slot in reversed(range(9)):
            old = self.logs / ("llm_request." + str(slot) + ".jsonl")
            new = self.logs / ("llm_request." + str(slot + 1) + ".jsonl")
            if old.exists():
                old.rename(new)
        path.rename(self.logs / "llm_request.0.jsonl")
        return (first + second).encode("utf-8")

    def close(self):
        if self.proc is not None and self.proc.poll() is None:
            try:
                os.kill(self.proc.pid, signal.SIGCONT)
            except ProcessLookupError:
                pass
            self.proc.kill()
            self.proc.wait(timeout=5)
        for stream in (self.stdout, self.stderr):
            if stream is not None:
                stream.close()
        self.temp.cleanup()


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.fixture = Fixture()

    def tearDown(self):
        self.fixture.close()

    def assert_success(self, result, count):
        self.assertEqual(result["exit_code"], 0)
        self.assertTrue(result["final_scan_complete"])
        self.assertEqual(result["errors"], [])
        self.assertIsInstance(result["ready_ns"], int)
        self.assertGreaterEqual(result["finished_ns"], result["ready_ns"])
        self.assertEqual(len(result["files"]), count)
        keys = set()
        for item in result["files"]:
            path = Path(item["path"])
            self.assertTrue(path.is_absolute())
            info = path.stat()
            key = (info.st_dev, info.st_ino)
            self.assertEqual(key, (item["device"], item["inode"]))
            self.assertNotIn(key, keys)
            keys.add(key)
            content = path.read_bytes()
            self.assertEqual(item["sha256"], hashlib.sha256(content).hexdigest())
            self.assertEqual(item["size"], len(content))

    def test_24_rotations_preserve_final_buffered_contents(self):
        f = self.fixture.start()
        contents = [f.produce(index) for index in range(24)]
        result = f.finish()
        self.assert_success(result, 24)
        self.assertEqual(result["initial_source_files"], [])
        self.assertEqual(len(list(f.logs.glob("llm_request.*.jsonl"))), 10)
        self.assertEqual(
            {item["sha256"] for item in result["files"]},
            {hashlib.sha256(content).hexdigest() for content in contents})
        self.assertTrue(all(item["size"] > 0 for item in result["files"]))

    def test_create_already_renamed_and_final_drain(self):
        f = self.fixture.start()
        f.pause()
        contents = [f.produce(index, wait_for_link=False) for index in range(4)]
        f.stop.write_text("stop queued before collector resumes\n")
        f.resume()
        result = f.finish(stopped_already=True)
        self.assert_success(result, 4)
        self.assertEqual(
            {item["sha256"] for item in result["files"]},
            {hashlib.sha256(content).hexdigest() for content in contents})

    def test_unrecoverable_rotated_away_requests_fail(self):
        f = self.fixture.start()
        f.pause()
        for index in range(15):
            f.produce(index, wait_for_link=False)
        f.stop.write_text("some inodes lost before collector can link\n")
        f.resume()
        result = f.finish(expected=1, stopped_already=True)
        self.assertFalse(result["final_scan_complete"])
        self.assertTrue(any("not recoverable" in error for error in result["errors"]))
        self.assertLessEqual(len(result["files"]), 10)

    def test_duplicate_inode_initial_aliases_are_deduplicated(self):
        f = self.fixture
        one = f.logs / "llm_request.0.jsonl"
        two = f.logs / "llm_request.1.jsonl"
        one.write_text('{"synthetic":"initial alias"}\n')
        os.link(one, two)
        f.start()
        result = f.finish()
        self.assert_success(result, 1)
        self.assertEqual(result["initial_source_files"], sorted([str(one), str(two)]))
        # A trajectory adapter must still reject this fixture as a non-fresh profile.

    def test_open_writer_at_stop_is_not_complete(self):
        f = self.fixture.start()
        path = f.logs / ("llm_request." + str(uuid.uuid4()) + ".jsonl")
        with path.open("w") as writer:
            writer.write('{"synthetic":"writer still open"}\n')
            writer.flush()
            await_condition(lambda: path.stat().st_nlink >= 2)
            result = f.finish(expected=1)
        self.assertFalse(result["final_scan_complete"])
        self.assertTrue(any("writer closure" in error for error in result["errors"]))

    def test_symlink_request_is_rejected(self):
        f = self.fixture
        target = f.root / "unrelated-synthetic.txt"
        target.write_text("synthetic file outside log directory\n")
        name = f.logs / ("llm_request." + str(uuid.uuid4()) + ".jsonl")
        name.symlink_to(target)
        f.start(expect_ready=False)
        await_condition(lambda: f.result.exists() or f.proc.poll() is not None)
        result = f.finish(expected=1)
        self.assertIsNone(result["ready_ns"])
        self.assertFalse(f.ready.exists())
        self.assertFalse(result["final_scan_complete"])
        self.assertTrue(any("open failed" in error for error in result["errors"]))

    def test_source_directory_move_is_rejected(self):
        f = self.fixture.start()
        f.logs.rename(f.root / "logs-moved")
        result = f.finish(expected=1)
        self.assertFalse(result["final_scan_complete"])
        self.assertTrue(any("directory" in error for error in result["errors"]))

    def test_inotify_overflow_event_fails_closed(self):
        f = self.fixture
        watcher = module.Capture(f.logs, f.output, f.ready, f.result, f.stop)
        events = module.parse_events(module.HEADER.pack(-1, module.IN_Q_OVERFLOW, 0, 0))
        watcher.process(events)
        result = watcher.result()
        self.assertEqual(result["exit_code"], 1)
        self.assertFalse(result["final_scan_complete"])
        self.assertTrue(any("IN_Q_OVERFLOW" in error for error in result["errors"]))

    def test_truncated_inotify_records_are_rejected(self):
        with self.assertRaises(ValueError):
            module.parse_events(b"\0")
        with self.assertRaises(ValueError):
            module.parse_events(module.HEADER.pack(1, module.IN_CREATE, 0, 16) + b"short")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CaptureTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {
        "scope": "synthetic filesystem/inotify fixtures only; no Goose/model/network",
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "successful": result.wasSuccessful(),
        "watcher_sha256": hashlib.sha256(WATCHER.read_bytes()).hexdigest(),
        "selftest_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python_version": sys.version.split()[0],
    }
    print(json.dumps(report, indent=2))
    sys.exit(0 if result.wasSuccessful() else 1)
