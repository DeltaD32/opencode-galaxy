---
name: ace-angular-core-theme
description: Alphabet core-theme utility classes for HTML templates — grid, spacing, icons, typography, breakpoints. Use whenever you think you need css changes or any visual/layout adjustments to a template, no matter how small or easy the change is.
metadata:
  version: '1.1.0'
  authors:
    - name: Rutger Van der Auwera
      email: rutger.vanderauwera@partner.bmwgroup.com
  tags:
    - angular
    - frontend
    - css
    - styling
    - fonts
    - core-theme
---

# Alphabet Core Theme — Utility Class Reference

## When to Use

- Building or modifying Angular HTML templates that need grid layout, spacing, icons, or typography
- Styling components visually — always reach for a theme utility class before writing custom CSS
- Adding icons to UI elements
- Keywords: grid, spacing, padding, margin, icon, color, typography, font, theme, layout, CSS, styling, utility class, core-theme

## No Custom CSS for Visual Properties

The theme and core-components handle all visual styling (colors, typography, shadows, borders) automatically. Writing custom CSS for these properties breaks theme consistency and dark-mode support.

Custom CSS is acceptable **only for layout** — properties like `width`, `height`, `position`, `overflow`, `display` (beyond what `flex` or grid classes provide), or `gap` when the grid system doesn't fit. Even then, use `var(--size-*)` tokens for any size values. Only use it when there is no other option.

If you find yourself writing color, text, shadow, or border-radius CSS, either a theme class exists or the core-component handles it internally.

## 1. Grid System

A 12-column CSS Grid system. On mobile (< 768px) all columns span the full width; on `breakpoint-s` (≥ 768px) columns use their declared span.
This grid system can be used to divide the layout horizontally in columns or to center content if applicable.

### Container

| Class | Description |
|---|---|
| `al-ds-grid--12` | 12-column grid container (24px gap, 24px padding) |
| `al-ds-grid--6` | 6-column grid container (24px gap, no padding) |
| `al-ds-grid--12 no-padding` | 12-column grid without horizontal padding |

### Column Span

Pattern: `al-ds-grid__col-span--{columns}-{total}`

| Class | Columns spanned |
|---|---|
| `al-ds-grid__col-span--1-12` | 1 of 12 |
| `al-ds-grid__col-span--2-12` | 2 of 12 |
| `al-ds-grid__col-span--3-12` | 3 of 12 (quarter) |
| `al-ds-grid__col-span--4-12` | 4 of 12 (third) |
| `al-ds-grid__col-span--6-12` | 6 of 12 (half) |
| `al-ds-grid__col-span--8-12` | 8 of 12 (two-thirds) |
| `al-ds-grid__col-span--9-12` | 9 of 12 (three-quarters) |
| `al-ds-grid__col-span--12-12` | 12 of 12 (full width) |

Any value from 1–12 is valid: `al-ds-grid__col-span--{1..12}-12`.

### Column Start

Pattern: `al-ds-grid__col-{column-start}`

Explicitly sets the column a grid item starts at. Combine with a span class to position and size an item at the same time.

| Class | Effect |
|---|---|
| `al-ds-grid__col-1` | Start at column 1 (default flow) |
| `al-ds-grid__col-2` | Start at column 2 |
| `al-ds-grid__col-3` | Start at column 3 |
| `al-ds-grid__col-4` | Start at column 4 |
| `al-ds-grid__col-5` | Start at column 5 |
| `al-ds-grid__col-6` | Start at column 6 |
| `al-ds-grid__col-7` | Start at column 7 |
| `al-ds-grid__col-8` | Start at column 8 |
| `al-ds-grid__col-9` | Start at column 9 |
| `al-ds-grid__col-10` | Start at column 10 |
| `al-ds-grid__col-11` | Start at column 11 |
| `al-ds-grid__col-12` | Start at column 12 |

Any value from 1–12 is valid: `al-ds-grid__col-{1..12}`.

### Vertical Grid

| Class | Description |
|---|---|
| `al-ds-vertical-grid--2` | 2-row grid |
| `al-ds-grid__row-1`, `al-ds-grid__row-2` | Place item in specific row |
| `al-ds-grid__row-span--2-2` | Span 2 rows |

### Alignment Helpers

| Class | Description |
|---|---|
| `align-right` | Aligns content to end of grid cell (inline-grid, column flow) |
| `align-bottom` | Aligns items to bottom of container |

### Example: Basic two-column layout

```html
<section class="al-ds-grid--12 container-spacing">
    <div class="al-ds-grid__col-span--4-12">
        <!-- sidebar: 1/3 width -->
    </div>
    <div class="al-ds-grid__col-span--8-12">
        <!-- main content: 2/3 width -->
    </div>
</section>
```

### Example: Centered third with column-start

Use `al-ds-grid__col-{n}` to offset a span to a specific starting column. The example below starts a 4-column (one-third) block at column 5, centering it within the 12-column grid.

```html
<section class="al-ds-grid--12 container-spacing">
  <div class="al-ds-grid__col-5 al-ds-grid__col-span--4-12">
    <!-- 4 columns wide, starting at column 5 → centered -->
  </div>
</section>
```

---

## 2. Spacing

Spacing classes add **margin-bottom** (outer) or **padding** (inner) using the 4px base grid.
If the request asks for a different size, that is not based on the 4px base grid, suggest an available scale to the user first.

### Spacing Scale

| Token | Size | CSS Variable |
|---|---|---|
| `xs` | 4px | `--size-1` |
| `s` | 8px | `--size-2` |
| `m` | 16px | `--size-4` |
| `l` | 24px | `--size-6` |
| `xl` | 40px | `--size-10` |

### Outer Spacing (margin-bottom)

| Class | Effect |
|---|---|
| `spacing-xs` | 4px margin-bottom |
| `spacing-s` | 8px margin-bottom |
| `spacing-m` | 16px margin-bottom |
| `spacing-l` | 24px margin-bottom |
| `spacing-xl` | 40px margin-bottom |

All `spacing-*` classes also set `display: grid; width: 100%`.

### Inner Spacing (padding)

Pattern: `spacing-inner-{side}-{size}`

| Class | Effect |
|---|---|
| `spacing-inner-top-xs` | 4px padding-top |
| `spacing-inner-top-s` | 8px padding-top |
| `spacing-inner-left-m` | 16px padding-left |
| `spacing-inner-right-l` | 24px padding-right |
| `spacing-inner-bottom-xl` | 40px padding-bottom |

Sides: `top`, `bottom`, `left`, `right`. Sizes: `xs`, `s`, `m`, `l`, `xl`.

### Other Layout Utilities

| Class | Effect |
|---|---|
| `no-margin` | Removes margin-bottom (e.g. on input fields) |
| `container-spacing` | Adds 24px padding-top (for main content containers) |
| `flex` | `display: flex; flex-wrap: wrap` |
| `text-align-right` | `text-align: right` |

### Example

```html
<div class="spacing-m">
  <p>Content</p>
</div>
<div class="spacing-inner-top-l spacing-inner-bottom-l">
  <p>Padded content</p>
</div>
```

---

## 3. CSS Custom Properties (Variables)

Use these instead of hardcoded values whenever you need sizing or color in CSS.

### Size Variables

| Variable | Value |
|---|---|
| `--size-1` | 4px |
| `--size-2` | 8px |
| `--size-3` | 12px |
| `--size-4` | 16px |
| `--size-5` | 20px |
| `--size-6` | 24px |
| `--size-8` | 32px |
| `--size-10` | 40px |
| `--size-12` | 48px |
| `--size-16` | 64px |
| `--size-20` | 80px |
| `--size-page` | 1440px |

---

## 4. Icons

Icons use an icon font. Apply the class `al-ds-icon-{name}` to display an icon via the `::before` pseudo-element.

### Usage

```html
<!-- Standalone icon -->
<span class="al-ds-icon-search"></span>

<!-- Icon with color modifier -->
<span class="al-ds-icon-attention icon__error"></span>

<!-- Conditional icon in Angular -->
<span [class.al-ds-icon-download]="!disabled"
      [class.al-ds-icon-file]="disabled"></span>
```

### Icon Color Modifiers

| Class | Color            |
|---|------------------|
| `icon__light` | White            |
| `icon__success` | Success green    |
| `icon__error` | Error red        |
| `icon__attention` | Highlight yellow |

### Common UI Icons

`angle_down`, `angle_up`, `angle_left`, `angle_right`, `angle_left_stop`, `angle_right_stop`,
`arrow_down`, `arrow_up`, `arrow_left`, `arrow_right`, `arrow_down_bold`,
`check`, `checked`, `close`, `close_tag-f`,
`plus`, `minus`, `search`, `filter`, `sort`, `sort_simple_up`,
`pencil`, `trash`, `copy`, `download`, `download_more`, `download_xls`,
`calendar`, `clock`, `info`, `attention`, `warning_large`,
`user`, `logout`, `lock-f`, `unlock`, `menu`, `memo`, `envelope`, `external`,
`file`, `folder`, `globe`, `star`, `star-f`, `start`, `steps`, `task`,
`task_approve`, `task_reject`, `task_return`, `task_returned`,
`asset`, `customer_agreement`, `dot`, `slidein_panel`, `more_options`,
`view_configuration`, `view_grid`, `view_list`, `add_branch`, `add_object`,
`mileage`, `github`

### Extra Sizes

- Extra small: `extra_small-angle_down`, `extra_small-angle_up`, `extra_small-angle_left`, `extra_small-angle_right`
- Large: `large-create_offer`, `large-error`, `large-warning`

### Business/Product Icons

Prefixed with `ALP_` or `ALA_`. See [references/icons.md](references/icons.md) for the full list. Usage:

```html
<span class="al-ds-icon-ALP_0001_Operating_Lease"></span>
```

---

## 5. Typography

Headings (`h1`–`h5`) are automatically styled by the theme — no extra classes needed. The theme uses **Alphabet Slab Pro** for headings and **Alphabet Sans Pro** for body text.

### Text Utility Classes

| Class | Effect |
|---|---|
| `strong` / `<strong>` / `<b>` | Bold (Alphabet Sans Pro Medium) |
| `ellipsis` | Truncate with ellipsis (`text-overflow: ellipsis`) |
| `al-ds-error-text` | Error red text color |
| `light` | White text (on child `*` elements) |
| `sub` / `subheading` | Subheading style |
| `list` | Styled list with bottom padding on `li` |
| `list-none` | Remove list bullets and left padding |

## 6. Breakpoints

| Name | Min-width |
|---|---|
| `breakpoint-s` | 768px |
| `breakpoint-m` | 1024px |
| `breakpoint-l` | 1200px |

CSS variables `--breakpoint-s`, `--breakpoint-m`, `--breakpoint-l` are also available.

The grid system is the primary responsive mechanism — columns collapse to full-width below `breakpoint-s`. For component-level responsive behavior, use the core-components responsive features or, as a last resort, custom media queries with these breakpoint values.

---

## 7. Tree Structure

For hierarchical/tree displays:

```html
<ul class="al-ds-trunk">
    <li>
        Root item
        <ul>
            <li class="al-ds-branch">
                <div class="al-ds-leaf">Child item</div>
            </li>
        </ul>
    </li>
</ul>
```

---

## 8. Transformations

| Class | Effect |
|---|---|
| `rotate-cc-90` | Rotate -90° (counter-clockwise) |

---

## Decision Checklist

Before writing any custom CSS, check:

1. **Layout?** → Use `al-ds-grid--12` with `al-ds-grid__col-span--*` classes; add `al-ds-grid__col-{n}` to start a span at a specific column
2. **Spacing between elements?** → Use `spacing-{xs|s|m|l|xl}` or `spacing-inner-{side}-{size}`
3. **Icon?** → Use `al-ds-icon-{name}`
4. **Text truncation?** → Use `ellipsis`
5. **Bold text?** → Use `<strong>` — do not write `font-weight` in component CSS
6. **Flexbox?** → Use `flex` class
7. **Specific size value?** → Use `var(--size-*)` tokens

**If your CSS contains `color`, `background-color`, `font-size`, `font-weight`, `font-family`, `box-shadow`, `border-radius`, or `opacity` — stop and look for a theme class or variable instead. Custom visual styling breaks theme consistency and dark-mode support.**

---

## Rules

- Do not write custom CSS for colors, backgrounds, typography, shadows, border-radius, or opacity — use theme classes or core-components
- Never use inline styling
- Custom CSS is permitted only for layout properties: `width`, `height`, `position`, `overflow`, `display`, `gap`
- Use `var(--size-*)` tokens instead of hardcoded pixel values in any custom CSS
- Use `spacing-*` classes for margin-bottom, `spacing-inner-*` for padding — do not write `margin` or `padding` in component styles
- Use `al-ds-grid--12` with `al-ds-grid__col-span--*` for page layout instead of custom grid or flexbox CSS
- Use `al-ds-grid__col-{n}` to start a grid item at a specific column; combine with `al-ds-grid__col-span--*` for precise positioning
- Use `<strong>` for bold text — do not write `font-weight` in component CSS
- Use `al-ds-icon-{name}` classes for icons — see [references/icons.md](references/icons.md) for the full list of business/product icons
