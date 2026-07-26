"""Generate a real QR PNG using the frozen qrcode dependency."""

from __future__ import annotations

import os
from pathlib import Path

import qrcode


def run(args):
    values = args or {}
    payload = str(values.get("text", "")).strip() or "MISSING_QR_PAYLOAD"
    root = Path(os.environ["ACQUISITION_ARTIFACT_DIR"]).resolve()
    root.mkdir(parents=True, exist_ok=True)
    path = root / "pilot_qr.png"
    image = qrcode.make(payload)
    image.save(path)
    return f"ARTIFACT_CREATED path={path} type=image/png"
