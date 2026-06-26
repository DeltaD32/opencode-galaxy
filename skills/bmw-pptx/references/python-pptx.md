# python-pptx Cheat Sheet

## Setup

```bash
pip install python-pptx
```

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

prs = Presentation()
prs.slide_width = Inches(13.333)   # 16:9
prs.slide_height = Inches(7.5)
```

For BMW branded: use `from bmw_pptx import BmwPresentation, BMW` instead. See [bmw-ci.md](bmw-ci.md).

## Slides

```python
slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
# Inspect layouts:
for i, layout in enumerate(prs.slide_layouts): print(i, layout.name)
```

## Text Boxes

```python
txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.5), Inches(9), Inches(1))
tf = txBox.text_frame
tf.word_wrap = True
tf.vertical_anchor = MSO_ANCHOR.MIDDLE  # TOP, MIDDLE, BOTTOM

p = tf.paragraphs[0]
p.text = "Title"
p.font.size = Pt(36)
p.font.bold = True
p.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
p.alignment = PP_ALIGN.LEFT

# Rich text
run1 = p.add_run(); run1.text = "Bold "; run1.font.bold = True
run2 = p.add_run(); run2.text = "normal"
```

## Shapes

```python
# Rectangle
slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1), Inches(1), Inches(3), Inches(2))

# Rounded rectangle
shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1), Inches(1), Inches(3), Inches(2))
shape.fill.solid()
shape.fill.fore_color.rgb = RGBColor(0x1E, 0x27, 0x61)
shape.adjustments[0] = 0.05  # corner radius (0-1)
shape.line.fill.background()  # no border

# Line
conn = slide.shapes.add_connector(1, Inches(1), Inches(3), Inches(5), Inches(3))
conn.line.color.rgb = RGBColor(0x99, 0x99, 0x99)
conn.line.width = Pt(1)

# Text inside shapes
shape.text_frame.word_wrap = True
shape.text_frame.paragraphs[0].text = "Label"
shape.text_frame.paragraphs[0].font.size = Pt(14)
shape.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
```

## Images

```python
slide.shapes.add_picture("image.png", Inches(1), Inches(1), Inches(4), Inches(3))
# From BytesIO:
from io import BytesIO
slide.shapes.add_picture(BytesIO(image_bytes), Inches(1), Inches(1), Inches(4), Inches(3))
```

## Backgrounds

```python
slide.background.fill.solid()
slide.background.fill.fore_color.rgb = RGBColor(0x1E, 0x27, 0x61)
```

## Tables

```python
table = slide.shapes.add_table(3, 4, Inches(0.5), Inches(1.5), Inches(9), Inches(2)).table
table.cell(0, 0).text = "Header"
cell = table.cell(0, 0)
cell.fill.solid()
cell.fill.fore_color.rgb = RGBColor(0x02, 0x80, 0x90)
```

## Icons via Unicode Shapes

```python
def add_icon(slide, text, x, y, size=0.6, bg_color="028090", fg_color="FFFFFF", font_size=20):
    shape = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(size), Inches(size))
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor.from_string(bg_color)
    shape.line.fill.background()
    p = shape.text_frame.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = RGBColor.from_string(fg_color)
    p.alignment = PP_ALIGN.CENTER

# Usage: add_icon(slide, "★", 0.5, 1.0)
# Symbols: ★ ⚙ ✓ ✗ ◆ ▶ ⚡ (avoid emoji -- inconsistent in PowerPoint)
```

## Slide Operations (without XML pipeline)

```python
from copy import deepcopy

def delete_slide(prs, slide_index):
    """Delete slide at given index (0-based)."""
    rId = prs.slides._sldIdLst[slide_index].get(
        '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
    prs.part.drop_rel(rId)
    del prs.slides._sldIdLst[slide_index]

def move_slide(prs, old_index, new_index):
    """Move slide from old_index to new_index (0-based)."""
    slides = list(prs.slides._sldIdLst)
    el = slides.pop(old_index)
    slides.insert(new_index, el)
    for child in list(prs.slides._sldIdLst):
        prs.slides._sldIdLst.remove(child)
    for child in slides:
        prs.slides._sldIdLst.append(child)

def duplicate_slide(prs, slide_index):
    """Duplicate slide at given index. Returns the new slide."""
    template = prs.slides[slide_index]
    layout = template.slide_layout
    new_slide = prs.slides.add_slide(layout)
    for shape in template.shapes:
        el = deepcopy(shape.element)
        new_slide.shapes._spTree.append(el)
    # Copy background if set
    if template.background.fill.type is not None:
        new_slide.background._element.attrib.update(template.background._element.attrib)
    return new_slide
```

## Common Pitfalls

1. **Always use `Inches()` or `Pt()`** -- raw integers are EMU (914400/inch)
2. **`RGBColor` takes integers** -- `RGBColor(0x1E, 0x27, 0x61)` or `RGBColor.from_string("1E2761")`, no `#`
3. **First paragraph exists** -- `paragraphs[0]` is always there; use `add_paragraph()` for more
4. **`shape.text` wipes formatting** -- use `paragraphs[0].text` to preserve structure
5. **No native gradient fills** -- use a gradient image instead
6. **Layout indices vary by template** -- inspect layout names before using an index
7. **Remove border**: `shape.line.fill.background()` (not `None` or `0`)
