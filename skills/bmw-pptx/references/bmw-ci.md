# BMW Corporate Identity -- PowerPoint

## Master Template

File: `tools/pptx/assets/BMW-Master-2025-EF-clean.pptx` -- 13.333" x 7.5" (16:9), 0 slides, 15 layouts.

## Theme Colors

| Role | Hex | Python Constant | Usage |
|------|-----|-----------------|-------|
| Dark 1 | `000000` | `BMW.BLACK` | Black text |
| Light 1 | `FFFFFF` | `BMW.WHITE` | White text, backgrounds |
| Dark 2 | `035970` | `BMW.DARK_TEAL` | Headings, dark accents |
| Light 2 | `92A2BD` | `BMW.SECONDARY` | Secondary text, borders |
| Accent 1 | `39B3E6` | `BMW.LIGHT_BLUE` | Primary accent (use sparingly) |
| Accent 2 | `079EDA` | `BMW.MEDIUM_BLUE` | Charts, icons |
| Accent 3 | `8CB7E3` | `BMW.SOFT_BLUE` | Secondary charts |
| Accent 4 | `C8D7E0` | `BMW.CARD_BG` | Card backgrounds, dividers |
| Accent 5 | `DEE5EC` | `BMW.SUBTLE_BG` | Subtle backgrounds |
| Accent 6 | `E8EBF1` | `BMW.STRIPE_BG` | Table stripes |

High-contrast pairings: white on `035970`, black on `DEE5EC`/`E8EBF1`.

**CRITICAL -- text contrast:** The palette is almost entirely blues/teals. On any dark or blue/teal background (including gradients), text MUST be `WHITE`, `SUBTLE_BG`, or `STRIPE_BG`. Never use `LIGHT_BLUE`, `MEDIUM_BLUE`, `SOFT_BLUE`, or `SECONDARY` as text color on dark/teal/gradient backgrounds -- they are unreadable. On light backgrounds, use `BLACK` or `DARK_TEAL` for text.

Font: **BMWGroupTN Condensed** (fallback: BMW Group Condensed, then Arial)

## Slide Layouts (15 total)

| Idx | Name | Use for |
|-----|------|---------|
| 0 | Title \| Full Picture | Title slides (idx=0 title, idx=1 subtitle) |
| 1 | Divider \| Half Area Right | Section dividers |
| 2 | Grid \| 1 | Freeform content |
| 3 | Grid \| 2x2 | 2x2 grid |
| 4-8 | Content \| 1/2/3/4/2x2 | 1-4 columns or 2x2 (idx=17-20) |
| 9-10 | Content \| Picture L/R | Image + text |
| 11-13 | Content \| Picture 2/3/4 | Multi image-text pairs |
| 14 | Key Note | Centered key message |

## Helper Module -- `bmw_pptx.py`

Location: `tools/pptx/bmw_pptx.py`

### Quick Start

```python
from bmw_pptx import BmwPresentation, BMW, set_font

bmw = BmwPresentation()
slide = bmw.add_title_slide("My Title", subtitle="Month Year")
slide = bmw.add_grid_slide("Section")  # freeform content area
bmw.save("output.pptx")
```

### High-Level Slide Methods

| Method | Layout | Placeholders |
|--------|--------|--------------|
| `add_title_slide(title, subtitle)` | 0 -- Title \| Full Picture | idx=0 (title), idx=1 (subtitle) |
| `add_divider_slide(title)` | 1 -- Divider \| Half Area Right | idx=0 (title) |
| `add_content_slide(title, body)` | 4 -- Content \| 1 | idx=0 (title), idx=17 (content) |
| `add_two_column_slide(title, left, right)` | 5 -- Content \| 2 | idx=0, idx=17 (left), idx=18 (right) |
| `add_grid_slide(title)` | 2 -- Grid \| 1 | idx=0 (title), freeform below |
| `add_keynote_slide(message)` | 14 -- Key Note | idx=0 (centered title) |
| `add_slide(name_or_index)` | Any | Returns raw slide |

### Font Helper

```python
set_font(run_or_paragraph_or_textframe, size=16, bold=True, color=BMW.WHITE)
```

Applies BMWGroupTN Condensed and styling to a Run, Paragraph, or TextFrame.

### Direct Access

For custom shapes, images, or tables, use `bmw.prs` (the underlying `python-pptx.Presentation` object). All BMW theme colors, fonts, and slide dimensions are inherited from the template.

## Rules

- Use BMW theme colors only for primary elements. Custom shapes: pick Accent 1-6.
- Prefer layout placeholders over freeform text boxes.
- Title placeholder (idx=0) position varies: top-left on content, centered on title/key note.
