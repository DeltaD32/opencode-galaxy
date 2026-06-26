# Brand Styling Guide — BMW CI

Extracted from `Presentation1.pptx` on 2026-06-24.

---

## BMW Group Corporate Identity Rules

This is the **reference style**. All other registered styles are clones that inherit
structural elements from this CI and override visual ones.

### Font Family Constraint

All BMW Group presentations **must** use a BMW Group typeface. Permitted font families:

| Family | Variants | Use |
|--------|----------|-----|
| `BMWGroupTN Condensed` | Regular, Bold, Italic | Titles, body, UI labels (primary) |
| `BMW Group Condensed`  | Regular, Bold         | Alternative body / legacy decks   |
| `BMW Group`            | Regular, Bold, Italic | Long-form body text               |

> **Never substitute** Arial, Calibri, or other system fonts in BMW presentations.
> If a BMW font is unavailable on the rendering machine, flag it rather than silently falling back.

### Primary Brand Color

- **Ocean Blue** `#035970` — the mandatory primary color for titles, headers, and key accents.
- Secondary palette: `#548D9E` (accent1), `#85ACB9` (accent2), `#92A2BD` (lt2).
- Never use red, orange, or non-BMW-palette colors for structural elements in the default CI.

### Structural Elements Inherited by All Clones

| Element | Spec |
|---------|------|
| Slide dimensions | 13.333" × 7.5" (16:9, 12192000 × 6858000 EMU) |
| Footer shape | `FußzeileAU1` at `(0.535", 7.26")` — update text, never reposition |
| Page number | `SeitenzahlAU1` at `(12.4", 7.26")` — text `- ‹#› -` |
| Divider line | `BMW Group Trennlinie` — horizontal rule above footer |

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
| Color | `#035970` |
| Alignment | `l` |
| Bullet | none |

### Body Style — Bullet Levels

| Lvl | Size | Font | Bullet | Bullet Font | Bullet Color | Space After | Indent (EMU) |
|-----|------|------|--------|-------------|--------------|-------------|--------------|
| 1 | 18.0 | `BMWGroupTN Condensed` | `§` | `Wingdings` | `#035970` | 6.0 | 190800 |
| 2 | 18.0 | `BMWGroupTN Condensed` | `-` | `BMW Group Condensed` | `#035970` | 6.0 | 381600 |
| 3 | 18.0 | `BMWGroupTN Condensed` | `-` | `BMW Group Condensed` | `#035970` | 6.0 | 572400 |
| 4 | 18.0 | `BMWGroupTN Condensed` | `-` | `BMW Group Condensed` | `#035970` | 6.0 | 763200 |
| 5 | 18.0 | `BMWGroupTN Condensed` | `-` | `BMW Group Condensed` | `#035970` | 6.0 | 954000 |
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
| `FußzeileAU1` | TEXT_BOX (17) | 0.535"×7.26" | 1.501"×0.168" | `—` | Department | Date | Author |
| `Textfeld 3` | TEXT_BOX (17) | 6.164"×7.231" | 1.036"×0.2" | `—` | CONFIDENTIAL |

---

## Layouts

| Layout Name | Background | Dark? | Title Color | Title Size | Placeholders |
|-------------|-----------|-------|-------------|------------|--------------|
| `Title | Full Area` | inherited | no | #FFFFFF | 40.0pt | 6 |
| `Title | Full Picture` | inherited | no | #FFFFFF | 40.0pt | 6 |
| `Divider | Half Area Right` | inherited | no | #000000 | 40.0pt | 3 |
| `Grid | 1` | inherited | no | inherited | inherited | 1 |
| `Grid | 2` | inherited | no | inherited | inherited | 1 |
| `Grid | 3` | inherited | no | inherited | inherited | 1 |
| `Grid | 4` | inherited | no | inherited | inherited | 1 |
| `Grid | 2x2` | inherited | no | inherited | inherited | 1 |
| `Content | 1` | inherited | no | inherited | inherited | 2 |
| `Content | 2` | inherited | no | inherited | inherited | 3 |
| `Content | 3` | inherited | no | inherited | inherited | 4 |
| `Content | 4` | inherited | no | inherited | inherited | 5 |
| `Content | 2x2` | inherited | no | inherited | inherited | 5 |
| `Content | Area` | inherited | no | inherited | inherited | 1 |
| `Content | Picture Left` | inherited | no | inherited | inherited | 3 |
| `Content | Picture Right` | inherited | no | inherited | inherited | 3 |
| `Content | Picture | 2` | inherited | no | inherited | inherited | 5 |
| `Content | Picture | 3` | inherited | no | inherited | inherited | 7 |
| `Content | Picture | 4` | inherited | no | inherited | inherited | 9 |
| `Key Note` | inherited | no | #FFFFFF | 40.0pt | 2 |

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
| **Title (default)** | `BMWGroupTN Condensed` | 26.0pt | master txStyles default | `#035970` |
| **Title (full-bleed)** | `BMWGroupTN Condensed` | 40.0pt | layout override (dark/picture title slides) | `#035970` |
| **Body** | `BMWGroupTN Condensed` | 18.0pt | | `#000000` |
| **Footer** | `BMWGroupTN Condensed` | 10.0pt | | — |

---

## Usage Notes

1. **Primary brand color** (theme `dk2`): `#035970`
2. **Title font:** `BMWGroupTN Condensed` — resolves from theme token `+mj-lt`
3. **Body font:** `BMWGroupTN Condensed` — resolves from theme token `+mn-lt`
4. **Bullet (level 1):** char `§` in `Wingdings` — color `#035970`
5. **Title scheme color:** `tx2` → `#035970`
6. See `style.json` for the complete machine-readable profile.