# Brand Styling Guide — Aiconic Grand Prix

Extracted from `Overview_Aiconic-GrandPrix  -  Read-Only.pptx` on 2026-06-24.

---

## BMW Group CI Anchor

This style is a **clone** — it stands on its own visually but anchors to BMW Group CI
structural rules. The table below shows what is inherited vs overridden.

| Element | Inherited from BMW CI | This style's value |
|---------|----------------------|-------------------|
| Slide dimensions | ✅ 13.333" × 7.5" (16:9) | same |
| Font family constraint | ✅ BMW Group typeface | `BMWGroupTN Condensed` |
| Footer shape names | ✅ `FußzeileAU1`, `SeitenzahlAU1`, `BMW Group Trennlinie` | same (from master) |
| Primary brand color | ❌ overridden | `#F69954` (extracted from this deck) |
| Dark layouts | ❌ overridden | 20 dark / 1 light layouts |
| Title color | ❌ overridden | `#FFFFFF` |

### Font Family Rule

This style uses BMW Group fonts — CI compliant.

Permitted BMW Group font families (for any BMW Group presentation):
- `BMWGroupTN Condensed` — primary, all weights
- `BMW Group Condensed` — alternative / legacy
- `BMW Group` — long-form body text

**Active in this style:** `BMWGroupTN Condensed` (headings) / `BMWGroupTN Condensed` (body)

### Primary Brand Color for This Style

| Color | Hex | Source |
|-------|-----|--------|
| Primary | `#F69954` | dark layout background fill |
| Supporting palette | `#035970` | extracted shape fills |

---

## Slide Dimensions

- **Width:** 13.333" (16:9)
- **Height:** 7.5"
- **Width EMU:** 12192000
- **Height EMU:** 6858000

---

## Theme Color Scheme — `BMW Group 21`

These are the canonical slot values from `<a:clrScheme>`. Every shape that uses a
scheme color (e.g. `tx2`, `accent1`) inherits from this table.

| Slot | Hex | Label |
|------|-----|-------|
| `dk1` | `#000000` | Text/Dark 1 (primary text) ← also `tx1` |
| `lt1` | `#FFFFFF` | Background/Light 1 (slide bg) ← also `bg1` |
| `dk2` | `#035970` | Dark 2 (primary brand) ← also `tx2` |
| `lt2` | `#92A2BD` | Light 2 ← also `bg2` |
| `accent1` | `#548D9E` | Accent 1 |
| `accent2` | `#85ACB9` | Accent 2 |
| `accent3` | `#ABC4CF` | Accent 3 |
| `accent4` | `#C8D7E0` | Accent 4 |
| `accent5` | `#DEE5EC` | Accent 5 |
| `accent6` | `#E8EBF1` | Accent 6 |
| `hlink` | `#000000` | Hyperlink |
| `folHlink` | `#000000` | Followed Hyperlink |

---

## Theme Font Scheme — `BMW Group 2021`

| Token | Resolved Font | Role |
|-------|---------------|------|
| `+mj-lt` | `BMWGroupTN Condensed` | Headings / titles |
| `+mn-lt` | `BMWGroupTN Condensed` | Body text |

---

## Master Text Styles (from `p:txStyles`)

### Title Style

| Attr | Value |
|------|-------|
| Font size | **26.0pt** |
| Font | `BMWGroupTN Condensed` |
| Capitalization | `all` |
| Bold | False |
| Color | `#FFFFFF` |
| Alignment | `l` |
| Bullet | none |

### Body Style — Bullet Levels

| Lvl | Size | Font | Bullet | Bullet Font | Bullet Color | Space After | Indent (EMU) |
|-----|------|------|--------|-------------|--------------|-------------|--------------|
| 1 | 18.0 | `BMWGroupTN Condensed` | `§` | `Wingdings` | `#FFFFFF` | 6.0 | 190800 |
| 2 | 18.0 | `BMWGroupTN Condensed` | `-` | `BMW Group Condensed` | `#FFFFFF` | 6.0 | 381600 |
| 3 | 18.0 | `BMWGroupTN Condensed` | `-` | `BMW Group Condensed` | `#FFFFFF` | 6.0 | 572400 |
| 4 | 18.0 | `BMWGroupTN Condensed` | `-` | `BMW Group Condensed` | `#FFFFFF` | 6.0 | 763200 |
| 5 | 18.0 | `BMWGroupTN Condensed` | `-` | `BMW Group Condensed` | `#FFFFFF` | 6.0 | 954000 |
| 6 | 18.0 | `BMWGroupTN Condensed` | `•` | `Arial` | `—` | — | 2514600 |
| 7 | 18.0 | `BMWGroupTN Condensed` | `•` | `Arial` | `—` | — | 2971800 |
| 8 | 18.0 | `BMWGroupTN Condensed` | `•` | `Arial` | `—` | — | 3429000 |
| 9 | 18.0 | `BMWGroupTN Condensed` | `•` | `Arial` | `—` | — | 3886200 |

---

## Master Background

- **Type:** `inherited`

---

## Master Shapes (footer, lines, logos)

| Name | Type | Position | Size | Fill | Text |
|------|------|----------|------|------|------|
| `Objekt 9` | EMBEDDED_OLE_OBJECT (7) | 0.002"×0.002" | 0.002"×0.002" | `—` |  |
| `Textplatzhalter 1` | PLACEHOLDER (14) | 0.535"×1.546" | 12.275"×5.353" | `—` | Click to edit text
Second level
Third le |
| `Titelplatzhalter 1` | PLACEHOLDER (14) | 0.535"×0.38" | 12.275"×0.438" | `—` | Click to edit Action Title. 26pt. Upperc |
| `BMW Group Trennlinie` | LINE (9) | -0.0"×7.188" | 13.333"×0.0" | `—` |  |
| `SeitenzahlAU1` | AUTO_SHAPE (1) | 12.4"×7.26" | 0.41"×0.168" | `—` | - ‹#› - |
| `Textfeld 3` | TEXT_BOX (17) | 6.164"×7.231" | 1.036"×0.2" | `—` | CONFIDENTIAL |
| `FußzeileAU1` | TEXT_BOX (17) | 0.535"×7.26" | 1.501"×0.168" | `—` | Department | Date | Author |

---

## Layouts

| Layout Name | Background | Dark? | Title Color | Title Size | Placeholders |
|-------------|-----------|-------|-------------|------------|--------------|
| `M_Dark_Title | Full Picture` | inherited | yes | #FFFFFF | 40.0pt | 5 |
| `GenAI_Dark_Title | Full Picture` | inherited | yes | #FFFFFF | 40.0pt | 6 |
| `1_GenAI_Dark_Title | Full Picture` | inherited | yes | #FFFFFF | 40.0pt | 5 |
| `M_Dark_Divider | Full Area` | inherited | yes | #FFFFFF | 40.0pt | 2 |
| `M_Dark_Grid | 2` | inherited | yes | inherited | inherited | 1 |
| `M_Dark_Grid | 1` | inherited | yes | inherited | inherited | 1 |
| `M_Gradient_Content | 1` | inherited | yes | inherited | inherited | 2 |
| `M_Dark_Content | 1` | inherited | yes | inherited | inherited | 2 |
| `GENAI_Gradient_Content | 1` | inherited | yes | inherited | inherited | 2 |
| `1_GENAI_Gradient_Content | 1` | inherited | yes | inherited | inherited | 0 |
| `M_Dark_Content | 2` | inherited | yes | inherited | inherited | 3 |
| `M_Dark_Content | 3` | inherited | yes | inherited | inherited | 4 |
| `M_Dark_Content | 4` | inherited | yes | inherited | inherited | 5 |
| `M_Dark_Content | 2x2` | inherited | yes | inherited | inherited | 5 |
| `M_Dark_Content | Picture Left` | inherited | yes | inherited | inherited | 3 |
| `M_Dark_Content | Picture Right` | inherited | yes | inherited | inherited | 3 |
| `M_Dark_Content | Picture | 2` | inherited | yes | inherited | inherited | 5 |
| `M_Dark_Content | Picture | 3` | inherited | yes | inherited | inherited | 7 |
| `M_Dark_Content | Picture | 4` | inherited | yes | inherited | inherited | 9 |
| `M_Dark_Key Note` | inherited | yes | #FFFFFF | 40.0pt | 1 |
| `D. Four column green` | inherited | no | inherited | inherited | 3 |

---

## Shape Fill Colors (across all slides)

These are the actual fill colors used on slide shapes — the true brand palette.

### Hardcoded Hex Colors (by frequency)

| Hex | Count |
|-----|-------|

### Scheme-color Fills (by frequency)

| Scheme Slot | Count | Resolved Hex |
|------------|-------|--------------|

---

## Typography Summary

| Element | Font | Size | Notes | Color |
|---------|------|------|-------|-------|
| **Title (default)** | `BMWGroupTN Condensed` | 26.0pt | master txStyles default | `#FFFFFF` |
| **Title (full-bleed)** | `BMWGroupTN Condensed` | 40.0pt | layout override (dark/picture title slides) | `#FFFFFF` |
| **Body** | `BMWGroupTN Condensed` | 18.0pt | | `#FFFFFF` |
| **Footer** | `BMWGroupTN Condensed` | 7.0pt | | — |

---

## Usage Notes

1. **Primary brand color** (theme `dk2`): `#035970`
2. **Title font:** `BMWGroupTN Condensed` — resolves from theme token `+mj-lt`
3. **Body font:** `BMWGroupTN Condensed` — resolves from theme token `+mn-lt`
4. **Bullet (level 1):** char `§` in `Wingdings` — color `#FFFFFF`
5. **Title scheme color:** `bg1` → `#FFFFFF`
6. See `style.json` for the complete machine-readable profile.