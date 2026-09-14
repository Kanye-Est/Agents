#!/usr/bin/env python3
"""Offline verification of the already completed ten-case calibration archive.

Read members in memory without extracting or executing any captured content.
The archive and summary are fixed. This is not another Goose/model attempt.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tarfile
from unittest.mock import patch

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(HERE))
import formal_baseline_contract as formal

ARCHIVE_SHA256 = "fe3d07ccc52fa97f2b16c893c0c9e9a71589a0efdcb675ef45d821fdfc1593f6"
PREFIX = "ta-wording-calibration-complete/"


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        raise SystemExit("Provide the preserved calibration archive path")
    archive = Path(args[0]).resolve(strict=True)
    with archive.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    formal.require(actual == ARCHIVE_SHA256, "offline_archive_hash")
    summary_raw = (HERE / formal.SUMMARY_RELATIVE_PATH).read_bytes()
    formal.require(formal.digest(summary_raw) == formal.SUMMARY_SHA256, "offline_summary_hash")
    summary = formal.strict_object(summary_raw, "summary")
    prompts = {
        cid: (HERE / Path(formal.SUITE_RELATIVE_PATH).parent / "cases" / cid / "prompt.txt").read_bytes()
        for cid in formal.CASE_IDS
    }
    references = {}
    with tarfile.open(archive, "r:gz") as saved:
        members = saved.getmembers()
        formal.require(len({m.name for m in members}) == len(members), "offline_duplicate_member")
        formal.require(PREFIX + formal.REPAIR_DIRECTORY + "/STOP.json" not in saved.getnames(),
                       "offline_unresolved_repair_stop")

        def read_evidence(path):
            relative = Path(path).relative_to(formal.CALIBRATION_BATCH).as_posix()
            name = PREFIX + relative
            member = saved.getmember(name)
            formal.require(member.isfile(), "offline_nonregular_evidence", name)
            with saved.extractfile(member) as stream:
                raw = stream.read()
            references[name] = {"bytes": len(raw), "sha256": formal.digest(raw)}
            return raw

        with patch("socket.create_connection", side_effect=AssertionError("No network")), \
             patch("subprocess.run", side_effect=AssertionError("No commands")), \
             patch("subprocess.Popen", side_effect=AssertionError("No processes")):
            selected = formal._verify_summary(
                summary, prompts, calibration_batch=formal.CALIBRATION_BATCH,
                evidence_reader=read_evidence,
            )
    formal.require(len(references) == 104, "offline_reference_count")
    formal.require(selected == "C04", "offline_selected_case")
    print(json.dumps({
        "run": 0, "scope": "offline replay of preserved calibration evidence; no model requests",
        "passed": True, "archive_sha256": actual, "summary_sha256": formal.digest(summary_raw),
        "cases_replayed": 10, "unique_referenced_members_verified": len(references),
        "selected_case_id": selected, "references": references,
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
