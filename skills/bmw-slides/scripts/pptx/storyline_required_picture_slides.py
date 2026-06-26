#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
storyline_required_picture_slides.py - Print required picture slide numbers from storyline.

Output is comma-separated slide numbers for layouts: 0,1,13,14,18,19.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

SLIDE_RE = re.compile(r"^##\s+Slide\s+(\d+)\s+\[layout\s+(\d+)(?:[^\]]*)\]\s*$", re.IGNORECASE)
PICTURE_LAYOUTS = {0, 1, 13, 14, 18, 19}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Extract required picture slide numbers from storyline."
    )
    p.add_argument("storyline", help="Path to storyline markdown")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    lines = Path(args.storyline).read_text(encoding="utf-8").splitlines()
    req: list[int] = []
    for raw in lines:
        m = SLIDE_RE.match(raw.strip())
        if not m:
            continue
        slide_num = int(m.group(1))
        layout = int(m.group(2))
        if layout in PICTURE_LAYOUTS:
            req.append(slide_num)
    print(",".join(str(n) for n in req))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
