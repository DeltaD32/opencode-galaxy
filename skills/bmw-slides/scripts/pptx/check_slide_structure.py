#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "python-pptx",
# ]
# ///

"""
check_slide_structure.py - Structural gate for one slide before polish.

This check is intentionally non-visual and fast. Use it between build and polish
in the delivery inner loop to avoid unnecessary render/review cycles.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

PICTURE_LAYOUTS = {0, 1, 13, 14, 18, 19}

# Text-overflow heuristic constants
# Average character width as fraction of font-size EMU.
# BMW slides use BMWGroupTN Condensed — a narrow typeface whose glyphs are
# ~25% narrower than Calibri/Arial. 0.42 is calibrated for condensed fonts;
# use 0.55 for proportional fonts like Calibri.
AVG_CHAR_WIDTH_FACTOR = 0.42
LINE_HEIGHT_FACTOR = 1.35  # line spacing multiplier
DEFAULT_FONT_EMU = 14 * 12700  # Pt(14) in EMU
MIN_SHAPE_AREA_FOR_CHECK = 500000 * 500000  # skip tiny shapes (< ~1.4cm x 1.4cm)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Check structural quality of one slide.")
    p.add_argument("--pptx", required=True, help="Path to presentation")
    p.add_argument("--slide", required=True, type=int, help="1-based slide number")
    p.add_argument(
        "--layout",
        type=int,
        default=None,
        help="Expected layout index from storyline (optional, recommended)",
    )
    p.add_argument(
        "--require-picture",
        action="store_true",
        help="Require at least one picture shape on this slide.",
    )
    p.add_argument(
        "--json-out",
        default="",
        help="Optional output path for machine-readable gate result JSON.",
    )
    return p.parse_args()


def _contains_placeholder_prompt(slide) -> bool:
    for shp in slide.shapes:
        if not getattr(shp, "has_text_frame", False):
            continue
        txt = (shp.text_frame.text or "").strip().lower()
        if "click to add" in txt:
            return True
    return False


def _has_picture(slide) -> bool:
    for shp in slide.shapes:
        if shp.shape_type == MSO_SHAPE_TYPE.PICTURE:
            return True
    # Placeholder-based images may not always surface as PICTURE shapes.
    # Fallback: check slide XML for embedded image blips.
    xml = slide.part.blob
    if b"<a:blip" in xml and b"r:embed" in xml:
        return True
    return False


def _check_text_overflow(slide) -> list[str]:
    """Heuristic check for text that likely exceeds its container.

    For each shape with a text frame, estimates the number of lines needed
    based on character count, font size, and shape width.  Compares against
    the available height.  This is a rough approximation — false positives
    are possible but the check catches the worst offenders (10+ bullets in
    a narrow placeholder, walls of text in small boxes).
    """
    issues: list[str] = []

    for shp in slide.shapes:
        if not getattr(shp, "has_text_frame", False):
            continue

        w = int(shp.width)
        h = int(shp.height)

        # Skip tiny shapes and the title placeholder
        if w * h < MIN_SHAPE_AREA_FOR_CHECK:
            continue
        try:
            ph_fmt = shp.placeholder_format  # raises ValueError on non-placeholders
            if ph_fmt is not None and ph_fmt.idx == 0:
                continue
        except ValueError:
            pass  # not a placeholder — continue to overflow check

        tf = shp.text_frame
        total_text = (tf.text or "").strip()
        if not total_text:
            continue

        # Determine dominant font size (use the largest found, fall back to default)
        max_font_emu = 0
        for para in tf.paragraphs:
            if para.font.size is not None:
                max_font_emu = max(max_font_emu, int(para.font.size))
            for run in para.runs:
                if run.font.size is not None:
                    max_font_emu = max(max_font_emu, int(run.font.size))
        if max_font_emu == 0:
            max_font_emu = DEFAULT_FONT_EMU

        # Estimate lines needed
        char_width = max_font_emu * AVG_CHAR_WIDTH_FACTOR
        chars_per_line = max(1, int(w / char_width))
        line_height = max_font_emu * LINE_HEIGHT_FACTOR

        total_lines = 0
        for para in tf.paragraphs:
            para_text = para.text or ""
            # Each paragraph takes at least one line
            para_lines = max(1, -(-len(para_text) // chars_per_line))  # ceil division
            total_lines += para_lines

        estimated_height = total_lines * line_height

        # Flag if estimated text height exceeds shape height by >40%
        # (generous margin to avoid false positives)
        if estimated_height > h * 1.4:
            label = total_text[:40]
            issues.append(
                f"Likely text overflow in shape '{label}...' "
                f"(~{total_lines} lines estimated, shape fits ~{max(1, int(h / line_height))}). "
                "Reduce content, split across slides, or use a larger shape."
            )
            if len(issues) >= 2:
                break  # limit noise

    return issues


def _write_json_result(path: str, payload: dict) -> None:
    if not path:
        return
    out_path = Path(path).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def main() -> int:
    args = parse_args()
    pptx_path = Path(args.pptx).expanduser().resolve()
    prs = Presentation(str(pptx_path))

    if args.slide < 1 or args.slide > len(prs.slides):
        msg = f"slide {args.slide} is out of range (1..{len(prs.slides)})."
        print(f"FAILED: {msg}")
        _write_json_result(
            args.json_out,
            {
                "check": "structure",
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "pptx": str(pptx_path),
                "slide": args.slide,
                "expected_layout": args.layout,
                "actual_layout": None,
                "passed": False,
                "errors": [msg],
            },
        )
        return 1

    slide = prs.slides[args.slide - 1]
    errors: list[str] = []

    actual_layout = prs.slide_layouts.index(slide.slide_layout)
    if args.layout is not None and actual_layout != args.layout:
        errors.append(f"Layout mismatch: expected {args.layout}, found {actual_layout}.")

    # Title placeholder check (idx 0 expected in BMW template layouts)
    title_text = ""
    try:
        title_text = (slide.placeholders[0].text or "").strip()
    except Exception:
        errors.append("Missing title placeholder idx 0.")
    if not title_text:
        errors.append("Title placeholder idx 0 is empty.")

    if _contains_placeholder_prompt(slide):
        errors.append("Found unresolved placeholder prompt text ('Click to add ...').")

    require_picture = args.require_picture or (
        args.layout is not None and args.layout in PICTURE_LAYOUTS
    )
    if require_picture and not _has_picture(slide):
        errors.append("Picture required but no picture shape found.")

    # Title layouts need department placeholder filled (template-specific)
    if (args.layout in {0, 19}) if args.layout is not None else (actual_layout in {0, 19}):
        try:
            dept_text = (slide.placeholders[22].text or "").strip()
            if not dept_text:
                errors.append("Department placeholder idx 22 is empty on title slide.")
        except Exception:
            errors.append("Department placeholder idx 22 missing on title slide.")

    # Text overflow heuristic — catches overstuffed placeholders/textboxes
    errors.extend(_check_text_overflow(slide))

    result = {
        "check": "structure",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "pptx": str(pptx_path),
        "slide": args.slide,
        "expected_layout": args.layout,
        "actual_layout": actual_layout,
        "require_picture": bool(args.require_picture),
        "passed": len(errors) == 0,
        "errors": errors,
    }

    if errors:
        print(f"FAILED slide {args.slide}:")
        for e in errors:
            print(f"- {e}")
        _write_json_result(args.json_out, result)
        return 1

    print(f"OK slide {args.slide}: layout={actual_layout}, title='{title_text[:60]}'")
    _write_json_result(args.json_out, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
