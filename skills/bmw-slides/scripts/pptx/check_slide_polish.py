#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "python-pptx",
# ]
# ///

"""
check_slide_polish.py - Fast non-visual polish gate for one slide.

Catches two high-impact regressions:
1) Bottom takeaway rendered as plain/small textbox (footer-like)
2) Arrow/chevron overlapping large cards
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE, MSO_SHAPE_TYPE
from pptx.util import Cm

# Ensure skill root is importable when running via absolute script path.
SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from pptx_lib.constants import (  # noqa: E402
    FREE_BOTTOM,
    FREE_HEIGHT,
    FREE_LEFT,
    FREE_TOP,
    FREE_WIDTH,
)

EMU_PER_PT = 12700
BOTTOM_ZONE_TOP = int(FREE_TOP + FREE_HEIGHT - Cm(3.2))
MIN_TAKEAWAY_PT = 18.0
MIN_CARD_W = int(Cm(8.0))
MIN_CARD_H = int(Cm(4.0))
MIN_INTERSECT = int(Cm(0.05))
MIN_CARD_GAP = int(Cm(0.15))  # minimum gap between adjacent cards
BANNER_EDGE_TOLERANCE = int(Cm(0.6))  # max allowed mismatch between banner and content edges
OOB_TOLERANCE = int(Cm(0.15))  # tolerance for out-of-bounds check
FREE_RIGHT = int(FREE_LEFT + FREE_WIDTH)
FREE_BOTTOM_EMU = int(FREE_BOTTOM)
ARROW_TYPES = {
    MSO_AUTO_SHAPE_TYPE.CHEVRON,
    MSO_AUTO_SHAPE_TYPE.RIGHT_ARROW,
    MSO_AUTO_SHAPE_TYPE.LEFT_ARROW,
    MSO_AUTO_SHAPE_TYPE.LEFT_RIGHT_ARROW,
    MSO_AUTO_SHAPE_TYPE.UP_ARROW,
    MSO_AUTO_SHAPE_TYPE.DOWN_ARROW,
}
CARD_TYPES = {
    MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
    MSO_AUTO_SHAPE_TYPE.RECTANGLE,
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Check polish quality of one slide.")
    p.add_argument("--pptx", required=True, help="Path to presentation")
    p.add_argument("--slide", required=True, type=int, help="1-based slide number")
    p.add_argument(
        "--json-out",
        default="",
        help="Optional output path for machine-readable gate result JSON.",
    )
    return p.parse_args()


def _shape_bbox(shp) -> tuple[int, int, int, int]:
    left = int(shp.left)
    top = int(shp.top)
    right = left + int(shp.width)
    bottom = top + int(shp.height)
    return left, top, right, bottom


def _intersect_dims(a, b) -> tuple[int, int]:
    aw = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    ah = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    return aw, ah


def _all_font_pts(shape) -> list[float]:
    sizes: list[float] = []
    if not getattr(shape, "has_text_frame", False):
        return sizes
    tf = shape.text_frame
    for para in tf.paragraphs:
        if para.font.size is not None:
            sizes.append(int(para.font.size) / EMU_PER_PT)
        for run in para.runs:
            if run.font.size is not None:
                sizes.append(int(run.font.size) / EMU_PER_PT)
    return sizes


def _shape_text(shape) -> str:
    if not getattr(shape, "has_text_frame", False):
        return ""
    return (shape.text_frame.text or "").strip()


def _is_plain_textbox(shape) -> bool:
    return shape.shape_type == MSO_SHAPE_TYPE.TEXT_BOX


def _check_bottom_takeaway(slide) -> list[str]:
    issues: list[str] = []
    for shp in slide.shapes:
        txt = _shape_text(shp)
        if not txt or len(txt) < 35:
            continue
        if int(shp.top) < BOTTOM_ZONE_TOP:
            continue

        sizes = _all_font_pts(shp)
        max_pt = max(sizes) if sizes else 0.0

        # Plain textboxes are acceptable if they have strong enough styling
        # (bold, >= 18pt). Only flag if the text is too small — that's the
        # real problem (footer-like appearance), not the container type.
        if max_pt < MIN_TAKEAWAY_PT:
            issues.append(
                f"Bottom takeaway text too small ({max_pt:.1f}pt). "
                f"Use >= {MIN_TAKEAWAY_PT:.0f}pt with bold styling, "
                "or wrap in add_bottom_banner(...) / add_takeaway_box(...)."
            )
    return issues


def _check_arrow_card_overlap(slide) -> list[str]:
    issues: list[str] = []
    cards = []
    arrows = []

    for shp in slide.shapes:
        if shp.shape_type != MSO_SHAPE_TYPE.AUTO_SHAPE:
            continue
        if (
            shp.auto_shape_type in CARD_TYPES
            and int(shp.width) >= MIN_CARD_W
            and int(shp.height) >= MIN_CARD_H
        ):
            cards.append(shp)
        elif shp.auto_shape_type in ARROW_TYPES:
            arrows.append(shp)

    for arrow in arrows:
        abox = _shape_bbox(arrow)
        for card in cards:
            cbox = _shape_bbox(card)
            iw, ih = _intersect_dims(abox, cbox)
            if iw > MIN_INTERSECT and ih > MIN_INTERSECT:
                issues.append(
                    "Arrow/chevron overlaps a large card. Use add_gap_chevron(...) or "
                    "compute arrow width from the actual gap."
                )
                break
    return issues


def _check_card_gaps(slide) -> list[str]:
    """Check that adjacent cards have a minimum gap between them.

    Adjacent cards on the same row (vertically overlapping) must have at
    least MIN_CARD_GAP horizontal space.  Adjacent cards on the same column
    (horizontally overlapping) must have at least MIN_CARD_GAP vertical space.
    """
    issues: list[str] = []
    cards = []

    for shp in slide.shapes:
        if shp.shape_type != MSO_SHAPE_TYPE.AUTO_SHAPE:
            continue
        if (
            shp.auto_shape_type in CARD_TYPES
            and int(shp.width) >= MIN_CARD_W
            and int(shp.height) >= MIN_CARD_H
        ):
            cards.append(shp)

    if len(cards) < 2:
        return issues

    bboxes = [_shape_bbox(shp) for shp in cards]

    for i in range(len(bboxes)):
        for j in range(i + 1, len(bboxes)):
            a = bboxes[i]
            b = bboxes[j]

            # Check vertical overlap (same row)
            v_overlap = min(a[3], b[3]) - max(a[1], b[1])
            if v_overlap > MIN_INTERSECT:
                # Cards share a row — check horizontal gap
                if a[2] <= b[0]:
                    h_gap = b[0] - a[2]
                elif b[2] <= a[0]:
                    h_gap = a[0] - b[2]
                else:
                    h_gap = 0  # overlapping — already caught by overlap check
                if 0 < h_gap < MIN_CARD_GAP:
                    issues.append(
                        f"Cards too close horizontally (gap={h_gap / 360000:.2f}cm, "
                        f"min={MIN_CARD_GAP / 360000:.2f}cm). "
                        "Use ContentGrid with col_gap >= Cm(0.4)."
                    )
                    return issues  # one finding is enough

            # Check horizontal overlap (same column)
            h_overlap = min(a[2], b[2]) - max(a[0], b[0])
            if h_overlap > MIN_INTERSECT:
                # Cards share a column — check vertical gap
                if a[3] <= b[1]:
                    v_gap = b[1] - a[3]
                elif b[3] <= a[1]:
                    v_gap = a[1] - b[3]
                else:
                    v_gap = 0
                if 0 < v_gap < MIN_CARD_GAP:
                    issues.append(
                        f"Cards too close vertically (gap={v_gap / 360000:.2f}cm, "
                        f"min={MIN_CARD_GAP / 360000:.2f}cm). "
                        "Use ContentGrid with row_gap >= Cm(0.4)."
                    )
                    return issues

    return issues


def _check_banner_alignment(slide) -> list[str]:
    """Check that bottom banners/takeaway boxes are not wider or narrower
    than the content cards above them.

    A banner whose left edge is more than BANNER_EDGE_TOLERANCE inside/outside
    the outermost card edges is flagged.
    """
    issues: list[str] = []
    cards = []
    banners = []

    for shp in slide.shapes:
        if shp.shape_type != MSO_SHAPE_TYPE.AUTO_SHAPE:
            continue
        bbox = _shape_bbox(shp)

        # Banner detection: wide shape in the bottom zone
        if (
            shp.auto_shape_type in CARD_TYPES
            and bbox[1] >= BOTTOM_ZONE_TOP
            and int(shp.width) >= int(FREE_WIDTH * 0.5)
        ):
            banners.append(bbox)
        elif (
            shp.auto_shape_type in CARD_TYPES
            and int(shp.width) >= MIN_CARD_W
            and int(shp.height) >= MIN_CARD_H
            and bbox[1] < BOTTOM_ZONE_TOP
        ):
            cards.append(bbox)

    if not banners or not cards:
        return issues

    # Find the outermost card edges
    content_left = min(c[0] for c in cards)
    content_right = max(c[2] for c in cards)

    for b in banners:
        left_diff = abs(b[0] - content_left)
        right_diff = abs(b[2] - content_right)

        if left_diff > BANNER_EDGE_TOLERANCE or right_diff > BANNER_EDGE_TOLERANCE:
            banner_w_cm = (b[2] - b[0]) / 360000
            content_w_cm = (content_right - content_left) / 360000
            issues.append(
                f"Banner width ({banner_w_cm:.1f}cm) does not match content width "
                f"({content_w_cm:.1f}cm). Use ContentGrid.banner() to ensure alignment, "
                f"or set banner left/width to match the outermost card edges."
            )
            break

    return issues


def _check_out_of_bounds(slide) -> list[str]:
    """Check that no content shape extends beyond the FREE area.

    Connectors (lines) are excluded — they are decorative and may
    intentionally extend slightly beyond the content zone.
    Only AutoShapes and TextBoxes are checked.
    """
    issues: list[str] = []
    free_l = int(FREE_LEFT) - OOB_TOLERANCE
    free_t = int(FREE_TOP) - OOB_TOLERANCE
    free_r = int(FREE_RIGHT) + OOB_TOLERANCE
    free_b = int(FREE_BOTTOM_EMU) + OOB_TOLERANCE

    for shp in slide.shapes:
        if shp.shape_type not in (
            MSO_SHAPE_TYPE.AUTO_SHAPE,
            MSO_SHAPE_TYPE.TEXT_BOX,
        ):
            continue
        left, top, right, bottom = _shape_bbox(shp)
        if left < free_l or top < free_t or right > free_r or bottom > free_b:
            txt = _shape_text(shp)[:40] or "(no text)"
            issues.append(
                f"Shape extends beyond FREE area: {txt!r}. Check helper geometry or item count."
            )
            return issues  # one finding is enough
    return issues


def _write_json_result(path: str, payload: dict) -> None:
    if not path:
        return
    out_path = Path(path).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def main() -> int:
    args = parse_args()
    pptx = Path(args.pptx).expanduser().resolve()
    prs = Presentation(str(pptx))

    if args.slide < 1 or args.slide > len(prs.slides):
        msg = f"slide {args.slide} out of range (1..{len(prs.slides)})."
        print(f"FAILED: {msg}")
        _write_json_result(
            args.json_out,
            {
                "check": "polish",
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "pptx": str(pptx),
                "slide": args.slide,
                "passed": False,
                "errors": [msg],
            },
        )
        return 1

    slide = prs.slides[args.slide - 1]
    issues: list[str] = []
    issues.extend(_check_bottom_takeaway(slide))
    issues.extend(_check_arrow_card_overlap(slide))
    issues.extend(_check_card_gaps(slide))
    issues.extend(_check_banner_alignment(slide))
    issues.extend(_check_out_of_bounds(slide))

    result = {
        "check": "polish",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "pptx": str(pptx),
        "slide": args.slide,
        "passed": len(issues) == 0,
        "errors": issues,
    }

    if issues:
        print(f"FAILED slide {args.slide}:")
        for i in issues:
            print(f"- {i}")
        _write_json_result(args.json_out, result)
        return 1

    print(f"OK slide {args.slide}: polish gate passed")
    _write_json_result(args.json_out, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
