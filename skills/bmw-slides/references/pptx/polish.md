# Delivery Polish Reference

## Polish Checklist

For each slide (skip title/divider slides with layouts 0, 1, 18, 19), check:

> The patterns and values below are **starting points, not mandates**. The right treatment depends on the slide's visual character (data-forward, structure-forward, flow-forward, narrative-forward, comparison-forward). Vary the polish approach across slides — visual variety is a feature, not a bug.

1. **Dead space:** Is **more than 60%** of the free area visually empty? If yes, consider redistributing content, increasing font size, vertically centering, or adding supporting shapes. Intentional white space around a centered visual element is acceptable — do not fill space just to fill it.
2. **Plain bullet lists:** Can bullet lists benefit from visual structure? Options: card backgrounds with accent strips, accent underlines with bold headlines, numbered badges, key-value pair formatting, or strong typographic hierarchy alone (large bold headlines, lighter body text). **Not every slide needs card backgrounds.** Pick the approach that fits the slide's visual character and differs from neighboring slides.
3. **Multi-column slides:** Do columns lack visual separation? Options: card backgrounds, divider lines, generous white space (>1cm gap), or contrasting background tints per column.
4. **Missing visual anchors:** No shapes and no strong typographic hierarchy? Consider adding a shape (card, line, circle) if the slide looks unstructured. A well-typeset text-only slide with clear hierarchy is acceptable.
5. **Attribution:** Append image attribution to each slide's speaker notes. If 3+ images require attribution, add a final "Image Credits" slide using `add_credits_slide`.
6. **Bottom takeaway emphasis:** See Rule 13 in `./references/pptx/sub-agent-context.md` (the authoritative kicker rule). Summary: `add_bottom_banner(...)` or `add_takeaway_box(...)` preferred; bold styled textbox ≥ `Pt(18)` acceptable; never footer-like.
7. **No connector overlap:** Transition arrows/chevrons between cards must sit fully in the gap. If uncertain, use `add_gap_chevron(...)`.

## Enhancement Patterns

Apply these patterns to the **content area only** (below the title placeholder). See `./references/pptx/sub-agent-context.md` for the pptx_lib API reference.

**Important: vary the treatment across slides.** Do not apply cards + accent strips to every slide. Choose the pattern that fits the slide's visual character and creates contrast with neighboring slides.

### Pattern A: Card Backgrounds + Accent Strips (best for: structure-forward slides)

Wrap each content column or section in a rounded rectangle (light grey fill `CARD_BG` / `#FAFAFA`, optional thin border). Add a narrow vertical accent strip (3–4mm wide, primary color) on the left edge. Best for slides with parallel content blocks (pillars, tiles, multi-column). **Skip this pattern on infographic slides** (hero numbers, timelines, progress rings) — these are self-structuring.

### Pattern B: Typographic Hierarchy (best for: narrative-forward slides)

No background shapes. Instead, use strong font size contrast: large bold headlines (Pt(22-28)), lighter body text (Pt(16-18)), accent underlines below key headings. Creates a clean, editorial look. Best for pull-quotes, key-value pairs, sidebar layouts.

### Pattern C: Subtle Dividers (best for: comparison-forward slides)

Thin horizontal or vertical lines (`add_divider_line`) between sections. No card backgrounds. Clean separation without visual weight. Best for comparisons, before/after layouts, multi-column content.

### Pattern D: Color-Tinted Zones (best for: data-forward slides)

Instead of card outlines, use subtle background tinting on key areas (e.g. a light primary-tint rectangle behind the hero number). Keep most of the slide white. Best for hero numbers, RAG dashboards, progress rings.

### Pattern E: Icon Circles + Connectors (best for: flow-forward slides)

Small filled circles with numbers/letters as anchor points, connected by thin lines or arrows. No card backgrounds needed — the flow itself provides structure. Best for timelines, chevron chains, numbered badge lists.

### Legacy patterns (still available)

**Step Indicators (Process Flows):**
For sequential content (steps, phases, timeline), use numbered shapes connected by a horizontal line or arrow chain.

**Pillar Diagrams:**
For 3-4 equal concepts, use tall rounded rectangles side by side with colored header + light body.

**Comparison Layouts:**
For two opposing concepts, use two large cards side by side with color-coded accent strips or a vertical divider.

## Polish Rules

1. **Content area only.** Never modify title placeholder (idx 0) — no font, size, position, or color changes.
2. **Send shapes to back.** New background shapes must be behind existing text. Use `spTree.insert(2, sp)` to push shapes behind content.
3. **Preserve text.** Never delete or rewrite existing text content. Only add visual shapes around/behind it.
4. **Inner padding — mandatory.** When wrapping a textbox or placeholder inside a card, the textbox must be inset from the card edge by at least `Cm(0.4)` on all sides (left, top, right). Never let text start flush against a card boundary. If the card has an accent strip (~`Cm(0.15)` wide), the textbox left must be at least `Cm(0.55)` from the card left edge.
5. **Font size minimums.** After repositioning: body text ≥ `Pt(16)`, section headers/sub-headings ≥ `Pt(18)` for standalone textboxes. Never change the title placeholder font.
6. **Brand consistency, not visual uniformity.** Use the same colors (palette from `pptx_lib.constants`), same fonts, and same brand elements across all slides. But vary the enhancement pattern (A–E) per slide — the deck should feel curated, not stamped from a single mold.
7. **Don't over-decorate.** Prefer 2–3 shape types per slide (e.g., card + accent strip + icon). Complex infographics may use more — but every shape should serve a distinct purpose.
8. **Arrows and connectors always in front.** Transition arrows, chevrons, and connector lines must never be obscured by card backgrounds or accent strips. After adding any card, accent strip, or background shape, call `bring_to_front(slide, arrow_shape)` on every arrow/connector on that slide.
9. **Bottom takeaway style floor.** Bottom conclusion text **should** target `Pt(20)` in a banner/box. A bold styled textbox ≥ `Pt(18)` is acceptable when the composition works better without a container. If a conclusion looks like footer text, fix it before handoff.

## Polish Script Template

The polish script imports `pptx_lib` for all colors, constants, and helpers — just like `build_common.py`. Never redefine colors or paste helper functions manually.

Slide filtering requirement: support optional slide filtering (e.g. `--only 3,7`) so polish can run per-slide in inner loops. Run without `--only` for the final collection pass.

```python
import argparse
import os
import sys
from pptx import Presentation
from pptx.util import Pt, Emu, Cm
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# Import pptx_lib — same approach as build_common.py
for _candidate in ["~/.copilot/skills/bmw-slides", "~/.claude/skills/bmw-slides"]:
    _expanded = os.path.expanduser(_candidate)
    if os.path.isdir(_expanded):
        sys.path.insert(0, _expanded)
        break
from pptx_lib import *

INPUT = "/absolute/path/to/build-output.pptx"
OUTPUT = "/absolute/path/to/final-output.pptx"

def parse_only_arg():
    p = argparse.ArgumentParser()
    p.add_argument("--only", default="", help="Comma-separated 1-based slide numbers, e.g. 3,7")
    args = p.parse_args()
    if not args.only:
        return None
    nums = set()
    for part in args.only.split(","):
        part = part.strip()
        if part:
            nums.add(int(part))
    return nums

ONLY_SLIDES = parse_only_arg()

prs = Presentation(INPUT)

SKIP_LAYOUTS = {0, 1, 18, 19}  # Title/divider layouts

for idx, slide in enumerate(prs.slides, start=1):
    if ONLY_SLIDES is not None and idx not in ONLY_SLIDES:
        continue
    layout_idx = prs.slide_layouts.index(slide.slide_layout)
    if layout_idx in SKIP_LAYOUTS:
        continue
    # ... per-slide polish logic ...

prs.save(OUTPUT)
```

## Self-Review after Polish

The build step already verified structural correctness. The polish-step review focuses only on polish quality.

```bash
bash ./scripts/pptx/self-review.sh /path/to/final.pptx --scan
```

Run a fast non-visual polish gate per changed slide before visual review:

```bash
uv run python ./scripts/pptx/check_slide_polish.py --pptx /path/to/final.pptx --slide N
```

Read `review/contact.jpg` for a quick scan of all slides (all review images are `.jpg` — never `.png`). For content slides (skip layouts 0, 1, 18, 19), check **polish-specific concerns only**:

- Card backgrounds and accent strips present and correctly positioned
- No shapes overlapping title placeholder
- **Text not touching card edges** — confirm ≥ 0.4 cm gap between text and surrounding card borders on all sides (top, left, right)
- **Font size readable** — body text looks clearly legible; anything that looks like fine print must be fixed (≥ Pt(16) for body, ≥ Pt(18) for headers)
- **Bottom takeaway prominence** — any bottom conclusion line is in a banner/box and visually strong (target Pt(20), never footer-like)
- Visual balance — no slide is just plain white with tiny text in the corner
- Brand colors used correctly (palette from `pptx_lib.constants`) — no off-brand colors
- Visual variety — adjacent slides use different enhancement patterns, not all cards+strips

If contact sheet looks clean, proceed. If a slide looks off, read that individual `slide-NN.jpg`. After fixing, use `--only N` to selectively re-review.

Fix issues and re-run before presenting to the user.
