#!/usr/bin/env python3
"""Offline tests of source-transition and no-retry guards; never starts Goose."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import calibration_resume as resume


class ResumeGuards(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.batch, self.source = self.root / "batch", self.root / "source"
        self.batch.mkdir(); self.source.mkdir()
        self.repair = self.batch / resume.DIRECTORY
        self.repair.mkdir()
        self.original_stop = b'{"case_id":"C04","status":"STOP"}\n'
        (self.batch / "STOP.json").write_bytes(self.original_stop)
        (self.source / "score_baseline.py").write_text("# protected scorer\n")
        (self.source / "calibration_observations.py").write_text("# repaired observer\n")
        old = self.batch / "instruments"
        old.mkdir()
        (old / "score_baseline.py").write_bytes((self.source / "score_baseline.py").read_bytes())
        (old / "calibration_observations.py").write_text("# old observer\n")
        original = {"git_commit": resume.ORIGINAL_COMMIT, "suite_sha256": resume.ORIGINAL_SUITE,
                    "sources": [{"relative_path": p.name, "sha256": resume.sha(p)} for p in sorted(old.iterdir())]}
        self.put(self.batch / "batch-init.json", {"source_freeze": original})
        self.manifest = {"git_commit": "repaired-commit", "manifest_sha256": "repaired-manifest",
                         "suite_sha256": resume.ORIGINAL_SUITE,
                         "sources": [{"relative_path": p.name, "sha256": resume.sha(p)} for p in sorted(self.source.iterdir())]}
        (self.source / "SHA256SUMS").write_text("fixture manifest\n")
        for index in range(1, 11):
            stage = self.batch / "cases" / f"C{index:02d}"
            stage.mkdir(parents=True)
            if index > 4:
                continue
            self.put(stage / "case-attempt.json", {"source_commit": resume.ORIGINAL_COMMIT})
            for name in ("baseline-score.json", "envelope-audit.json", "http.json", "request-invariants.json"):
                self.put(stage / name, {"case": index, "file": name})
            self.put(stage / "trajectory/capture_manifest.json", {"case": index})
            self.put(stage / "calibration-observation.json", {"status": "stopped" if index == 4 else "observed"})
            observed = stage / "calibration-observation.json"
            if index == 4:
                observed = resume.corrected_observation(self.batch)
                self.put(observed, {"status": "observed", "tool_natural": True,
                         "actual_tool_call_count": 1, "task_completed": False, "outer_fenced": True,
                         "sources": {label: {"path": str(stage / rel), "sha256": resume.sha(stage / rel)}
                                     for label, rel in (("score", "baseline-score.json"),
                                         ("capture_manifest", "trajectory/capture_manifest.json"),
                                         ("envelope", "envelope-audit.json"))}})
            self.put(stage / "bounded-review.json", {"case_id": f"C{index:02d}",
                     "allow_next_preregistered_case": True, "observation_path": str(observed),
                     "observation_sha256": resume.sha(observed),
                     "envelope_sha256": resume.sha(stage / "envelope-audit.json")})
        anchors = {relative: resume.sha(self.batch / relative) for relative in resume.ORIGINAL_EVIDENCE}
        self.anchor_patch = patch.dict(resume.ORIGINAL_EVIDENCE, anchors, clear=True)
        self.anchor_patch.start(); self.addCleanup(self.anchor_patch.stop)

    @staticmethod
    def put(path, obj):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj) + "\n")

    def record(self):
        return resume.record_repair(self.batch, self.manifest, self.source, {})

    def test_record_and_load_preserve_stop_and_snapshot(self):
        result = self.record()
        self.assertEqual(result["authorized_remaining_cases"], ["C05", "C06", "C07", "C08", "C09", "C10"])
        self.assertEqual((self.batch / "STOP.json").read_bytes(), self.original_stop)
        self.assertEqual(resume.load_repair(self.batch, self.manifest, self.source, "C05"), result)
        self.assertEqual((self.repair / "instruments/calibration_observations.py").read_bytes(),
                         (self.source / "calibration_observations.py").read_bytes())

    def test_prior_cases_cannot_be_retried(self):
        self.record()
        for cid in ("C01", "C02", "C03", "C04", "C11"):
            with self.subTest(case=cid), self.assertRaisesRegex(RuntimeError, "untouched C05-C10"):
                resume.load_repair(self.batch, self.manifest, self.source, cid)

    def test_record_cannot_be_overwritten(self):
        self.record()
        with self.assertRaisesRegex(RuntimeError, "already recorded"):
            self.record()

    def test_prior_stop_cannot_be_removed_or_changed(self):
        self.record()
        (self.batch / "STOP.json").write_text("changed\n")
        with self.assertRaisesRegex(RuntimeError, "Original stopped evidence changed"):
            resume.load_repair(self.batch, self.manifest, self.source, "C05")

    def test_new_stop_blocks_resume(self):
        self.record()
        self.put(self.repair / "STOP.json", {"status": "STOP"})
        with self.assertRaisesRegex(RuntimeError, "continuation is stopped"):
            resume.load_repair(self.batch, self.manifest, self.source, "C05")

    def test_protected_scorer_change_is_rejected(self):
        (self.source / "score_baseline.py").write_text("# changed scorer\n")
        with self.assertRaisesRegex(RuntimeError, "Protected measurement source changed"):
            self.record()

    def test_source_commit_and_manifest_changes_are_rejected(self):
        self.record()
        for key in ("git_commit", "manifest_sha256", "suite_sha256"):
            changed = copy.deepcopy(self.manifest); changed[key] = "unexpected"
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                resume.load_repair(self.batch, changed, self.source, "C05")

    def test_old_commit_cannot_claim_repair(self):
        self.manifest["git_commit"] = resume.ORIGINAL_COMMIT
        with self.assertRaisesRegex(RuntimeError, "new committed source freeze"):
            self.record()

    def test_c04_original_report_change_is_rejected(self):
        (self.batch / "cases/C04/baseline-score.json").write_text("{}\n")
        with self.assertRaisesRegex(RuntimeError, "Original stopped evidence changed"):
            self.record()

    def test_replay_cannot_change_task_outcome(self):
        path = resume.corrected_observation(self.batch)
        value = resume.read(path); value["task_completed"] = True; self.put(path, value)
        with self.assertRaisesRegex(RuntimeError, "preserve the saved raw observations"):
            self.record()

    def test_c04_replay_source_hash_must_match(self):
        path = resume.corrected_observation(self.batch)
        value = resume.read(path); value["sources"]["score"]["sha256"] = "wrong"; self.put(path, value)
        with self.assertRaisesRegex(RuntimeError, "original report"):
            self.record()

    def test_c04_review_must_bind_corrected_report(self):
        path = self.batch / "cases/C04/bounded-review.json"
        value = resume.read(path); value["observation_sha256"] = "wrong"; self.put(path, value)
        with self.assertRaisesRegex(RuntimeError, "bound root review"):
            self.record()

    def test_record_rejects_previously_attempted_remaining_case(self):
        self.put(self.batch / "cases/C05/case-attempt.json", {"already": True})
        with self.assertRaisesRegex(RuntimeError, "already been attempted"):
            self.record()

    def test_post_record_historical_evidence_change_is_rejected(self):
        self.record()
        (self.batch / "cases/C01/baseline-score.json").write_text("{}\n")
        with self.assertRaisesRegex(RuntimeError, "Recorded repair evidence changed"):
            resume.load_repair(self.batch, self.manifest, self.source, "C05")


if __name__ == "__main__":
    unittest.main(verbosity=2)
