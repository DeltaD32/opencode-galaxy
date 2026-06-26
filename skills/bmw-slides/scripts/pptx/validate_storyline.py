#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
validate_storyline.py - Validate storyline minimum quality gates before build.

Checks:
1. Slide 1 must be layout 0 or 19 (title page).
2. At least one picture layout exists (0,1,13,14,18,19).
3. Picture-required slides (0,1,13,14,18,19) must define **Image:**.
4. Output path is present.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

SLIDE_RE = re.compile(r"^##\s+Slide\s+(\d+)\s+\[layout\s+(\d+)(?:[^\]]*)\]\s*$", re.IGNORECASE)
OUTPUT_RE = re.compile(r"^Output:\s+(.+)\s*$", re.IGNORECASE)
IMAGE_RE = re.compile(r"^\*\*Image:\*\*\s+(.+)\s*$")
PIC_LAYOUTS = {0, 1, 13, 14, 18, 19}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate bmw-pptx storyline format and gates.")
    p.add_argument("storyline", help="Path to storyline .md file")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    text = Path(args.storyline).read_text(encoding="utf-8")
    lines = text.splitlines()

    output_path = ""
    slides: list[dict] = []
    current: dict | None = None

    for raw in lines:
        m_out = OUTPUT_RE.match(raw.strip())
        if m_out:
            output_path = m_out.group(1).strip()

        m_slide = SLIDE_RE.match(raw.strip())
        if m_slide:
            if current is not None:
                slides.append(current)
            current = {
                "num": int(m_slide.group(1)),
                "layout": int(m_slide.group(2)),
                "image": "",
            }
            continue

        if current is not None:
            m_img = IMAGE_RE.match(raw.strip())
            if m_img:
                current["image"] = m_img.group(1).strip()

    if current is not None:
        slides.append(current)

    errors: list[str] = []

    if not output_path:
        errors.append("Missing `Output:` path.")

    if not slides:
        errors.append("No `## Slide N [layout X]` entries found.")
    else:
        first = slides[0]
        if first["layout"] not in {0, 19}:
            errors.append(
                f"Slide 1 must be layout 0 or 19 (title page), found layout {first['layout']}."
            )

    if slides and not any(s["layout"] in PIC_LAYOUTS for s in slides):
        errors.append("At least one picture layout is required (0,1,13,14,18,19).")

    for s in slides:
        if s["layout"] in PIC_LAYOUTS and not s["image"]:
            errors.append(f"Slide {s['num']} uses layout {s['layout']} and requires `**Image:**`.")

    if errors:
        print("Storyline validation FAILED:")
        for e in errors:
            print(f"- {e}")
        return 1

    print("Storyline validation OK.")
    print(f"Slides: {len(slides)}")
    print(f"Output: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
