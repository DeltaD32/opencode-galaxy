"""
pptx_lib.constants — Template color palette and free-area geometry.

These values are extracted from the BMW template.pptx and must match exactly.
"""

from __future__ import annotations

from pptx.dml.color import RGBColor
from pptx.util import Cm, Pt

# ── Colors ─────────────────────────────────────────────────────────────────────
COLOR_PRIMARY = RGBColor(0x03, 0x59, 0x70)  # #035970 dk2 — dark teal
COLOR_ACCENT = RGBColor(0xFB, 0xAE, 0x40)  # #FBAE40 — amber
COLOR_ACCENT2 = RGBColor(0x54, 0x8D, 0x9E)  # #548D9E accent1 — muted teal
COLOR_SECONDARY = RGBColor(0xF2, 0x6B, 0x43)  # #F26B43 — orange
CARD_BG = RGBColor(0xFA, 0xFA, 0xFA)  # #FAFAFA card background
CARD_BORDER = RGBColor(0xDD, 0xDD, 0xDD)  # #DDDDDD card border
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
DARK = RGBColor(0x22, 0x22, 0x22)

# Convenience palette for cycling through colors.
# Ordered for maximum contrast at small N (avoids two teals adjacent).
PALETTE = [COLOR_PRIMARY, COLOR_ACCENT, COLOR_SECONDARY, COLOR_ACCENT2]

# ── Free area geometry ─────────────────────────────────────────────────────────
# Layout 12 (Content | Area) — content placeholder zone below the title bar.
FREE_LEFT = Cm(1.36)
FREE_TOP = Cm(3.93)
FREE_WIDTH = Cm(31.18)
FREE_HEIGHT = Cm(13.6)
FREE_BOTTOM = FREE_TOP + FREE_HEIGHT  # never place shapes below this

# Layout 2 (Grid | 1) — larger free area because the title sits higher.
FREE2_TOP = Cm(2.07)
FREE2_HEIGHT = Cm(15.46)
FREE2_BOTTOM = FREE2_TOP + FREE2_HEIGHT


def body_font_size(height_per_item_cm: float) -> "Pt":
    """Return a body font size scaled to the available height per item.

    Uses fixed tiers so similar slides share the same font size rather than
    each getting a slightly different value.  All layout helpers call this
    instead of hardcoding a size.

    Tiers (height per item in cm → Pt):
      ≥ 4.0 cm  → Pt(20)   spacious single-item or 2-item layout
      ≥ 3.0 cm  → Pt(18)
      ≥ 2.2 cm  → Pt(16)   typical 3–4 item layout
      ≥ 1.6 cm  → Pt(14)
      ≥ 1.1 cm  → Pt(12)   dense 6–8 item layout
      < 1.1 cm  → Pt(10)   absolute minimum (≥ 6 items in tight space)
    """
    if height_per_item_cm >= 4.0:
        return Pt(20)
    if height_per_item_cm >= 3.0:
        return Pt(18)
    if height_per_item_cm >= 2.2:
        return Pt(16)
    if height_per_item_cm >= 1.6:
        return Pt(14)
    if height_per_item_cm >= 1.1:
        return Pt(12)
    return Pt(10)


def free_area(layout_idx: int = 12) -> tuple:
    """Return (left, top, width, height) for the free content area of a layout.

    Layout 2 has a larger free area than Layout 12 because its title
    placeholder sits higher.  All other free-area layouts use the Layout 12
    dimensions.

    Usage::

        left, top, width, height = free_area(layout_idx)
        grid = ContentGrid(left, top, width, height, cols=3)
    """
    if layout_idx == 2:
        return FREE_LEFT, FREE2_TOP, FREE_WIDTH, FREE2_HEIGHT
    return FREE_LEFT, FREE_TOP, FREE_WIDTH, FREE_HEIGHT
