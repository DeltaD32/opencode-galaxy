# BMW Brand Styling Guide

Extracted from `Presentation1.pptx` master slide on February 1, 2026.

## Color Scheme (BMW Group 21)

| Role | Hex Code | RGB | Usage |
|------|----------|-----|-------|
| **Dark 1 (Text)** | `#000000` | rgb(0, 0, 0) | Primary text color |
| **Light 1 (Background)** | `#FFFFFF` | rgb(255, 255, 255) | Background, white elements |
| **Dark 2 (Primary Brand)** | `#035970` | rgb(3, 89, 112) | Ocean Blue - primary brand color |
| **Light 2** | `#92A2BD` | rgb(146, 162, 189) | Light blue-gray accents |
| **Accent 1** | `#548D9E` | rgb(84, 141, 158) | Teal accent |
| **Accent 2** | `#85ACB9` | rgb(133, 172, 185) | Light teal |
| **Accent 3** | `#ABC4CF` | rgb(171, 196, 207) | Pale blue |
| **Accent 4** | `#C8D7E0` | rgb(200, 215, 224) | Light gray-blue |
| **Accent 5** | `#DEE5EC` | rgb(222, 229, 236) | Very light blue |
| **Accent 6** | `#E8EBF1` | rgb(232, 235, 241) | Near white blue |

### Custom Brand Colors

| Name | Hex | Darker Variant | 30% Lighter | 60% Lighter |
|------|-----|----------------|-------------|-------------|
| Ocean Blue | `#035970` | `#024152` | `#4F8B9B` | `#A7C5CD` |
| Night Blue | `#173B68` | `#133155` | `#687F9D` | `#B9C4D1` |
| Sky Blue | `#7B9AC0` | `#5179A9` | `#A8BED4` | `#D0DDE8` |
| Turquoise | `#009A97` | `#00777A` | `#66C2C1` | `#B2E0E0` |
| Yellow | `#FAD022` | `#D2A000` | `#FCE37A` | `#FDF1BC` |
| Orange | `#E96D0C` | `#AF5009` | `#F69954` | `#FBCCA9` |
| Purple | `#8D1E77` | `#6B175B` | `#BB78AD` | `#DDBBD6` |
| Red | `#AC1640` | `#76102D` | `#CD738C` | `#E6B9C5` |
| Cyan | `#079EDA` | `#05709B` | `#6DCBF1` | `#B1E7FD` |
| Green | `#508130` | `#365620` | `#8BB86D` | `#C9DEBB` |

> **Usage note:** For accent usage in slides, prefer **Accent 2 Blue-Gray `#85ACB9`** over Turquoise `#009A97`. Turquoise falls outside the preferred blue-gray range. The recommended accent palette is: Ocean Blue `#035970`, Teal `#548D9E`, Blue-Gray `#85ACB9`, Ice Blue Accent 3 `#ABC4CF`, Ice Blue Accent 4 `#C8D7E0`, Ice Blue Accent 5 `#DEE5EC`, Ice Blue Accent 6 `#E8EBF1`.

---

## Typography

### Fonts
- **Primary Font (Major):** BMWGroupTN Condensed
- **Secondary Font (Minor):** BMWGroupTN Condensed
- **Fallback:** Arial

### Text Sizes and Styles

| Element | Size | Style | Color |
|---------|------|-------|-------|
| **Slide Title** | 26pt | UPPERCASE, left-aligned | Ocean Blue `#035970` |
| **Body Text** | 18pt | Normal | Black `#000000` |
| **Level 2 Bullet** | 18pt | Normal | Black |
| **Footer Text** | 10pt | Normal | Gray (65% luminosity) |
| **Classification** | 12pt | Normal | Red `#C00000` at 50% opacity |

### Bullet Style

The BMW master slide defines specific bullet characters for each level:

| Level | Character | Font | Notes |
|-------|-----------|------|-------|
| **Level 1** | ▪ (small filled square) | Wingdings | Renders as small filled square in Wingdings |
| **Level 2-5** | - (dash) | BMW Group Condensed | Simple hyphen/dash |

- **Bullet Color:** Ocean Blue `#035970` (schemeClr tx2)
- **Indent per level:** 190,800 EMU 
- **Margin progression:** Level 1: 190800, Level 2: 381600, Level 3: 572400, Level 4: 763200, Level 5: 954000
- **Spacing after:** 600 points

**Important:** When the font doesn't support BMW Group Condensed, use:
- **Level 1:** Unicode bullet `•` (U+2022) or `▪` (U+25AA small black square)
- **Level 2+:** Simple dash `-`

---

## Layout Specifications

### Title Slide Layout ("Title | Full Picture")

The title slide uses the **"Title | Full Picture"** layout which has a full-slide picture placeholder containing a BMW gradient background JPEG image.

> **Key rule:** Always use `add_slide(layout)` with this layout. The picture placeholder (idx=21) already contains the gradient background image. **Never draw a manual `MSO_SHAPE.RECTANGLE` with gradient fill** — that ignores the template's built-in background.

#### Background/Picture Placeholder (idx=21)
- **Type:** Picture placeholder (contains gradient JPEG)
- **Position:** Full slide (x=0, y=0)
- **Size:** 12,192,000 x 6,572,262 EMU (13.33" x 7.25")
- **Fill:** BMW gradient background JPEG image (extracted to `extracted-assets/title-bg-default.jpeg`)
  - Visual: Ocean Blue `#035970` (top) → Darker Ocean Blue `#012C38` (bottom)
- **Usage:** Inherits automatically from layout — no action needed

#### Title Text
- **Position:** x = 0 (with 572,400 EMU left padding), y = 3,837,978 EMU (~4.23")
- **Size:** Full width, height = 1,376,513 EMU (~1.52")
- **Font:** 40pt, UPPERCASE, white (`#FFFFFF`)
- **Background:** None (transparent)
- **Alignment:** Left, bottom-anchored

#### Subtitle Text  
- **Position:** x = 0 (with 572,400 EMU left padding), y = 5,311,365 EMU (~5.86")
- **Size:** Full width, height = 453,183 EMU (~0.5")
- **Font:** 20pt, UPPERCASE, white (`#FFFFFF`)
- **Background:** None (transparent)
- **Alignment:** Left

### Content Slide Layout

### Slide Dimensions
- **Width:** 12,192,000 EMU (13.333 inches / 16:9)
- **Height:** 6,858,000 EMU (7.5 inches)

### Content Area
- **Left Margin:** 488,947 EMU (~0.54 inches)
- **Title Position:** Top-left, x = 488,947 EMU, y = 347,184 EMU (~0.38 inches from top)
- **Title Width:** 11,224,684 EMU (~11.68 inches)
- **Title Height:** 400,110 EMU (~0.44 inches)
- **Body Area Position:** x = 488,947 EMU, y = 1,413,933 EMU (~1.56 inches from top)
- **Body Area Width:** 11,224,684 EMU (~11.68 inches)
- **Body Area Height:** 4,894,792 EMU (~5.4 inches)

### Footer
- **Built-in shapes on master slide** (inherited automatically by all slides):
  - `FußzeileAU1`: Department/date/author text — update via `_update_master_footer()` with format "Dept | Date | Topic"
  - `SeitenzahlAU1`: Auto page numbers in format "– ‹#› –"
  - `BMW Group Trennlinie`: Separator line at y ≈ 7.19"
  - `Textfeld 3`: Classification label (e.g., "CONFIDENTIAL")
- **Separator Line:** Full width at y = 6,572,265 EMU
- **Line Weight:** 12,700 EMU (1pt)
- **Line Opacity:** 25%
- **Do NOT** draw manual footer elements (lines, text boxes, page numbers) — these duplicate the master's inherited footer

---

## Asset Files

Located in `references/master-slide-assets/` (legacy) and `references/extracted-assets/` (preferred):

| File | Description |
|------|-------------|
| `extracted-assets/title-bg-default.jpeg` | **BMW gradient background JPEG** from picture placeholder |
| `master-slide-assets/image2.png` | BMW Roundel logo (reference only — layout SmartArt renders this) |
| `master-slide-assets/image4.png` | BMW GROUP text wordmark (reference only — layout SmartArt renders this) |
| `master-slide-assets/image3.svg` | BMW GROUP text logo (SVG) |
| `master-slide-assets/image5.svg` | BMW Roundel logo (SVG) |
| `master-slide-assets/theme1.xml` | Full theme color definitions |
| `master-slide-assets/slideMaster1.xml` | Master slide layout specifications |

---

## Usage Notes

1. **Title slides** must use the **"Title | Full Picture"** layout — it has the gradient background JPEG baked into the picture placeholder (idx=21). **Do NOT draw a manual gradient rectangle.**
2. **Title slide background** is a picture placeholder with a JPEG image — it inherits automatically from the layout
3. **Title/subtitle text** — set text on the `ctrTitle` and `subTitle` placeholders; they have NO fill (transparent over the background image)
4. **Department badge** — set text on the `body` placeholder (idx=22); it already has the correct position and style
5. **Logos** — SmartArt placeholders in the title layout (idx=24 roundel, idx=23 group) render logos automatically. **Do NOT overlay PNG images.**
6. **Footer** — The master has built-in footer shapes (`FußzeileAU1`, `SeitenzahlAU1`, separator line). Update `FußzeileAU1` text with "Dept | Date | Topic". **Do NOT draw manual footer elements.**
7. **Content slides** use white background with Ocean Blue titles
7. **All titles** should be UPPERCASE
8. **Maximum 5 bullets** per slide
9. **Footer separator** is a subtle gray line at 25% opacity
10. **Classification labels** (e.g., "CONFIDENTIAL") appear centered in red
