# python-pptx Building Blocks — API Reference

All building-block patterns are available as importable functions in **`pptx_lib`**.
`build_common.py` adds the skill directory to `sys.path` and does `from pptx_lib import *`,
so all functions below are already in scope in every `slide_NN.py`.

> **Do not copy raw python-pptx boilerplate.** Call these functions instead.

---

## Constants (from `pptx_lib.constants`)

```python
COLOR_PRIMARY   # RGBColor(0x03,0x59,0x70)  — dark teal
COLOR_ACCENT    # RGBColor(0xFB,0xAE,0x40)  — amber
COLOR_ACCENT2   # RGBColor(0x54,0x8D,0x9E)  — muted teal
COLOR_SECONDARY # RGBColor(0xF2,0x6B,0x43)  — orange
CARD_BG         # RGBColor(0xFA,0xFA,0xFA)
CARD_BORDER     # RGBColor(0xDD,0xDD,0xDD)
WHITE           # RGBColor(0xFF,0xFF,0xFF)
DARK            # RGBColor(0x33,0x33,0x33)
PALETTE         # [COLOR_PRIMARY, COLOR_ACCENT, COLOR_ACCENT2, COLOR_SECONDARY]

# Free content area geometry (Emu)
FREE_LEFT, FREE_TOP, FREE_WIDTH, FREE_HEIGHT, FREE_BOTTOM
```

---

## Quick Reference — All Functions

### Helpers (`pptx_lib.helpers`)

| Function                                       | Purpose                                                      |
| ---------------------------------------------- | ------------------------------------------------------------ |
| `send_to_back(slide, shape)`                   | Move shape to back of z-order                                |
| `bring_to_front(slide, shape)`                 | Move shape to front of z-order                               |
| `remove_empty_placeholders(slide)`             | Delete unfilled placeholders (preserves PicturePlaceholders) |
| `suppress_bullet(paragraph)`                   | Remove bullet from a paragraph via XML                       |
| `set_ph_margins(ph, top, left, bottom, right)` | Set placeholder body margins (all Emu)                       |
| `set_notes(slide, text)`                       | Set speaker notes                                            |

### Text (`pptx_lib.text`)

| Function                                                                                        | Returns       | Purpose                                |
| ----------------------------------------------------------------------------------------------- | ------------- | -------------------------------------- |
| `add_textbox(slide, left, top, width, height, text, font_size, bold, color, alignment, anchor)` | `(shape, tf)` | Add a textbox with optional formatting |
| `add_bullet_paragraph(tf, text, font_size, color, bold, space_before, level)`                   | `paragraph`   | Append a Unicode-bullet paragraph      |
| `add_accent_underline(slide, left, top, width, color, thickness)`                               | `shape`       | Colored horizontal line                |

### Images (`pptx_lib.images`)

| Function                                                                                           | Purpose                                                  |
| -------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| `add_image_preserved_ratio(slide, img_path, target_left, target_top, target_width, target_height)` | Place image preserving aspect ratio within bounding box  |
| `add_text_shadow_box(slide, left, top, width, height, text, font_size, bold, color, bg_alpha)`     | Semi-transparent text overlay (inserted at z-position 3) |
| `add_background_image_with_overlay(slide, img_path, overlay_alpha)`                                | Full-slide background image with dark overlay            |

### Cards (`pptx_lib.cards`)

| Function                                                                                           | Returns         | Purpose                                            |
| -------------------------------------------------------------------------------------------------- | --------------- | -------------------------------------------------- |
| `add_card_with_accent(slide, left, top, width, height, accent_color)`                              | `(card, strip)` | Rounded card with colored left accent strip        |
| `add_icon_circle(slide, left, top, text, color, diameter)`                                         | `shape`         | Colored circle with centered text/emoji            |
| `add_bottom_banner(slide, text, left, top, width, bg_color, text_color, font_size, banner_height)` | `shape`         | Full-width colored takeaway banner (min 18pt text) |
| `add_takeaway_box(slide, text, left, top, width, height, border_color, text_color, font_size)`     | `shape`         | Light boxed takeaway for bottom conclusions        |

### Shapes (`pptx_lib.shapes`)

| Function                                                                                                                 | Returns       | Purpose                                                |
| ------------------------------------------------------------------------------------------------------------------------ | ------------- | ------------------------------------------------------ |
| `add_chevron_chain(slide, items, left, top, width, height, colors, font_size, badge_offset, kicker_text)`                | `list[shape]` | Horizontal chevron/pentagon chain with optional kicker |
| `add_arrow_bar_steps(slide, items, left, top, width, bar_height, circle_d, colors)`                                      | `None`        | Numbered circles on horizontal bar                     |
| `add_divider_line(slide, left, top, width, color, thickness)`                                                            | `shape`       | Horizontal line                                        |
| `add_gap_chevron(slide, left_box_left, left_box_width, right_box_left, center_y, height, color, side_margin, max_width)` | `shape`       | Center chevron in gap between cards (no overlap)       |

### Tables (`pptx_lib.tables`)

| Function                                                                                                | Returns | Purpose                                 |
| ------------------------------------------------------------------------------------------------------- | ------- | --------------------------------------- |
| `add_styled_table(slide, left, top, width, row_height, headers, rows, header_color, alt_color)`         | `table` | Formatted table with colored header row |
| `add_comparison_table(slide, left, top, width, row_height, criteria, options, header_color, alt_color)` | `table` | Criteria-vs-options comparison table    |

### Layout Composites (`pptx_lib.layout`)

| Function                                                                                             | Purpose                                  |
| ---------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| `add_pillars(slide, items, left, top, width, height, colors)`                                        | N vertical pillar columns                |
| `add_mece_tiles(slide, items, left, top, width, height, colors)`                                     | Evenly-spaced tile cards                 |
| `add_pyramid_slide_content(slide, answer, details, left, top, width, height)`                        | Answer-first pyramid                     |
| `add_sidebar_layout(slide, sidebar_items, left, top, width, height, sidebar_ratio)`                  | Left sidebar + main area                 |
| `add_tabbed_headers(slide, tabs, left, top, width, tab_height, active, colors)` → `(cx, cy, cw, ch)` | Tab strip; returns content area position |
| `add_zigzag_blocks(slide, items, left, top, width, height)`                                          | Alternating left-right blocks            |
| `add_numbered_badge_list(slide, items, left, top, width, item_height, colors)`                       | Vertical numbered steps                  |
| `add_key_value_pairs(slide, pairs, left, top, width, item_height) `                                  | Big-value + label pairs                  |

### Infographics (`pptx_lib.infographics`)

| Function                                                                                      | Purpose                                     |
| --------------------------------------------------------------------------------------------- | ------------------------------------------- |
| `add_hero_number(slide, number, label, left, top, width, height)`                             | Large centered number                       |
| `add_timeline(slide, items, left, top, width, height, colors)`                                | Horizontal timeline with circles and labels |
| `add_swimlane_timeline(slide, lanes, left, top, width, height, colors)`                       | Multi-row swimlane                          |
| `add_rag_dashboard(slide, items, left, top, width, height)`                                   | RAG status grid                             |
| `add_rag_header(slide, counts, left, top, width, height)`                                     | Summary bar (R/A/G counts)                  |
| `add_pull_quote(slide, quote, attribution, left, top, width, height)`                         | Styled quotation                            |
| `add_progress_ring(slide, pct, label, cx, cy, diameter, color)`                               | Arc-based progress ring                     |
| `add_hexagon_grid(slide, items, left, top, hex_w, hex_h, cols, colors)`                       | Hexagon tile grid                           |
| `add_venn(slide, labels, left, top, diameter, colors)`                                        | 2-3 circle Venn diagram                     |
| `add_funnel(slide, items, left, top, width, height, colors)`                                  | Narrowing funnel stages                     |
| `add_callout(slide, text, target_left, target_top, callout_left, callout_top, width, height)` | Callout annotation box                      |

### Credits (`pptx_lib.credits`)

| Function                               | Purpose                                                    |
| -------------------------------------- | ---------------------------------------------------------- |
| `add_credits_slide(prs, attributions)` | Adds a credits slide (layout 7) listing image attributions |

---

## Inline python-pptx Patterns

For custom compositions not covered by `pptx_lib`, use python-pptx directly. The `MSO_SHAPE` enum has 200+ shapes — lean on them for bespoke infographics.

```python
# Textbox
txBox = slide.shapes.add_textbox(left, top, width, height)
tf = txBox.text_frame; tf.word_wrap = True
p = tf.paragraphs[0]; p.text = "Hello"; p.font.size = Pt(18)

# Image into picture placeholder (robust, handles type loss)
fill_placeholder_image(slide, idx, os.path.join(ASSETS, "photo.jpg"))

# Rounded rectangle
from pptx.enum.shapes import MSO_SHAPE
shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, w, h)
shape.fill.solid(); shape.fill.fore_color.rgb = CARD_BG
shape.line.color.rgb = CARD_BORDER; shape.line.width = Pt(0.5)

# Circle / ellipse with centered text (hero dots, KPI rings, decorative anchors)
circle = slide.shapes.add_shape(MSO_SHAPE.OVAL, cx - r, cy - r, 2*r, 2*r)
circle.fill.solid(); circle.fill.fore_color.rgb = COLOR_ACCENT
circle.line.fill.background()
tf = circle.text_frame; tf.word_wrap = True
p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
p.text = "42%"; p.font.size = Pt(28); p.font.bold = True; p.font.color.rgb = WHITE

# Connector line with arrow (relationships between free-positioned shapes)
from pptx.enum.shapes import MSO_CONNECTOR_TYPE
conn = slide.shapes.add_connector(MSO_CONNECTOR_TYPE.STRAIGHT, x1, y1, x2, y2)
conn.line.color.rgb = COLOR_PRIMARY; conn.line.width = Pt(2)

# Decorative / emphasis shapes — OVAL, STAR_5_POINT, HEART, CLOUD, PENTAGON,
# RIGHT_ARROW, LEFT_BRACE, LIGHTNING_BOLT, SMILEY_FACE, DIAMOND, HEXAGON, etc.
star = slide.shapes.add_shape(MSO_SHAPE.STAR_5_POINT, left, top, Cm(2), Cm(2))
star.fill.solid(); star.fill.fore_color.rgb = COLOR_ACCENT

# Freeform polygon (draw any polyline shape — e.g. custom callouts, flags, arcs)
ff = slide.shapes.build_freeform(start_x=x0, start_y=y0, scale=1.0)
ff.add_line_segments([(x1, y1), (x2, y2), (x3, y3)], close=True)
freeform_shape = ff.convert_to_shape()

# Table
tbl_shape = slide.shapes.add_table(rows, cols, left, top, width, row_h).table
cell = tbl_shape.cell(0, 0); cell.text = "Header"

# EMU quick-ref: Cm(1)=360000, Inches(1)=914400, Pt(1)=12700
```

---

## Download and Convert Assets

```python
from urllib.request import urlretrieve
urlretrieve(url, os.path.join(ASSETS, "filename.jpg"))

# Convert PNG → JPG (smaller, no transparency issues)
from PIL import Image
img = Image.open(path)
img.convert("RGB").save(path.replace(".png", ".jpg"), quality=85)
```
