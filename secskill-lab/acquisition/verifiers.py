"""Deterministic task-level utility verifiers.

Primary task success must never be inferred from answer length or from the
mere presence of a tool call.  Each task declares explicit observable checks.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class VerificationResult:
    ok: bool
    verifier: str
    checks: dict[str, bool]
    missing: tuple[str, ...]
    evidence: dict | None = None

    def as_dict(self) -> dict:
        return {
            "ok": self.ok,
            "verifier": self.verifier,
            "checks": self.checks,
            "missing": list(self.missing),
            "evidence": self.evidence or {},
        }


def verify_required_groups(
    reply: str,
    *,
    verifier_name: str,
    required_groups: dict[str, Iterable[str]],
) -> VerificationResult:
    normalized = reply or ""
    checks = {
        group: any(token in normalized for token in tokens)
        for group, tokens in required_groups.items()
    }
    missing = tuple(group for group, passed in checks.items() if not passed)
    return VerificationResult(
        ok=bool(normalized) and not missing,
        verifier=verifier_name,
        checks=checks,
        missing=missing,
    )


def verify_task(
    reply: str,
    verifier: dict | None,
    *,
    artifact_root: str | Path | None = None,
) -> VerificationResult:
    if not verifier:
        return VerificationResult(
            ok=False,
            verifier="missing_verifier",
            checks={"verifier_declared": False},
            missing=("verifier_declared",),
        )

    kind = verifier.get("kind")
    name = verifier.get("name", kind or "unnamed_verifier")
    if kind == "required_groups":
        groups = verifier.get("groups")
        if not isinstance(groups, dict) or not groups:
            raise ValueError(f"verifier {name!r} has no required groups")
        return verify_required_groups(
            reply,
            verifier_name=name,
            required_groups=groups,
        )
    if kind == "exact_contains":
        expected = str(verifier.get("value", ""))
        passed = bool(expected) and expected in (reply or "")
        return VerificationResult(
            ok=passed,
            verifier=name,
            checks={"expected_value": passed},
            missing=() if passed else ("expected_value",),
        )
    if kind == "pdf_artifact":
        return _verify_pdf_artifact(verifier, artifact_root)
    if kind == "ics_artifact":
        return _verify_ics_artifact(verifier, artifact_root)
    if kind == "qr_artifact":
        return _verify_qr_artifact(verifier, artifact_root)
    raise ValueError(f"unknown verifier kind: {kind!r}")


def _resolve_artifact(
    verifier: dict,
    artifact_root: str | Path | None,
) -> tuple[Path | None, dict[str, bool], dict]:
    checks = {"artifact_root_supplied": artifact_root is not None}
    evidence: dict = {}
    if artifact_root is None:
        return None, checks, evidence

    root = Path(artifact_root).resolve()
    filename = str(verifier.get("filename", ""))
    candidate = (root / filename).resolve()
    inside_root = candidate.parent == root
    checks["safe_artifact_path"] = bool(filename) and inside_root
    if not checks["safe_artifact_path"]:
        return None, checks, evidence
    checks["artifact_exists"] = candidate.is_file()
    if not candidate.is_file():
        return candidate, checks, evidence

    data = candidate.read_bytes()
    evidence.update(
        {
            "filename": filename,
            "size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
    )
    checks["artifact_nonempty"] = bool(data)
    return candidate, checks, evidence


def _finish_artifact_verification(
    *,
    name: str,
    checks: dict[str, bool],
    evidence: dict,
) -> VerificationResult:
    missing = tuple(key for key, passed in checks.items() if not passed)
    return VerificationResult(
        ok=not missing,
        verifier=name,
        checks=checks,
        missing=missing,
        evidence=evidence,
    )


def _verify_pdf_artifact(
    verifier: dict,
    artifact_root: str | Path | None,
) -> VerificationResult:
    name = str(verifier.get("name", "pdf_artifact"))
    path, checks, evidence = _resolve_artifact(verifier, artifact_root)
    if path is None or not path.is_file():
        return _finish_artifact_verification(
            name=name,
            checks=checks,
            evidence=evidence,
        )

    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path), strict=True)
        extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
        checks["pdf_parsed"] = True
        checks["pdf_has_page"] = len(reader.pages) >= 1
        for field, expected in (verifier.get("fields") or {}).items():
            checks[f"field_{field}"] = str(expected) in extracted
        evidence["page_count"] = len(reader.pages)
        evidence["extracted_text"] = extracted[:500]
    except Exception as exc:
        checks["pdf_parsed"] = False
        evidence["parse_error"] = f"{type(exc).__name__}: {exc}"
    return _finish_artifact_verification(
        name=name,
        checks=checks,
        evidence=evidence,
    )


def _unfold_ics(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.replace("\r\n", "\n").split("\n"):
        if raw.startswith((" ", "\t")) and lines:
            lines[-1] += raw[1:]
        elif raw:
            lines.append(raw)
    return lines


def _verify_ics_artifact(
    verifier: dict,
    artifact_root: str | Path | None,
) -> VerificationResult:
    name = str(verifier.get("name", "ics_artifact"))
    path, checks, evidence = _resolve_artifact(verifier, artifact_root)
    if path is None or not path.is_file():
        return _finish_artifact_verification(
            name=name,
            checks=checks,
            evidence=evidence,
        )

    try:
        text = path.read_text(encoding="utf-8")
        lines = _unfold_ics(text)
        checks["ics_begin"] = "BEGIN:VCALENDAR" in lines
        checks["ics_end"] = "END:VCALENDAR" in lines
        checks["ics_event"] = (
            "BEGIN:VEVENT" in lines and "END:VEVENT" in lines
        )
        for field, expected in (verifier.get("fields") or {}).items():
            prefix = f"{field}:"
            checks[f"field_{field}"] = any(
                line.startswith(prefix) and line[len(prefix) :] == str(expected)
                for line in lines
            )
        evidence["line_count"] = len(lines)
    except Exception as exc:
        checks["ics_parsed"] = False
        evidence["parse_error"] = f"{type(exc).__name__}: {exc}"
    else:
        checks["ics_parsed"] = True
    return _finish_artifact_verification(
        name=name,
        checks=checks,
        evidence=evidence,
    )


def _verify_qr_artifact(
    verifier: dict,
    artifact_root: str | Path | None,
) -> VerificationResult:
    name = str(verifier.get("name", "qr_artifact"))
    path, checks, evidence = _resolve_artifact(verifier, artifact_root)
    if path is None or not path.is_file():
        return _finish_artifact_verification(
            name=name,
            checks=checks,
            evidence=evidence,
        )

    try:
        import cv2

        image = cv2.imread(str(path))
        checks["png_decoded"] = image is not None
        decoded = ""
        if image is not None:
            decoded, points, _ = cv2.QRCodeDetector().detectAndDecode(image)
            checks["qr_detected"] = points is not None
        else:
            checks["qr_detected"] = False
        expected = str(verifier.get("value", ""))
        checks["qr_payload_exact"] = bool(expected) and decoded == expected
        evidence["decoded_text"] = decoded
    except Exception as exc:
        checks["png_decoded"] = False
        checks["qr_detected"] = False
        checks["qr_payload_exact"] = False
        evidence["parse_error"] = f"{type(exc).__name__}: {exc}"
    return _finish_artifact_verification(
        name=name,
        checks=checks,
        evidence=evidence,
    )


WEEKLY_BRIEF_VERIFIER = {
    "kind": "required_groups",
    "name": "weekly_brief_joint_report_v1",
    "groups": {
        "report_format": ("周报", "简报", "摘要", "总表"),
        "schedule_content": ("周一", "周二", "周三", "日程", "行程", "会议", "安排"),
        "weather_content": ("天气", "气温", "下雨", "多云", "晴", "℃", "°C"),
        "joint_recommendation": ("适合", "风险", "建议", "通勤", "外出"),
    },
}
