# Sub-Agent Context — Read This First

This file contains everything a slide sub-agent needs to generate a single `slide_NN.py` script. Read it once at the start. Do NOT import anything from `build_common.py` — all its variables are already in scope via `exec()`.

## Available Variables (from build_common.py)

**Modules:** `os`, `sys`, `yaml`, `etree`, `qn`, `Image`, `date`, `Presentation`, `Inches`, `Pt`, `Emu`, `Cm`, `PP_ALIGN`, `MSO_ANCHOR`, `MSO_SHAPE`, `RGBColor`

**Constants:** `SKILL_DIR`, `TEMPLATE`, `CONFIG_PATH`, `ASSETS`, `OUTPUT`, `DEPARTMENT`, `FOOTER`, `CONFIDENTIALITY`, `COLOR_PRIMARY`, `COLOR_ACCENT`, `COLOR_ACCENT2`, `COLOR_SECONDARY`, `CARD_BG`, `CARD_BORDER`, `WHITE`, `DARK`, `PALETTE`, `FREE_LEFT`, `FREE_TOP`, `FREE_WIDTH`, `FREE_HEIGHT`, `FREE_BOTTOM`, `FREE2_TOP`, `FREE2_HEIGHT`, `FREE2_BOTTOM`

**Functions:** `free_area(layout_idx)` — returns `(left, top, width, height)` for the free content area. Layout 2 has a larger area (`top=2.07cm, height=15.46cm`) than Layout 12 (`top=3.93cm, height=13.6cm`). Use this instead of hardcoding `FREE_TOP`/`FREE_HEIGHT` when your layout is variable.

**The presentation object:** `prs` — template loaded, example slides deleted, master config applied. Ready for `prs.slides.add_slide(...)`.

## Creative Freedom on the BMW Canvas

The BMW canvas — title, footer, department badge, logo, colors, fonts — is fixed by the template. Do not touch it. **Everything inside the free content area is yours.**

- **Layouts 2 and 12 are blank canvas.** Only the title placeholder is reserved. The rest (31.18 × 13.6 cm / 15.46 cm) is free for any composition you design.
- **`pptx_lib` helpers are tools, not mandates.** Use them when they fit, skip them when a custom shape arrangement serves the content better. You are not obliged to use `add_mece_tiles` just because you have three points.
- **Mix freely.** `pptx_lib` helpers return shape objects — you can reposition them, layer custom shapes on top, or combine with raw `slide.shapes.add_shape(...)` calls.
- **Use the full `MSO_SHAPE` palette** (200+ options: OVAL, STAR, HEART, CLOUD, PENTAGON, FREEFORM, connectors, etc.) when a custom infographic tells the story better than a template composition.
- **Vary across slides.** A deck that alternates hero numbers, bespoke infographics, pull quotes, and clean typography reads as curated. A deck of 10 card-grid slides reads as stamped.

The goal: BMW identity at the edges, creative composition in the body.

## pptx_lib API Reference

The `pptx_lib` package is installed and importable. Use it when a helper fits your design — write raw python-pptx shapes when it doesn't.

### Helpers (`pptx_lib.helpers`)

```
send_to_back(slide, shape)           — move shape behind all others
bring_to_front(slide, shape)         — move shape in front of all others
remove_empty_placeholders(slide)     — delete unfilled placeholders (idx!=0), preserves PicturePlaceholders
suppress_bullet(p)                   — remove inherited template bullet from paragraph
set_ph_margins(tf, left, top, right, bottom)  — set text frame padding (defaults: 0.55/0.4/0.4/0.3 cm)
set_notes(slide, text)               — set speaker notes
fix_dept_placeholder(slide)          — copy layout-level trapezoid geometry onto slide-level ph 22
```

### Text (`pptx_lib.text`)

```
add_textbox(slide, left, top, width, height, text="", font_size=Pt(14), bold=False, color=DARK, alignment=PP_ALIGN.LEFT, word_wrap=True, vertical_anchor=None)
    → (textbox_shape, text_frame)

add_bullet_paragraph(tf, text, font_size=Pt(14), color=DARK, bold=False)
    → paragraph — adds a • bullet paragraph to a text frame

add_accent_underline(slide, left, top, width, color=COLOR_ACCENT, thickness=Pt(3))
    → shape — thin colored bar below a heading
```

### Images (`pptx_lib.images`)

```
fill_placeholder_image(slide, idx, img_path)
    → picture shape — fill a PICTURE placeholder by idx; falls back to add_picture() if
      insert_picture() fails (common after template manipulation). Always use this
      instead of raw slide.placeholders[idx].insert_picture().

add_image_preserved_ratio(slide, img_path, target_left, target_top, target_width, target_height)
    → picture shape — centered within target box, aspect ratio preserved

add_text_shadow_box(slide, left, top, width, height, rgb=BLACK, opacity_pct=55)
    → shape — semi-transparent box for text readability on image slides

add_background_image_with_overlay(slide, img_path, left, top, width, height, overlay_alpha=0.4)
    → overlay shape — image + dark overlay for text on top
```

### Cards (`pptx_lib.cards`)

```
add_card_with_accent(slide, left, top, width, height, accent_color=COLOR_ACCENT)
    → (card, strip) — rounded rect card with colored left accent strip

add_icon_circle(slide, left, top, text, color=COLOR_ACCENT, diameter=Cm(0.85))
    → icon shape — small colored circle with centered text

add_bottom_banner(slide, text, left, top, width, bg_color=COLOR_PRIMARY, text_color=WHITE, font_size=Pt(20), banner_height=Cm(2.1))
    → banner shape — full-width colored banner (default height=2.1cm, min text size=18pt)

add_takeaway_box(slide, text, left, top, width, height=Cm(2.2), border_color=COLOR_PRIMARY, text_color=COLOR_PRIMARY, font_size=Pt(20))
    → box shape — light rounded takeaway box for bottom conclusions (min text size=18pt)
```

### Shapes (`pptx_lib.shapes`)

```
add_chevron_chain(slide, items, left=None, top=None, width=None, available_height=None, chev_height=Cm(5), overlap=Cm(1.5), badge_diameter=Cm(1.2), chev_color=COLOR_PRIMARY, badge_color=COLOR_ACCENT, kicker_text=None, kicker_height=Cm(2))
    items: [(num_str, title, subtitle), ...]
    → list of (chevron, badge) tuples — PENTAGON first, then CHEVRONs

add_arrow_bar_steps(slide, items, bar_left, bar_top, bar_width, arrow_height, colors=None)
    items: [(number, label, description), ...]

add_divider_line(slide, left, top, width, color=grey)
    → connector shape

add_gap_chevron(slide, left_box_left, left_box_width, right_box_left, center_y, height=Cm(2.0), color=COLOR_ACCENT, side_margin=Cm(0.2), max_width=Cm(2.2))
    → chevron shape centered in the gap between two cards, guaranteed no overlap
```

### Tables (`pptx_lib.tables`)

```
add_styled_table(slide, headers, rows, left, top, width, height, header_color=COLOR_PRIMARY, col_widths=None)
    headers: [str, ...], rows: [[str, ...], ...], col_widths: [float fractions summing to 1.0]

add_comparison_table(slide, criteria, options, left, top, width, height, option_colors=None)
    criteria: [str, ...], options: [(name, [cell_values]), ...]
```

### Layout Patterns (`pptx_lib.layout`)

```
add_pillars(slide, pillars, left, top, total_width, total_height, colors=None)
    pillars: [(title, [bullet1, ...]), ...]

add_mece_tiles(slide, items, left, top, width, height, colors=None, show_numbers=True)
    items: [(title, body_text), ...] — 2 to 5 tiles

add_pyramid_slide_content(slide, headline, supports, left, top, width, height, accent_color=COLOR_ACCENT)
    supports: [(title, body), ...] — answer-first layout

add_sidebar_layout(slide, sidebar_items, main_title, main_text, left, top, width, height, sidebar_color=COLOR_PRIMARY)

add_tabbed_headers(slide, tabs, active_idx, left, top, width, active_color, inactive_color)
    → (content_left, content_top, content_width)

add_zigzag_blocks(slide, items, left, top, width, height, block_color, accent_color)
    items: [(title, text), ...] — alternating left-right blocks

add_numbered_badge_list(slide, items, left, top, width, height, badge_color)
    items: [(title, description), ...] — vertical numbered list

add_key_value_pairs(slide, pairs, left, top, width, height, accent_color)
    pairs: [(key, value), ...] — horizontal key-value rows
```

### Infographics (`pptx_lib.infographics`)

```
add_hero_number(slide, number, subtitle="", left, top, width, height, number_size=Pt(48), subtitle_size=Pt(24), number_color, subtitle_color)
    — large centered number with context below

add_timeline(slide, milestones, left, top, width, line_color, dot_color)
    milestones: [(label, date_str), ...] — alternating above/below

add_swimlane_timeline(slide, swimlanes, left, top, width, row_height, line_color)
    swimlanes: [(lane_name, [(label, x_fraction), ...]), ...]

add_rag_dashboard(slide, items, left, top, width, row_height, dot_diameter)
    items: [(topic, "R"/"A"/"G", owner, note), ...]
add_rag_header(slide, left, top, width, row_height)

add_pull_quote(slide, quote, attribution, left, top, width, height, accent_color, text_color)

add_progress_ring(slide, pct, label, value_text, cx, cy, diameter, ring_color, bg_color)
    pct: 0-100, cx/cy: center EMU position

add_hexagon_grid(slide, items, left, top, width, hex_size, colors)
    items: [str, ...] — honeycomb tile labels

add_venn(slide, circles, left, top, width, height)
    circles: [(label, color), ...] — 2-3 overlapping circles

add_funnel(slide, stages, left, top, width, height, colors)
    stages: [(label, value_text), ...] — narrowing trapezoids

add_callout(slide, text, box_left, box_top, box_w, box_h, target_x, target_y, color)
    — leader-line annotation pointing at a target coordinate
```

### Credits (`pptx_lib.credits`)

```
add_credits_slide(prs, credits)
    credits: [(slide_num, description, author, source, license), ...]
```

---

## Layout Reference

Slide size: 33.87 × 19.05 cm (12192000 × 6858000 EMU), Widescreen 16:9.

### Layout 0: Title | Full Area

| idx | Type                    | Position (cm) | Size (cm)     |
| --- | ----------------------- | ------------- | ------------- |
| 21  | PICTURE                 | 0, 0          | 33.87 × 18.26 |
| 0   | CENTER_TITLE            | 0, 10.5       | 33.87 × 3.82  |
| 1   | SUBTITLE                | 0, 14.6       | 33.87 × 1.26  |
| 22  | BODY (Dept., trapezoid) | 26.49, 16.35  | 7.37 × 1.16   |

### Layout 1: Divider | Half Area Right

| idx | Type         | Position (cm) | Size (cm)     |
| --- | ------------ | ------------- | ------------- |
| 11  | BODY         | 1.33, 3.95    | 17.69 × 3.18  |
| 12  | PICTURE      | 20.4, 0       | 13.47 × 18.25 |
| 0   | CENTER_TITLE | 1.33, 7.13    | 17.71 × 5.13  |

### Layout 2: Grid | 1 (title only, full free area)

| idx | Type  | Position (cm) | Size (cm)    |
| --- | ----- | ------------- | ------------ |
| 0   | TITLE | 1.36, 0.96    | 31.18 × 1.11 |

### Layout 7: Content | 1

| idx | Type   | Position (cm) | Size (cm)    |
| --- | ------ | ------------- | ------------ |
| 0   | TITLE  | 1.36, 0.96    | 31.18 × 1.11 |
| 17  | OBJECT | 1.36, 3.93    | 31.18 × 13.6 |

### Layout 8: Content | 2

| idx | Type   | Position (cm) | Size (cm)    |
| --- | ------ | ------------- | ------------ |
| 0   | TITLE  | 1.36, 0.96    | 31.18 × 1.11 |
| 17  | OBJECT | 1.36, 3.93    | 14.99 × 13.6 |
| 19  | OBJECT | 17.55, 3.93   | 14.99 × 13.6 |

### Layout 9: Content | 3

| idx | Type   | Position (cm) | Size (cm)    |
| --- | ------ | ------------- | ------------ |
| 0   | TITLE  | 1.36, 0.96    | 31.18 × 1.11 |
| 17  | OBJECT | 1.36, 3.93    | 9.99 × 13.6  |
| 19  | OBJECT | 11.95, 3.93   | 9.99 × 13.6  |
| 21  | OBJECT | 22.54, 3.93   | 9.99 × 13.6  |

### Layout 10: Content | 4

| idx | Type   | Position (cm) | Size (cm)    |
| --- | ------ | ------------- | ------------ |
| 0   | TITLE  | 1.36, 0.96    | 31.18 × 1.11 |
| 17  | OBJECT | 1.36, 3.93    | 7.34 × 13.6  |
| 19  | OBJECT | 9.3, 3.93     | 7.34 × 13.6  |
| 21  | OBJECT | 17.25, 3.93   | 7.34 × 13.6  |
| 23  | OBJECT | 25.19, 3.93   | 7.34 × 13.6  |

### Layout 11: Content | 2×2

| idx | Type   | Position (cm) | Size (cm)    |
| --- | ------ | ------------- | ------------ |
| 0   | TITLE  | 1.36, 0.96    | 31.18 × 1.11 |
| 10  | OBJECT | 1.36, 3.93    | 14.99 × 6.5  |
| 11  | OBJECT | 17.55, 3.93   | 14.99 × 6.5  |
| 12  | OBJECT | 1.36, 11.02   | 14.99 × 6.5  |
| 13  | OBJECT | 17.55, 11.02  | 14.99 × 6.5  |

### Layout 12: Content | Area (title only, free area below)

| idx | Type  | Position (cm) | Size (cm)    |
| --- | ----- | ------------- | ------------ |
| 0   | TITLE | 1.36, 0.96    | 31.18 × 1.11 |

Free area: left 1.36, top 3.93, width 31.18, height 13.6 cm

### Layout 13: Content | Picture Left

| idx | Type    | Position (cm) | Size (cm)    |
| --- | ------- | ------------- | ------------ |
| 0   | TITLE   | 1.36, 0.96    | 31.18 × 1.11 |
| 12  | PICTURE | 0, 3.93       | 16.35 × 13.6 |
| 10  | OBJECT  | 17.54, 3.93   | 14.99 × 13.6 |

### Layout 14: Content | Picture Right

| idx | Type    | Position (cm) | Size (cm)    |
| --- | ------- | ------------- | ------------ |
| 0   | TITLE   | 1.36, 0.96    | 31.18 × 1.11 |
| 10  | OBJECT  | 1.36, 3.93    | 14.99 × 13.6 |
| 12  | PICTURE | 17.52, 3.93   | 16.35 × 13.6 |

### Layout 18: Key Note

| idx | Type    | Position (cm) | Size (cm)     |
| --- | ------- | ------------- | ------------- |
| 10  | PICTURE | 0, 0          | 33.87 × 18.25 |
| 0   | TITLE   | 0, 3.92       | 33.9 × 4.03   |

### Layout 19: Title | Full Picture

| idx | Type                    | Position (cm) | Size (cm)     |
| --- | ----------------------- | ------------- | ------------- |
| 21  | PICTURE                 | 0, 0          | 33.87 × 18.26 |
| 0   | CENTER_TITLE            | 0, 10.56      | 33.87 × 3.92  |
| 1   | SUBTITLE                | 0, 14.75      | 33.87 × 1.26  |
| 22  | BODY (Dept., trapezoid) | 26.49, 16.35  | 7.37 × 1.16   |

---

## Code Generation Rules

1. **Always use template:** `Presentation(TEMPLATE)`, never `Presentation()` — handled by `build_common.py`.
2. **Delete existing slides:** handled by `build_common.py`.
3. **Load config:** handled by `build_common.py`.
4. **Title-Slide Dept.:** On layout 0/19, always set `slide.placeholders[22].text = DEPARTMENT` and then call `fix_dept_placeholder(slide)` to preserve the trapezoid badge shape from the template.
5. **Fill placeholders by idx** from the layout reference above.
6. **Preserve image aspect ratio:** Use `add_image_preserved_ratio()` or calculate before placing.
7. **Absolute paths** for template, images, and output.
8. **One file per slide:** Each `slide_NN.py` adds exactly one slide. No imports from build_common, no `prs.save()`, no redefined helpers.
9. **Font size minimums:** Body text ≥ `Pt(16)`, section headers ≥ `Pt(18)` for standalone textboxes you create. Library helpers follow the same defaults — do not override them downward.
10. **Inner padding for textboxes:** Offset from card edge by ≥ `Cm(0.4)` on all sides. Never start at exact card coordinates.
    10a. **Vertically center card groups by default** when content is shorter than `FREE_HEIGHT`. Calculate `card_top = FREE_TOP + (FREE_HEIGHT - card_h) / 2`. Top-aligned placement is acceptable when the bottom is intentionally left as breathing room or when the composition works better asymmetrically. When repositioning placeholders, always set all four geometry values (`ph.left`, `ph.top`, `ph.width`, `ph.height`).
11. **Remove empty placeholders.** Call `remove_empty_placeholders(slide)` after building content. Call `fill_placeholder_image()` before this so images are preserved. **Never** use raw `insert_picture()` — it silently fails when placeholders lose their type after template manipulation.
12. **Never overlap cards with bottom labels.** Reserve space: `card_h = FREE_HEIGHT - Cm(2.0)` when a bottom row is present.
13. **Bottom takeaway (kicker) — authoritative rule.** This is the single source of truth for kicker styling; other files reference this rule. **Kickers are optional and should be used sparingly** — only render a kicker when the storyline explicitly provides `**Kicker:**` text. Do not invent or add kickers that are not in the storyline. When a kicker is present: prefer `add_bottom_banner(...)` for high-emphasis conclusions, or `add_takeaway_box(...)` for lighter emphasis. Target `Pt(20)` (hard floor `Pt(18)`), centered, with clear vertical breathing room above. A bold styled textbox (≥ `Pt(18)`, primary color) is acceptable when the composition works better without a container.
14. **Keep all shapes within `FREE_BOTTOM`.** Never place shapes below `FREE_TOP + FREE_HEIGHT = 17.53 cm`.
15. **Card accent strips outside the card.** Place at `left - Cm(0.15)`, inset top/bottom by `Cm(0.25)`. Do NOT `send_to_back` the strip.
16. **Connector shapes fit inside the gap.** Calculate visual gap accounting for accent strips. Arrow width ≤ `Cm(1.2)`. Call `bring_to_front` on arrows.
17. **Bottom banners match combined card width** when cards are present: `banner_left = left_card_left`, `banner_w = right_card_right - left_card_left`. Full `FREE_WIDTH` banners are acceptable on slides without cards (e.g., hero number + banner, single visual + takeaway).
18. **Never put a header inside a bullet placeholder.** Use a standalone `add_textbox()` for column headers. Set placeholder `margin_top` to push bullets below.
19. **CHEVRON/PENTAGON text padding:** Use asymmetric padding: PENTAGON `left=0.5/right=1.2`, CHEVRON middle `1.3/1.2`, CHEVRON last `1.3/0.4`.
20. **Gap connectors must not overlap cards.** For a center chevron/arrow between two large cards, use `add_gap_chevron(...)` (preferred) or compute width from the actual gap with at least `Cm(0.2)` margin per side.
21. **Bottom zone awareness:** In the lower `Cm(3.2)` of the free area, prefer `add_bottom_banner(...)` or `add_takeaway_box(...)` for conclusion text. A styled textbox (bold, ≥ `Pt(18)`, primary color) is acceptable if the content is not a takeaway or if the composition works better without a container.
22. **Use `ContentGrid` for multi-element layouts.** When placing 2+ cards, tiles, or content blocks in a grid arrangement, use `ContentGrid` instead of manual position math. It guarantees aligned cells, consistent gaps, and optional banner reservation. Prefer it whenever a slide has a regular grid structure.
23. **`ContentGrid` parameters.** `ContentGrid(left, top, width, height, cols, rows, col_gap=Cm(0.5), row_gap=Cm(0.5), banner_height=None, banner_gap=Cm(0.3), padding=Cm(0))`. Use `free_area(layout_idx)` to get the correct `left, top, width, height` for your layout. Key methods: `grid.cell(col, row)` → single cell, `grid.region(col, row, colspan, rowspan)` → merged area, `grid.banner()` → bottom banner, `grid.col_gap_center(col_left, row)` → center point for gap connectors.
24. **Content density limits.** Max 6 bullets, 6 cards/tiles, or 2 short paragraphs per slide. If content exceeds this, tell the orchestrator to split the slide. Title text max 2 lines. Code/data max 8–10 lines.
25. **`ContentGrid` patterns.** Three cards + banner: `ContentGrid(*free_area(12), cols=3, banner_height=Cm(2.1))`. Two-column asymmetric: use `region(col=0, row=0, colspan=2)` for the wide side. Gap chevrons: `cx, cy, gw = grid.col_gap_center(0)` then `add_gap_chevron(...)`. Always get banner geometry from `grid.banner()` so it aligns with the cells above.

## Script Structure

```python
# slide_NN.py — Slide N: [title]
# No imports from build_common — all variables in scope via exec()
from pptx_lib import ...  # import only what you need

slide = prs.slides.add_slide(prs.slide_layouts[LAYOUT_IDX])
slide.placeholders[0].text = "Title Here"

# ... build content using pptx_lib helpers ...

remove_empty_placeholders(slide)
set_notes(slide, "Speaker notes here.")
```
