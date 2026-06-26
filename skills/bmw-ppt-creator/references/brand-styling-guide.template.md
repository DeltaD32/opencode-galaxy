# BMW Brand Styling Guide (Template Flow)

Extracted from `2024-12-11 JD All Hands Telematics_new.pptx` on February 13, 2026.

## Slide Dimensions

- **Width:** 13.333" (16:9)
- **Height:** 7.5"

## Typography

| Element | Font | Size | Style |
|---------|------|------|-------|
| **Content Slide Title** | BMWGroupTN Condensed | 26pt | UPPERCASE (cap=all), left-aligned, Bright Blue `#00B0F0` |
| **Body Text** | BMWGroupTN Condensed | 18pt | Normal, white `#FFFFFF` (dark layouts) or black `#000000` (light layouts) |
| **Accent / Q&A Title** | BMWGroupTN Condensed | 36pt | Bold, white or Bright Blue |
| **Highlight / Topic** | BMWTypeNext Condensed | 54pt | Bold, Bright Blue `#00B0F0` |
| **Label / Caption** | BMWGroupTN Condensed | 24pt | Normal, Ice Blue `#E8EBF1` |
| **Footer Text** | BMWGroupTN Condensed (inherited) | 10pt | White (schemeClr bg1) |
| **Department Badge** | (inherited from layout) | 14pt | White on Ocean Blue |

### Theme Fonts
- **Major (headings):** BMWGroupTN Condensed (`+mj-lt`)
- **Minor (body):** BMWGroupTN Condensed (`+mn-lt`)
- **Fallback:** Arial

## Color Scheme

Theme: **BMW Group 21** (inherited from master slide):

| Role | Hex Code | Usage |
|------|----------|-------|
| **dk1** | `#000000` | Black — text on light backgrounds |
| **lt1 (bg1)** | `#FFFFFF` | White — body text on dark backgrounds, light slide BG |
| **dk2** | `#035970` | Ocean Blue — department badge fill, secondary headings |
| **lt2** | `#92A2BD` | Gray — muted text |
| **accent1** | `#548D9E` | Teal |
| **accent2** | `#85ACB9` | Blue-Gray |
| **accent3** | `#ABC4CF` | Ice Blue Accent 3 |
| **accent4** | `#C8D7E0` | Ice Blue Accent 4 |
| **accent5** | `#DEE5EC` | Ice Blue Accent 5 |
| **accent6** | `#E8EBF1` | Ice Blue Accent 6 — labels, captions on dark |
| **Title Color** | `#00B0F0` | Bright Blue — content slide titles, bullet markers |
| **Accent Cyan** | `#079EDA` | Secondary highlight |
| **Title Slide BG** | Gradient JPEG | Built into picture placeholder |

### Dominant Slide Colors (from extraction)

| Color | Frequency | Usage |
|-------|-----------|-------|
| `#035970` | 8 | Ocean Blue — shapes, badges |
| `#00B0F0` | 7 | Bright Blue — titles, bullets |
| `#E8EBF1` | 5 | Ice Blue — labels on dark |
| `#FFFFFF` | 3 | White — body text |
| `#079EDA` | 1 | Accent Cyan — highlights |

## Layout Specifications

### Title Slide (Layout: "1_Title | Full Picture")

Use `add_slide(layout)` with this layout. The picture placeholder (idx=21) already contains the BMW gradient background JPEG. **Do NOT draw a manual gradient rectangle.**

| Element | Position | Size / Notes |
|---------|----------|------|
| **Background (pic PH idx=21)** | x=0, y=0 | 13.333" x 7.25" — JPEG image inherits from layout |
| **Title (ctrTitle idx=0)** | x=0, y=4.16" | 13.333" x 1.55" — UPPERCASE, left-aligned |
| **Subtitle (subTitle idx=1)** | x=0, y=5.81" | 13.333" x 0.50" |
| **Department Badge (body idx=22)** | x=10.43", y=6.44" | 2.90" x 0.46" |
| **BMW Roundel (dgm idx=24)** | x=0.63", y=0.63" | 1.20" x 0.63" — renders from SmartArt, no overlay needed |
| **BMW GROUP (dgm idx=23)** | x=12.08", y=0.63" | 0.63" x 0.63" — renders from SmartArt, no overlay needed |

### Content Slide (Layout: "Grid | 1")

Light background layout — titles inherit `#00B0F0`, body inherits white (bg1).

| Element | Position | Size |
|---------|----------|------|
| **Title (PH idx=0)** | x=0.53", y=0.38" | 12.28" x 0.44" |
| **Body (PH idx=1)** | x=0.53", y=1.55" | 12.28" x 5.35" |

### Content Slides — Dark Layouts (Most Common in Template)

The template **predominantly uses dark-themed layouts**:
- `Dunkel_Neutral_Teilung_1a` — dark with left content area
- `Dunkel_Neutral_Teilung_1b` — dark with right content area
- `Dunkel_Neutral_Teilung_1c` — dark with full content area
- `Dunkel_Neutral_Teilung_Halb` — dark split layout
- `1_Dunkel_Neutral_3Poly_NEXT` — dark with polygonal accents

When using dark layouts, body text is **white** (schemeClr bg1).

### Light Content Layouts (Also Available)

- `Weiss_Teilung_3er` — white three-column split
- `1_Inhalt mit Hintergrund` — content with background image
- `1_Kombifolie` — combination layout (light)

### Chapter/Section Break Layout

- `2_Kapiteltrenner` — used for Q&A/section breaks
  - Main text: BMWGroupTN Condensed 36pt bold
  - Topic highlight: BMWTypeNext Condensed 54pt bold, `#00B0F0`

## Bullet Style

| Level | Character | Font | Color |
|-------|-----------|------|-------|
| **Level 1** | ▪ (filled square) | Wingdings | Bright Blue `#00B0F0` |
| **Level 2–5** | - (dash) | Symbol | Bright Blue `#00B0F0` |

### Master Body Text Properties
- **Font:** BMWGroupTN Condensed (`+mn-lt`), 18pt
- **Text fill:** White (schemeClr bg1) — designed for dark backgrounds
- **Line spacing:** 100%
- **Space after:** 6pt
- **Alignment:** Left

## Footer

- **Built-in master shapes** (inherited automatically by all slides):
  - `FußzeileAU1`: x=0.53", y=7.18", 2.58" x 0.34" — department/date/topic text, 10pt, white
  - `SeitenzahlAU1`: Auto page numbers
  - `BMW Group Trennlinie`: Separator line
- Update via `_update_master_footer()` — **Do NOT** draw manual footer elements

## Department Badge

- **Shape:** Parallelogram (slanted left edge), inherited from layout placeholder idx=22
- **Fill:** Ocean Blue `#035970`
- **Text:** White, 14pt
- **Position:** Bottom-right of title slide (x=10.43", y=6.44")

## Available Layouts (Full List)

| Layout Name | Type | Notes |
|-------------|------|-------|
| `1_Title \| Full Picture` | Title | Title slide with gradient JPEG background |
| `Grid \| 1` | Content (light) | Single content area, light background |
| `Content \| 1` through `Content \| 4` | Content (light) | Multi-content areas |
| `Content \| 2x2` | Content (light) | 2x2 grid |
| `Content \| Picture Left/Right` | Content (light) | Picture + text |
| `Dunkel_Neutral_Teilung_1a/1b/1c` | Content (dark) | **Most used** in template |
| `Dunkel_Neutral_Teilung_Halb/Mittel/Breit` | Content (dark) | Various dark splits |
| `Weiss_Teilung_3er` | Content (light) | Three-column white |
| `2_Kapiteltrenner` | Section break | Q&A / chapter separator |
| `Benutzerdefiniertes Layout` | Custom | Blank custom layout |
