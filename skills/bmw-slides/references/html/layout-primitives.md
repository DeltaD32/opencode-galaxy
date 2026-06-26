# Layout Primitives

CSS + HTML patterns available in `base.css`. Delivery build sub-agents read this to build slide fragments.

All layouts assume the base CSS from `template.html` is loaded (reset, variables, `.deck`, `.slide`, `.title-bar`, `.footer`, `.content`, `.banner`, `.takeaway`, `.nav`).

---

## Grid Templates

Nine grid templates are available. Place them inside `.content` as the immediate child.

### `.grid-1col` — Single column, full width

One column spanning the full content width. Use for stacked content, single-card layouts, or simple lists.

```html
<div class="content">
  <div class="grid-1col">
    <div><!-- row 1 --></div>
    <div><!-- row 2 --></div>
  </div>
</div>
```

### `.grid-2col` — Equal two columns

Two equal-width columns (1fr 1fr), 20px gap.

```html
<div class="content">
  <div class="grid-2col">
    <div><!-- left --></div>
    <div><!-- right --></div>
  </div>
</div>
```

### `.grid-2col-wide-right` — Narrow left + wide right

Left column 1fr, right column 1.85fr. Use when the right side has more content (e.g., definition card left + grid right).

```html
<div class="content">
  <div class="grid-2col-wide-right">
    <div><!-- narrow left --></div>
    <div><!-- wide right --></div>
  </div>
</div>
```

### `.grid-2col-wide-left` — Wide left + narrow right

Left column 1.85fr, right column 1fr. Use when the left side has more content (e.g., KV metrics left + insight cards right).

```html
<div class="content">
  <div class="grid-2col-wide-left">
    <div><!-- wide left --></div>
    <div><!-- narrow right --></div>
  </div>
</div>
```

### `.grid-3col` — Equal three columns

Three equal-width columns, 14px gap.

```html
<div class="content">
  <div class="grid-3col">
    <div><!-- col 1 --></div>
    <div><!-- col 2 --></div>
    <div><!-- col 3 --></div>
  </div>
</div>
```

### `.grid-2x2` — 2 columns x 2 rows

Two columns, two rows (1fr 1fr / 1fr 1fr), 14px gap. Place exactly 4 children.

```html
<div class="content">
  <div class="grid-2x2">
    <div><!-- top-left --></div>
    <div><!-- top-right --></div>
    <div><!-- bottom-left --></div>
    <div><!-- bottom-right --></div>
  </div>
</div>
```

### `.grid-3x2` — 3 columns x 2 rows

Three columns, two rows, 14px gap. Place exactly 6 children.

```html
<div class="content">
  <div class="grid-3x2">
    <div><!-- 1 --></div>
    <div><!-- 2 --></div>
    <div><!-- 3 --></div>
    <div><!-- 4 --></div>
    <div><!-- 5 --></div>
    <div><!-- 6 --></div>
  </div>
</div>
```

### `.grid-sidebar-left` — 260px left panel + fluid right

Fixed 260px left sidebar, fluid right column, 20px gap. Use for hero+grid metric layouts, navigation panels.

```html
<div class="content">
  <div class="grid-sidebar-left">
    <div><!-- 260px sidebar --></div>
    <div><!-- fluid main --></div>
  </div>
</div>
```

### `.grid-sidebar-right` — Fluid left + 260px right panel

Fluid left column, fixed 260px right sidebar, 20px gap.

```html
<div class="content">
  <div class="grid-sidebar-right">
    <div><!-- fluid main --></div>
    <div><!-- 260px sidebar --></div>
  </div>
</div>
```

---

## Card Patterns

Reusable card primitives. Place them inside grid cells.

### `.card` — Standard light card

Generic container with light background, border, and rounded corners. Use as a general-purpose wrapper.

```html
<div class="card">
  <h4>Title</h4>
  <p>Body text goes here.</p>
</div>
```

### `.accent-card` — Dark primary card

Dark teal background (`--primary`), white text. Use for headlines, callouts, summary panels.

```html
<div class="accent-card">
  <h3>Headline</h3>
  <p>Supporting text in white.</p>
</div>
```

### `.metric-card` — Centered number + label

Light card with centered large number and label below. Use for KPIs and single metrics.

```html
<div class="metric-card">
  <div class="num">42%</div>
  <div class="label">Deployment Frequency</div>
</div>
```

### `.numbered-card` — Card with circular badge

Card with a circular numbered badge (`.badge`) positioned top-left. Use for pillars, dimensions, numbered lists.

Inner elements: `.badge`, `h4`, `p`, optional `.kicker` (secondary-colored accent line).

```html
<div class="numbered-card">
  <div class="badge">1</div>
  <h4>Pillar Title</h4>
  <p>Description of this pillar or dimension.</p>
  <div class="kicker">Optional accent kicker</div>
</div>
```

### `.quote-card` — Accent card with label, quote, note

Dark primary card with an uppercase `.label` (accent color), an italic `.quote` (border-left accent), and a `.note` box (frosted background). Use for definitions, quotations, key statements.

```html
<div class="quote-card">
  <div class="label">Definition</div>
  <div class="quote">"The quoted or defining text goes here."</div>
  <div class="note">
    <strong>Key point:</strong><br />
    Additional context or litmus test.
  </div>
</div>
```

### `.step-card` — Card with numbered badge

Card with an accent-colored (amber) numbered badge centered vertically. Use for recommendations, process steps, action items.

Inner elements: `.badge`, `h5`, `p`.

```html
<div class="step-card">
  <div class="badge">1</div>
  <h5>Step Title</h5>
  <p>Step description text.</p>
</div>
```

### `.insight-card` — Border-left colored card

Light card with a 4px colored left border. Default border is `--primary` (teal). Use for findings, insights, observations.

Variants:

- Default: teal left border, `strong` in primary color
- `.accent`: amber left border, `strong` in amber
- `.warn`: orange/red left border, `strong` in secondary color

```html
<div class="insight-card">
  <strong>Finding Title</strong>
  Description of the finding.
</div>

<div class="insight-card accent">
  <strong>Amber Insight</strong>
  An important observation.
</div>

<div class="insight-card warn">
  <strong>Warning</strong>
  A critical concern.
</div>
```

### `.comparison-item` — Checkmark/cross item

Item with a pseudo-element prefix: cross (red) by default, checkmark (green) with `.good`. Use for pros/cons, good/bad lists.

```html
<div class="comparison-item">Bad point or con</div>
<div class="comparison-item good">Good point or pro</div>
```

### `.kv-row` — Key-value metric row

Horizontal row with a large number (`.kv-num`) on the left and a label (`.kv-label`) on the right. Rows are separated by bottom borders; the last row has no border.

```html
<div class="kv-row">
  <div class="kv-num">4.2x</div>
  <div class="kv-label">
    <strong>Lead Time</strong>
    Time from commit to production deploy
  </div>
</div>
```

### Dark metric cells (for `.dark-bg` slides)

Use `.m-cell` inside dark-background slides for metric tiles.

**`.m-cell`** — Standard dark metric tile with `.m-num` (large accent number), `.m-label` (white label), optional `.m-ctx` (dim context).

```html
<div class="m-cell">
  <div class="m-num">85<sup>%</sup></div>
  <div class="m-label">Test Coverage</div>
  <div class="m-ctx">Up from 62% in Q1</div>
</div>
```

**`.m-cell.hero`** — Hero metric spanning 2 grid rows (`grid-row: 1 / 3`). Uses gradient background. Inner elements: `.m-hero-eyebrow`, `.m-hero-text` (with `<em>` for big number), `.m-hero-source`.

```html
<div class="m-cell hero">
  <div class="m-hero-eyebrow">KEY METRIC</div>
  <div class="m-hero-text">
    <em>3.2x</em>
    faster deployment frequency
  </div>
  <div class="m-hero-source">Source: DORA 2024 Report</div>
</div>
```

**`.m-cell.timeline`** — Before/after split cell. Two halves (`.m-timeline-before`, `.m-timeline-after`) separated by `.m-timeline-arrow`.

```html
<div class="m-cell timeline">
  <div class="m-timeline-before">
    <div class="m-num">2wk</div>
    <div class="m-label">Before</div>
  </div>
  <div class="m-timeline-arrow">
    <svg width="18" height="18" viewBox="0 0 18 18">
      <path
        d="M2 9h12M10 5l4 4-4 4"
        stroke="#FBAE40"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
        fill="none"
      />
    </svg>
  </div>
  <div class="m-timeline-after">
    <div class="m-num" style="color:var(--accent);">2d</div>
    <div class="m-label">After</div>
  </div>
</div>
```

---

## Decorators

### `.dark-bg` — Dark slide background

Apply to the `.slide` element. All title-bar, footer, and text colors adjust automatically via CSS descendants -- no overrides needed.

```html
<div class="slide dark-bg" id="slide-N">
  <!-- title-bar, content, footer all auto-adjust -->
</div>
```

### `.center` — Center content

Centers content vertically and horizontally with centered text. Apply to `.content` or any container.

```html
<div class="content center">
  <h3>Centered Title</h3>
  <p>Centered body text.</p>
</div>
```

### `.highlight` — Emphasis card

Applies accent background (`#EEF5F8`) and accent border. Add to any `.card` or item element to draw attention.

```html
<div class="card highlight">
  <h5>Highlighted item</h5>
  <p>This card stands out from the rest.</p>
</div>
```

### `.divider` — Horizontal rule

Thin 1px horizontal line with 8px vertical margin. Use between stacked sections.

```html
<div class="divider"></div>
```

### `.col-header` — Column header

Uppercase, bold, letterspaced header for comparison columns. Variants:

- `.col-header.muted` — gray text, gray border (for "before" or neutral columns)
- `.col-header.accent` — primary color text, accent border (for "after" or positive columns)
- `.col-header.bad` — red background, red text, rounded top corners (for negative/bad columns)
- `.col-header.good` — green background, green text, rounded top corners (for positive/good columns)

```html
<div class="col-header muted">BEFORE</div>
<div class="col-header accent">AFTER</div>
<div class="col-header bad">Challenges</div>
<div class="col-header good">Improvements</div>
```

### `.vs-badge` — VS badge

36px circular amber badge for the center of comparison columns. Typically placed between two columns.

```html
<div class="vs-badge">VS</div>
```

### `.arrow-connector` — Vertical arrow between columns

Vertical connector with lines above and below an arrow icon. Use as the center column in before/after layouts.

```html
<div class="arrow-connector">
  <div class="line"></div>
  <div class="icon">&rarr;</div>
  <div class="line"></div>
</div>
```

---

## Composition Recipes

Common slide types composed from primitives. Each recipe shows the complete HTML for a slide fragment.

### Definition Slide

Grid: `grid-2col-wide-right`. Left: `quote-card`. Right: `grid-2x2` with 4 x `numbered-card`.

```html
<div class="slide" id="slide-N">
  <div class="title-bar">
    <h2>{title}</h2>
    <span class="slide-num">N / {total}</span>
  </div>
  <div class="content">
    <div class="grid-2col-wide-right">
      <div class="quote-card reveal">
        <div class="label">{label, e.g. "Definition"}</div>
        <div class="quote">"{defining text}"</div>
        <div class="note">
          <strong>{highlight label}:</strong><br />
          {supporting text or litmus test}
        </div>
      </div>

      <div class="grid-2x2">
        <div class="numbered-card reveal">
          <div class="badge">1</div>
          <h4>{heading}</h4>
          <p>{body}</p>
        </div>
        <div class="numbered-card reveal">
          <div class="badge">2</div>
          <h4>{heading}</h4>
          <p>{body}</p>
        </div>
        <div class="numbered-card reveal">
          <div class="badge">3</div>
          <h4>{heading}</h4>
          <p>{body}</p>
        </div>
        <div class="numbered-card reveal">
          <div class="badge">4</div>
          <h4>{heading}</h4>
          <p>{body}</p>
        </div>
      </div>
    </div>
  </div>
  <div class="footer">
    <span>{footer}</span>
    <span class="conf">{confidentiality}</span>
  </div>
</div>
```

### Metrics Dashboard

Slide class: `slide dark-bg`. Uses the legacy `.metrics-inner` class (still available in base.css) for the 4-column + 2-row grid with a hero cell spanning 2 rows on the left.

Grid: `metrics-inner` = `260px repeat(3, 1fr)` columns, `1fr 1fr` rows. Alternatively, use inline grid styles on a plain `div`.

```html
<div class="slide dark-bg" id="slide-N">
  <div class="title-bar">
    <h2>{title}</h2>
    <span class="slide-num">N / {total}</span>
  </div>
  <div class="content">
    <div class="metrics-inner">
      <!-- Hero cell (spans 2 rows) -->
      <div class="m-cell hero reveal-scale">
        <div class="m-hero-eyebrow">{eyebrow}</div>
        <div class="m-hero-text">
          <em>{big number}</em>
          {description}
        </div>
        <div class="m-hero-source">{source attribution}</div>
      </div>

      <!-- Row 1: 3 metric cells -->
      <div class="m-cell reveal">
        <div class="m-num">{number}<sup>{unit}</sup></div>
        <div class="m-label">{label}</div>
        <div class="m-ctx">{context}</div>
      </div>
      <div class="m-cell reveal">
        <div class="m-num">{number}<sup>{unit}</sup></div>
        <div class="m-label">{label}</div>
      </div>
      <div class="m-cell reveal">
        <div class="m-num">{number}<sup>{unit}</sup></div>
        <div class="m-label">{label}</div>
      </div>

      <!-- Row 2: timeline cell + 2 regular cells -->
      <div class="m-cell timeline reveal">
        <div class="m-timeline-before">
          <div class="m-num">{before}</div>
          <div class="m-label">{before label}</div>
        </div>
        <div class="m-timeline-arrow">
          <svg width="18" height="18" viewBox="0 0 18 18">
            <path
              d="M2 9h12M10 5l4 4-4 4"
              stroke="#FBAE40"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
              fill="none"
            />
          </svg>
        </div>
        <div class="m-timeline-after">
          <div class="m-num" style="color:var(--accent);">{after}</div>
          <div class="m-label">{after label}</div>
        </div>
      </div>
      <div class="m-cell reveal">
        <div class="m-num">{number}</div>
        <div class="m-label">{label}</div>
      </div>
      <div class="m-cell reveal">
        <div class="m-num">{number}</div>
        <div class="m-label">{label}</div>
      </div>
    </div>
  </div>
  <div class="footer">
    <span>{footer}</span>
    <span class="conf">{confidentiality}</span>
  </div>
</div>
```

**Notes:**

- The `.metrics-inner` class is defined in base.css (legacy section) and provides the correct grid.
- If you need a different column count, use inline styles: `style="display:grid; grid-template-columns: 260px repeat(2, 1fr); grid-template-rows: 1fr 1fr; gap: 12px; height: 100%; padding: 14px;"`.
- Hero cell always spans 2 rows via `grid-row: 1 / 3` (built into `.m-cell.hero`).
- Timeline cell is optional -- use regular `.m-cell` if no before/after is needed.

### Pillars

Grid: `grid-3x2`. 6 x `numbered-card`.

```html
<div class="slide" id="slide-N">
  <div class="title-bar">
    <h2>{title}</h2>
    <span class="slide-num">N / {total}</span>
  </div>
  <div class="content">
    <div class="grid-3x2">
      <div class="numbered-card reveal">
        <div class="badge">1</div>
        <h4>{heading}</h4>
        <p>{body}</p>
        <div class="kicker">{optional kicker}</div>
      </div>
      <div class="numbered-card reveal">
        <div class="badge">2</div>
        <h4>{heading}</h4>
        <p>{body}</p>
      </div>
      <div class="numbered-card reveal">
        <div class="badge">3</div>
        <h4>{heading}</h4>
        <p>{body}</p>
      </div>
      <div class="numbered-card reveal">
        <div class="badge">4</div>
        <h4>{heading}</h4>
        <p>{body}</p>
      </div>
      <div class="numbered-card reveal">
        <div class="badge">5</div>
        <h4>{heading}</h4>
        <p>{body}</p>
      </div>
      <div class="numbered-card reveal">
        <div class="badge">6</div>
        <h4>{heading}</h4>
        <p>{body}</p>
      </div>
    </div>
  </div>
  <div class="footer">
    <span>{footer}</span>
    <span class="conf">{confidentiality}</span>
  </div>
</div>
```

### Before / After

Uses a 3-column inline grid (`1fr 60px 1fr`) with an arrow connector in the center. Left column has `.col-header.muted` + card items. Right column has `.col-header.accent` + card items (some with `.highlight`).

```html
<div class="slide" id="slide-N">
  <div class="title-bar">
    <h2>{title}</h2>
    <span class="slide-num">N / {total}</span>
  </div>
  <div class="content">
    <div
      style="display:grid; grid-template-columns: 1fr 60px 1fr; gap: 0; flex: 1; align-items: stretch;"
    >
      <!-- Before column -->
      <div style="display:flex; flex-direction:column; gap:10px;">
        <div class="col-header muted">{left header, e.g. "BEFORE"}</div>
        <div class="card reveal">
          <h5
            style="font-size:16px; font-weight:700; color:#888; margin-bottom:3px;"
          >
            {item title}
          </h5>
          <p style="font-size:15px; color:#666; line-height:1.4;">
            {item description}
          </p>
        </div>
        <div class="card reveal">
          <h5
            style="font-size:16px; font-weight:700; color:#888; margin-bottom:3px;"
          >
            {item title}
          </h5>
          <p style="font-size:15px; color:#666; line-height:1.4;">
            {item description}
          </p>
        </div>
        <!-- more items as needed -->
      </div>

      <!-- Arrow connector -->
      <div class="arrow-connector">
        <div class="line"></div>
        <div class="icon">&rarr;</div>
        <div class="line"></div>
      </div>

      <!-- After column -->
      <div style="display:flex; flex-direction:column; gap:10px;">
        <div class="col-header accent">{right header, e.g. "AFTER"}</div>
        <div class="card highlight reveal">
          <h5
            style="font-size:16px; font-weight:700; color:var(--primary); margin-bottom:3px;"
          >
            {item title}
          </h5>
          <p style="font-size:15px; color:#666; line-height:1.4;">
            {item description}
          </p>
        </div>
        <div class="card reveal">
          <h5
            style="font-size:16px; font-weight:700; color:var(--primary); margin-bottom:3px;"
          >
            {item title}
          </h5>
          <p style="font-size:15px; color:#666; line-height:1.4;">
            {item description}
          </p>
        </div>
        <!-- more items as needed -->
      </div>
    </div>
  </div>
  <div class="footer">
    <span>{footer}</span>
    <span class="conf">{confidentiality}</span>
  </div>
</div>
```

### Versus / Good vs Bad

Uses a 3-column inline grid (`1fr 48px 1fr`) with a VS badge in the center. Left column: `.col-header.bad` + `.comparison-item` items. Right column: `.col-header.good` + `.comparison-item.good` items.

```html
<div class="slide" id="slide-N">
  <div class="title-bar">
    <h2>{title}</h2>
    <span class="slide-num">N / {total}</span>
  </div>
  <div class="content">
    <div
      style="display:grid; grid-template-columns: 1fr 48px 1fr; gap: 0; align-items: start; flex: 1;"
    >
      <!-- Bad column -->
      <div style="display:flex; flex-direction:column; gap:9px; padding:4px 0;">
        <div class="col-header bad">{bad header}</div>
        <div class="comparison-item reveal">{point 1}</div>
        <div class="comparison-item reveal">{point 2}</div>
        <div class="comparison-item reveal">{point 3}</div>
      </div>

      <!-- VS divider -->
      <div
        style="display:flex; align-items:center; justify-content:center; align-self:stretch;"
      >
        <div class="vs-badge">VS</div>
      </div>

      <!-- Good column -->
      <div style="display:flex; flex-direction:column; gap:9px; padding:4px 0;">
        <div class="col-header good">{good header}</div>
        <div class="comparison-item good reveal">{point 1}</div>
        <div class="comparison-item good reveal">{point 2}</div>
        <div class="comparison-item good reveal">{point 3}</div>
      </div>
    </div>
  </div>
  <div class="footer">
    <span>{footer}</span>
    <span class="conf">{confidentiality}</span>
  </div>
</div>
```

### Key Findings

Grid: `grid-2col-wide-left`. Left: stack of `.kv-row` elements. Right: stack of `.insight-card` (variants: default, `.accent`, `.warn`).

```html
<div class="slide" id="slide-N">
  <div class="title-bar">
    <h2>{title}</h2>
    <span class="slide-num">N / {total}</span>
  </div>
  <div class="content">
    <div class="grid-2col-wide-left">
      <div style="display:flex; flex-direction:column; gap:0;">
        <div class="kv-row reveal">
          <div class="kv-num">{value}</div>
          <div class="kv-label"><strong>{headline}</strong>{detail}</div>
        </div>
        <div class="kv-row reveal">
          <div class="kv-num">{value}</div>
          <div class="kv-label"><strong>{headline}</strong>{detail}</div>
        </div>
        <div class="kv-row reveal">
          <div class="kv-num">{value}</div>
          <div class="kv-label"><strong>{headline}</strong>{detail}</div>
        </div>
      </div>

      <div style="display:flex; flex-direction:column; gap:10px;">
        <div class="insight-card reveal">
          <strong>{insight title}</strong>
          {insight body}
        </div>
        <div class="insight-card accent reveal">
          <strong>{insight title}</strong>
          {insight body}
        </div>
        <div class="insight-card warn reveal">
          <strong>{insight title}</strong>
          {insight body}
        </div>
      </div>
    </div>
  </div>
  <div class="footer">
    <span>{footer}</span>
    <span class="conf">{confidentiality}</span>
  </div>
</div>
```

### Recommendations

Grid: `grid-2col-wide-right`. Left: `accent-card` or `quote-card` with headline. Right: stack of `step-card`.

```html
<div class="slide" id="slide-N">
  <div class="title-bar">
    <h2>{title}</h2>
    <span class="slide-num">N / {total}</span>
  </div>
  <div class="content">
    <div class="grid-2col-wide-right">
      <div
        class="accent-card reveal"
        style="display:flex; flex-direction:column; justify-content:center;"
      >
        <div
          style="font-size:14px; font-weight:700; text-transform:uppercase; letter-spacing:2px; color:var(--accent); margin-bottom:14px;"
        >
          {eyebrow}
        </div>
        <h3
          style="font-size:28px; font-weight:700; line-height:1.3; margin-bottom:14px;"
        >
          {headline}
        </h3>
        <p
          style="font-size:16px; color:rgba(255,255,255,0.75); line-height:1.5;"
        >
          {supporting text}
        </p>
      </div>

      <div style="display:flex; flex-direction:column; gap:10px;">
        <div class="step-card reveal">
          <div class="badge">1</div>
          <h5>{step title}</h5>
          <p>{step description}</p>
        </div>
        <div class="step-card reveal">
          <div class="badge">2</div>
          <h5>{step title}</h5>
          <p>{step description}</p>
        </div>
        <div class="step-card reveal">
          <div class="badge">3</div>
          <h5>{step title}</h5>
          <p>{step description}</p>
        </div>
        <div class="step-card reveal">
          <div class="badge">4</div>
          <h5>{step title}</h5>
          <p>{step description}</p>
        </div>
      </div>
    </div>
  </div>
  <div class="footer">
    <span>{footer}</span>
    <span class="conf">{confidentiality}</span>
  </div>
</div>
```

### Simple Centered Text

No grid needed. `.content.center` with heading and paragraph.

```html
<div class="slide" id="slide-N">
  <div class="title-bar">
    <h2>{title}</h2>
    <span class="slide-num">N / {total}</span>
  </div>
  <div class="content center">
    <h3
      style="font-size:28px; font-weight:700; color:var(--primary); max-width:800px; line-height:1.4;"
    >
      {main statement}
    </h3>
    <p
      style="font-size:16px; color:#666; max-width:600px; line-height:1.6; margin-top:16px;"
    >
      {supporting text}
    </p>
  </div>
  <div class="footer">
    <span>{footer}</span>
    <span class="conf">{confidentiality}</span>
  </div>
</div>
```

---

## CI Elements

Title bar, footer, banner, takeaway -- these are structural CI elements present on every content slide. Refer to base.css for the full styles.

Every content slide should follow this skeleton:

```html
<div class="slide" id="slide-N">
  <div class="title-bar">
    <h2>{title}</h2>
    <span class="slide-num">N / {total}</span>
  </div>
  <div class="content">
    <!-- grid template + card patterns here -->
  </div>
  <!-- Optional: <div class="takeaway">{key takeaway text}</div> -->
  <!-- Optional: <div class="banner">{banner text}</div> -->
  <div class="footer">
    <span>{footer}</span>
    <span class="conf">{confidentiality}</span>
  </div>
</div>
```

**Notes:**

- `.title-bar` is 68px tall, primary-colored h2 with accent underline, slide number right-aligned.
- `.footer` is 34px tall, gray text with confidentiality label.
- `.banner` is a full-width primary-background bar with white bold text. Use for strong closing statements.
- `.takeaway` is a bordered box with primary-colored text. Use for slide-level key takeaways.
- Banner and takeaway are mutually exclusive -- use one or the other, not both.
- `{footer}` and `{confidentiality}` are literal placeholders replaced by the assemble script from `config.yaml`.

---

## Cover Components

These are CI-mandated components and are NOT composed from primitives. Use them exactly as documented.

### Cover -- BMW Corporate (`cover-bmw`)

**This is the default cover type.** Faithfully reproduces the BMW Group PowerPoint template:

- BMW Group logo top-left, brand logos (BMW + MINI) top-right
- Full-bleed background image (from `./assets/covers/` or the deck's `assets/` directory)
- Dark overlay so text stays readable
- Title block bottom-left: main title (large, all-caps), subtitle below a thin divider line
- Dept. badge bottom-right (teal diagonal slash + label, like "CB-11")
- Footer bar at the very bottom: left = Department | Date | Author, center = CONFIDENTIAL

**For the outro slide** (last slide of type `cover-bmw`): background image (same path as slide 1) + dark overlay + one closing statement (right half, slightly above center). No header, logos, title block, dept badge, footer, or banner.

#### CSS (in base.css -- no overrides needed)

```css
/* ── BMW Corporate Cover ── */
.cover-bmw {
  /* Do NOT set position:relative — .slide already has position:absolute + inset:0
     which sizes this element to fill .deck. Changing to relative would collapse
     height to zero (all children are absolutely-positioned, so no flow content). */
  overflow: hidden;
  background: #02324a;
}

/* Full-bleed background image */
.cover-bmw-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  background-size: cover;
  background-position: center top;
  background-repeat: no-repeat;
}

/* Dark overlay — heavier at bottom for text legibility */
.cover-bmw-overlay {
  position: absolute;
  inset: 0;
  z-index: 1;
  background: linear-gradient(
    180deg,
    rgba(2, 20, 30, 0.25) 0%,
    rgba(2, 20, 30, 0.4) 40%,
    rgba(2, 20, 30, 0.8) 100%
  );
}

/* Header bar — logos, top of slide */
.cover-bmw-header {
  position: absolute;
  z-index: 2;
  top: 0;
  left: 0;
  right: 0;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 36px;
}
.cover-bmw-logo-left img {
  height: 52px;
  width: auto;
  display: block;
}
.cover-bmw-logo-right {
  display: flex;
  align-items: center;
  gap: 4px;
}
.cover-bmw-logo-right img {
  height: 40px;
  width: auto;
  display: block;
}

/* Body — title block + dept badge, positioned in the lower portion */
.cover-bmw-body {
  position: absolute;
  z-index: 2;
  left: 0;
  right: 0;
  bottom: 34px; /* above the footer */
  padding: 0;
}

/* Title block: horizontal rule on top, title, divider, subtitle */
.cover-bmw-title-block {
  padding: 16px 44px 0 44px;
  border-top: 1px solid rgba(255, 255, 255, 0.3);
}
.cover-bmw-title {
  font-size: 46px;
  font-weight: 700;
  color: #ffffff;
  line-height: 1.08;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.cover-bmw-sub-divider {
  width: 100%;
  height: 1px;
  background: rgba(255, 255, 255, 0.3);
  margin: 12px 0;
}
.cover-bmw-subtitle {
  font-size: 14px;
  font-weight: 700;
  color: #ffffff;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  margin-bottom: 6px;
}

/* Department badge — teal parallelogram, right-aligned */
.cover-bmw-dept {
  float: right;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--primary);
  color: #ffffff;
  font-size: 22px;
  font-weight: 700;
  min-width: 234px;
  padding: 12px 40px 12px 56px;
  clip-path: polygon(20px 0%, 100% 0%, 100% 100%, 0% 100%);
  letter-spacing: 0.5px;
  margin-top: 4px;
}

/* Footer bar — absolute bottom */
.cover-bmw-footer {
  position: absolute;
  z-index: 2;
  left: 0;
  right: 0;
  bottom: 0;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 44px;
  border-top: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(2, 20, 30, 0.55);
}
.cover-bmw-footer span {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
}
.cover-bmw-footer .conf {
  font-weight: 600;
  color: #e05252;
  text-transform: uppercase;
  letter-spacing: 1px;
  font-size: 10px;
}
```

#### HTML

The background image is set via `style` on `.cover-bmw-bg`. Use a local asset from the deck's `assets/` directory, or the shared `assets/` folder at the project root.

**Default image** (when no specific cover image is provided): `../../assets/cover_default.jpg` (relative from slide fragment in `slides/`).

```html
<!-- SLIDE 1 — BMW CORPORATE COVER -->
<div class="slide cover-bmw active" id="slide-1">
  <!-- Background image -->
  <div
    class="cover-bmw-bg"
    style="background-image:url('../../assets/cover_default.jpg');"
  ></div>
  <div class="cover-bmw-overlay"></div>

  <!-- Header: logos -->
  <div class="cover-bmw-header">
    <div class="cover-bmw-logo-left">
      <img src="../../assets/bmw_group.png" alt="BMW Group" />
    </div>
    <div class="cover-bmw-logo-right">
      <img src="../../assets/bmw_mini.png" alt="BMW and MINI" />
    </div>
  </div>

  <!-- Body: title block bottom-left, dept badge bottom-right -->
  <div class="cover-bmw-body">
    <div class="cover-bmw-title-block">
      <div class="cover-bmw-title">
        {PRESENTATION TITLE,<br />TWO LINES MAXIMUM.}
      </div>
      <div class="cover-bmw-sub-divider"></div>
      <div class="cover-bmw-subtitle">{SUBTITLE, TWO LINES MAXIMUM.}</div>
    </div>
    <div class="cover-bmw-dept">{department}</div>
  </div>

  <!-- Footer -->
  <div class="cover-bmw-footer">
    <span>{footer}</span>
    <span class="conf">{confidentiality}</span>
  </div>
</div>
```

**Notes:**

- `cover-bmw` replaces `cover` as the default cover component. Always use `cover-bmw` for BMW presentations.
- Slide 1 gets `active` class.
- The `.cover-bmw-bg` background-image path must be relative to the slide fragment's location (`slides/slide-N.html`). Use `../../assets/cover_default.jpg` for shared project assets. The assemble script normalizes paths automatically.
- Logo paths: `../../assets/bmw_group.png` and `../../assets/bmw_mini.png` -- these live in the shared project `assets/` two levels above the deck dir. **Always use `../../assets/` for the shared logos.** If the logo files do not exist, omit the `<img>` tags entirely — use empty `<div>` placeholders instead so the header layout is preserved but no broken images appear.
- The `.cover-bmw-dept` badge text = `{department}` placeholder, replaced by the assemble script from `config.yaml`.
- `{footer}` and `{confidentiality}` are literal placeholders replaced by the assemble script.
- **Outro slide** (last slide, type `cover-bmw`): background image + overlay + `.outro-statement` div (right half, top 35%, width 44%, white bold uppercase text). No header, logos, title block, dept badge, footer, or banner. Requires CSS override in `overrides.css`.

### Cover -- Simple Gradient (`cover`)

Legacy centered cover without background image. Use only when no image is available.

#### CSS

```css
.cover {
  background: linear-gradient(155deg, #035970 0%, #02324a 45%, #05141e 100%);
  justify-content: center;
}
.cover-inner {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 50px 100px 20px;
  text-align: center;
}
.cover-eyebrow {
  font-size: 12px;
  font-weight: 700;
  color: var(--accent);
  letter-spacing: 3.5px;
  text-transform: uppercase;
  margin-bottom: 22px;
}
.cover-title {
  font-size: 58px;
  font-weight: 700;
  color: var(--white);
  line-height: 1.05;
  letter-spacing: -1.5px;
  margin-bottom: 10px;
}
.cover-title em {
  font-style: normal;
  color: var(--accent);
}
.cover-divider {
  width: 56px;
  height: 3px;
  background: var(--accent);
  margin: 18px auto;
  border-radius: 2px;
}
.cover-sub {
  font-size: 20px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.72);
  max-width: 720px;
  line-height: 1.5;
}
.cover-footer {
  flex-shrink: 0;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 44px;
  border-top: 1px solid rgba(255, 255, 255, 0.12);
}
.cover-footer span {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
}
.cover-footer .conf {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.35);
  text-transform: uppercase;
  letter-spacing: 1px;
  font-size: 10px;
}
```

#### HTML

```html
<div class="slide cover active" id="slide-1">
  <div class="cover-inner">
    <div class="cover-eyebrow">{eyebrow}</div>
    <div class="cover-title"><em>{highlighted}</em> {rest of title}</div>
    <div class="cover-divider"></div>
    <div class="cover-sub">{subtitle}</div>
  </div>
  <div class="cover-footer">
    <span>{footer}</span>
    <span class="conf">{confidentiality}</span>
  </div>
</div>
```

**Notes:**

- Wrap the emphasized word in `<em>` to render it in accent color.
- First slide always gets the `active` class.
- Cover uses `.cover-footer` instead of `.footer` (different styling for dark background).
- No `<title-bar>` on cover slides.

---

## Content Density Rules

- **Title slides**: max 2 lines for title, max 2 lines for subtitle.
- **Content slides**: 4-6 bullets max, or 2 short paragraphs.
- **Feature grids**: max 6 cards (3x2 or 2x2+2).
- **Code slides**: 8-10 lines max.
- **Metric tiles**: max 6 tiles + 1 hero.
- **If content exceeds limits**: split across multiple slides.

---

## Animation Usage

All animation classes are opt-in. Add them to content elements to animate them in when the slide becomes active.

- **`.reveal`** -- Fade up (opacity 0 to 1, translateY 30px to 0). Best for: most content elements, cards, text blocks.
- **`.reveal-scale`** -- Scale in (opacity 0 to 1, scale 0.9 to 1). Best for: cards, images, metric numbers.
- **`.reveal-blur`** -- Blur in (opacity 0 to 1, blur 10px to 0). Best for: hero numbers, large titles.
- **Stagger**: Children with reveal classes get automatic staggered delays (nth-child 1 = 0.1s, 2 = 0.2s, ..., 6 = 0.6s). Place `.reveal` on the direct children of the grid, not on the grid itself.
- **Respects `prefers-reduced-motion`**: All animations are disabled when the user prefers reduced motion.
- **Where NOT to use**: cover slides (they have their own layout), structural wrappers (grids, content div).

Example:

```html
<div class="grid-3x2">
  <div class="numbered-card reveal"><!-- appears at 0.1s --></div>
  <div class="numbered-card reveal"><!-- appears at 0.2s --></div>
  <div class="numbered-card reveal"><!-- appears at 0.3s --></div>
  <div class="numbered-card reveal"><!-- appears at 0.4s --></div>
  <div class="numbered-card reveal"><!-- appears at 0.5s --></div>
  <div class="numbered-card reveal"><!-- appears at 0.6s --></div>
</div>
```
