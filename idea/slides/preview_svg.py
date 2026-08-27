#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render the present-ready preview PDF from the actual .pptx via LibreOffice.

History: earlier this script hand-rebuilt each slide as SVG because the machine
had no LibreOffice, so the preview only *approximated* the deck and could drift
from build_deck.py. LibreOffice (libreoffice-still-zh-cn) is now installed, so we
render the real .pptx instead — the preview is byte-faithful to what PowerPoint
shows and can never drift. Keeps the documented `python preview_svg.py` step.
"""
import os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PPTX = os.path.join(HERE, "组会_Do_Not_Mention_三篇.pptx")
OUT  = os.path.join(HERE, "组会_Do_Not_Mention_三篇_预览.pdf")
# isolated profile so this works even if a LibreOffice window is already open
PROFILE = "file:///tmp/lo_profile_deck_preview"
TMPDIR = "/tmp/deck_preview_out"

def main():
    if not os.path.exists(PPTX):
        sys.exit(f"missing {PPTX} — run build_deck.py first")
    soffice = shutil.which("libreoffice") or shutil.which("soffice")
    if not soffice:
        sys.exit("LibreOffice not found (install libreoffice-still-zh-cn)")
    os.makedirs(TMPDIR, exist_ok=True)
    subprocess.run(
        [soffice, f"-env:UserInstallation={PROFILE}", "--headless",
         "--convert-to", "pdf", "--outdir", TMPDIR, PPTX],
        check=True,
    )
    produced = os.path.join(TMPDIR, os.path.splitext(os.path.basename(PPTX))[0] + ".pdf")
    if not os.path.exists(produced):
        sys.exit("LibreOffice did not produce a PDF")
    shutil.move(produced, OUT)
    print("wrote", OUT)

if __name__ == "__main__":
    main()
