# Design Principles

Guidelines for Phase 1 (Storyline). Goal: transform raw content into visually strong management slides.

**If PPTX mode:** Slides are built with python-pptx shapes and placeholders.
**If HTML mode:** Slides are rendered as HTML/CSS.

## Core Rules

1. **One message per slide.** Never pack three topics onto one slide. Add another slide instead.
2. **Less text, more impact.** Details belong in Speaker Notes, not on the slide.
3. **Visualize numbers, don't list them.** One large number with context beats any table.
4. **Management wants to make decisions.** Every slide answers: "What does this mean for us?" or "What do we need to do?"
5. **Creative body, fixed canvas.** Title, footer, department badge, logo, colors, and fonts are set by the BMW template — do not touch them. Everything below the title is a canvas for composition: use helpers, raw shapes, or both. The best decks are unmistakably BMW at the edges and unmistakably crafted in the body.
6. **Vary across slides.** A strong deck alternates character: a hero-number slide, then a structure slide, then a pull-quote, then a timeline — not ten variations of the same card grid. If two neighbouring slides use the same pattern, change one. Cookie-cutter is the failure mode, not the goal.

## Transformation: From Content to Visualization

When the markdown input contains one of these patterns, transform it into a visual.

### PPTX Transformation Table

**Variation rule — no repetition within a 3-slide window.** Never use the same visualization function (e.g. `add_mece_tiles`) on two slides that are within 3 positions of each other. When the table below lists multiple options for a pattern, pick the one that **differs most from the adjacent slides**. If the first option was already used nearby, you MUST choose a different one. Treat every option in the table as equally valid — they are listed in no particular priority order.

| Input Pattern                     | Instead of                      | Options (pick one — vary across slides)                                                                        | Visual Character    |
| --------------------------------- | ------------------------------- | -------------------------------------------------------------------------------------------------------------- | ------------------- |
| A single important number         | Bullet with number              | `add_hero_number`, `add_progress_ring` (if percentage), `add_pull_quote` (if the number tells a story)         | bold / data-forward |
| Before/After or Plan/Actual       | Two bullets                     | Two large numbers side by side with arrow or trend indicator, `add_pillars` (2 columns), `add_key_value_pairs` | comparison-forward  |
| 3–4 equal-weight points           | Bullet list                     | `add_mece_tiles`, `add_pillars`, `add_hexagon_grid`, `add_numbered_badge_list`                                 | structure-forward   |
| Timeline / chronological sequence | Numbered list                   | `add_timeline`, `add_chevron_chain`, `add_numbered_badge_list`, `add_zigzag_blocks`                            | flow-forward        |
| Percentages / shares              | "45% this, 30% that"            | Horizontal bars or circle segments, `add_progress_ring` (1–3 values), `add_pillars` (with bar shapes)          | data-forward        |
| Comparison of two options         | Prose text                      | Two columns with pro/con, `add_comparison_table`, `add_pillars` (2 columns)                                    | comparison-forward  |
| Ranking / Top N                   | Numbered list                   | Staggered bars or descending large numbers, `add_numbered_badge_list`, `add_key_value_pairs`                   | data-forward        |
| Recommendation / decision         | Bullet list of arguments        | `add_pyramid_slide_content`, `add_sidebar_layout`, `add_mece_tiles`                                            | narrative-forward   |
| MECE framework / pillars          | Nested bullets                  | `add_mece_tiles`, `add_pillars`, `add_tabbed_headers`, `add_hexagon_grid`                                      | structure-forward   |
| Multi-option decision             | Prose                           | `add_comparison_table`, `add_pillars` (one per option), `add_mece_tiles`                                       | comparison-forward  |
| Project / workstream status       | Bullet status list              | `add_rag_dashboard`, `add_key_value_pairs`, `add_styled_table`                                                 | data-forward        |
| Multi-workstream roadmap          | Gantt in text                   | `add_swimlane_timeline`, `add_timeline` (if single lane), `add_chevron_chain`                                  | flow-forward        |
| Powerful quote / customer voice   | Prose paragraph                 | `add_pull_quote`, `add_hero_number` (if quote is a single impactful line)                                      | narrative-forward   |
| KPI completion / sprint progress  | Number + "%"                    | `add_progress_ring`, `add_hero_number` (single KPI), horizontal bar shapes                                     | data-forward        |
| Capability map / tech stack       | Bullet list of items            | `add_hexagon_grid`, `add_mece_tiles`, `add_pillars`                                                            | structure-forward   |
| Overlap / synergy / trade-off     | Separate bullet groups          | `add_venn`, `add_pillars` (with shared base), `add_mece_tiles`                                                 | structure-forward   |
| Sales pipeline / conversion       | Table of numbers                | `add_funnel`, `add_chevron_chain` (horizontal flow), stacked bars                                              | flow-forward        |
| Annotated screenshot / image      | Text describing what to look at | `add_callout`, text overlay with `add_text_shadow_box`                                                         | narrative-forward   |
| Sequential steps / process text   | Numbered bullets                | `add_numbered_badge_list`, `add_chevron_chain`, `add_zigzag_blocks`, `add_arrow_bar_steps`                     | flow-forward        |
| Factual data / project specs      | Dense paragraph                 | `add_key_value_pairs`, `add_styled_table`, `add_sidebar_layout`                                                | data-forward        |
| Multi-category overview           | Full-width text                 | `add_sidebar_layout`, `add_tabbed_headers`, `add_mece_tiles`                                                   | structure-forward   |
| Multi-section deep-dive           | Long text under headings        | `add_tabbed_headers`, `add_zigzag_blocks`, `add_sidebar_layout`                                                | narrative-forward   |
| Narrative arc / story flow        | Stacked paragraphs              | `add_zigzag_blocks`, `add_numbered_badge_list`, `add_chevron_chain`                                            | flow-forward        |

**Visual Character** helps you plan variety at the deck level (see Phase 1 → Deck Composition Brief). Avoid placing two slides with the same Visual Character next to each other when possible.

### HTML Transformation Table

Map content patterns to grid templates and card primitives from `layout-primitives.md`.

| Input Pattern                    | Grid Template         | Card Types                                   | Modifier  |
| -------------------------------- | --------------------- | -------------------------------------------- | --------- |
| Single important number          | `sidebar-left`        | hero `.m-cell` + `.m-cell` tiles             | `dark-bg` |
| Number comparison (before/after) | `2col` + center arrow | `.m-cell.timeline` or comparison-items       | `dark-bg` |
| 3–6 equal-weight points          | `3x2` or `2x2`        | `.numbered-card`                             |           |
| Two approaches compared          | `2col` + VS badge     | `.comparison-item` + `.col-header.good/.bad` |           |
| Definition + dimensions          | `2col-wide-right`     | `.quote-card` + `.numbered-card`             |           |
| Key findings + insights          | `2col-wide-left`      | `.kv-row` + `.insight-card`                  |           |
| Recommendations / steps          | `2col-wide-right`     | `.accent-card` + `.step-card`                |           |
| Timeline / sequence              | `1col` or `3col`      | `.step-card`                                 |           |
| Simple statement                 | `1col` + `.center`    | plain `<h3>` + `<p>`                         |           |

## Free Composition Principles

**If PPTX mode:** When building slides with Layout 12 or 2 (free area, no content placeholders), the sub-agent creates all shapes from code.
**If HTML mode:** When using `[content, custom]` slides, the CSS is composed freely beyond the standard grid templates.

The following principles guide the composition — they are not rigid rules but design thinking tools.

### Composition Patterns

**Asymmetric split:**
**If PPTX mode:** Divide the free area into two unequal zones (e.g. 55/45 or 60/40). Each zone carries a different content type — stacked cards on one side, bullet groups on the other. A visual connector (chevron, arrow, divider line) in the gap signals the relationship. This is the most versatile pattern for content that has two related but distinct parts.
**If HTML mode:** Divide the content area into two unequal zones (e.g., `grid-template-columns: 1fr 1.85fr`). Each zone carries a different content type — accent card on one side, grid of cards on the other.

**Stacked cards with breathing room:**
**If PPTX mode:** Multiple related messages as vertically stacked cards on one side. Cards have a light background fill (`COLOR_LIGHT` or white with subtle border), consistent width, and equal vertical gaps. The remaining space holds supporting content or stays empty (white space is fine).
**If HTML mode:** Multiple related messages as vertically stacked cards. Cards have light background (`var(--card-bg)`), subtle border, consistent width, and equal gaps. Use `display: flex; flex-direction: column; gap: 10px;`.

**Hub and spokes:** A central element (hero number, key message, icon) with supporting elements arranged around it — works for content that has one dominant point with supporting details.

**Grid with variation:**
**If PPTX mode:** Tiles/cards in a grid, but not all the same size. One card can span two rows or be wider to signal importance. Avoid perfectly uniform grids — they feel like a table, not a design.
**If HTML mode:** Cards in a CSS grid, but not all the same size. One card can span two rows (`grid-row: 1 / 3`) to signal importance. Avoid perfectly uniform grids.

### Principles (not rules)

1. **Hierarchy through size.** The most important element is the largest. Not everything deserves equal space.
2. **Group by proximity.** Related items are close together. Unrelated items have clear separation (gap or divider).
3. **One visual connector per relationship.** If two content blocks relate to each other, use exactly one visual element to show it (arrow, chevron, divider, badge). Not two, not zero.
4. **White space is structure.** Empty space between groups is intentional. Do not fill every square centimeter.
5. **Contrast for emphasis.** Use a filled background behind the key message, not behind everything. If every card has a background, none stands out.
6. **Consistent inner logic.** Within one composition, cards should have consistent padding, font sizes, and corner radii / border-radius. Across slides in the same deck, reuse the same card style.
7. **Align to the grid.**
   **If PPTX mode:** Tops of elements in the same row align. Lefts of elements in the same column align. Gaps between elements are mathematically equal.
   **If HTML mode:** CSS Grid and Flexbox handle this natively — use `gap` for consistent spacing.

### What this looks like in the storyline (PPTX)

The `**Layout:**` field for a free composition slide should read like a design brief:

```
**Layout:** Left half: three stacked cards (light grey fill, each ~3.5 cm tall),
containing one bold headline + one line subtext per card. Right half: two
bullet groups with section headers (#2 Platforms, #4 AI Foundation). Between
left and right: a large chevron pointing right as visual connector. Bottom
strip: a takeaway banner full width.
```

The sub-agent translates this into python-pptx code using the Shape Geometry rules below.

## Bottom Elements

A conclusion or key message at the bottom of the slide.

**Use sparingly.** Aim for no more than 30–40% of content slides. A kicker is only warranted when the visual element does not speak for itself and an explicit concluding statement adds real value for the audience. If every slide has a kicker, the effect is diluted and it becomes visual noise rather than emphasis.

**When to add a bottom element:**

- The slide contains data/numbers that need interpretation ("This means we are on track / at risk")
- The slide presents options and the audience needs to know the recommended path
- The slide closes a narrative arc and a strong statement drives the point home

**When to omit (most cases):**

- The visual is self-explanatory (hero number, progress ring, infographic)
- The title already states the conclusion
- The slide is a supporting/context slide (not the decision-making moment)
- The preceding slide already provided the key takeaway

**If PPTX mode (Kicker / Takeaway Line):**

- Font: target 20–22pt, Bold (hard minimum 18pt)
- Color: `COLOR_PRIMARY` or `COLOR_DARK`
- A container (banner or box) is **recommended** — use a colored banner or a dedicated takeaway box
- Position: lower third of the content area, horizontally centered, at least 1 cm of space above
- Width: either full content width (banner) or 70–85% centered (takeaway box)
- **Wrong:** 13pt, grey, flush to the bottom edge, plain textbox — looks like a disclaimer.
- **Right:** 20pt bold in a banner/box, primary color, clear breathing room above.

**If HTML mode:**

- **`.takeaway`** — bordered box, centered text, `var(--primary)` color. For interpretive conclusions.
- **`.banner`** — full-width colored bar, white text. For bold statements.

## Shape Geometry & Alignment (PPTX)

These rules apply to all shapes (cards, arrows, tiles) in the delivery build and polish steps.

### Corner Radius

`ROUNDED_RECTANGLE` has a default radius in python-pptx that looks too strong on large shapes (>8 cm) — the sides appear curved instead of straight. Fix: set the radius explicitly small.

```python
shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
# Tight corner radius: ~2-3% of shorter side, max 0.3 cm
shape.adjustments[0] = 0.02  # 2% of shortest dimension
```

**Reference values:**

- Small tiles (< 5 cm height): `adjustments[0] = 0.04` (slightly rounded)
- Medium cards (5–10 cm): `adjustments[0] = 0.02` (subtle)
- Large cards (> 10 cm): `adjustments[0] = 0.01` (nearly straight edges)

### Grid Alignment

All elements must be mathematically aligned to the grid. Visual "roughly centered" is not enough.

**Calculation for symmetric layouts:**

```
total_width  = FREE_WIDTH
used_width   = n * element_width + (n-1) * gap
start_left   = FREE_LEFT + (FREE_WIDTH - used_width) / 2   # centered
```

**Connector / arrow between two elements:**

```
arrow_left = left_box_right + gap / 2 - arrow_width / 2   # exactly centered in the gap
arrow_top  = box_top + box_height / 2 - arrow_height / 2  # vertically centered to the box
```

**Checklist:**

- Left edge of box 1 and right edge of box N are symmetric around `FREE_LEFT + FREE_WIDTH / 2`
- Arrows/connectors sit exactly in the center of the gap between boxes
- Vertical center of arrows = vertical center of adjacent boxes
- For n side-by-side elements: `element_left[i] = start + i * (element_width + gap)`

## Images (HTML)

Slides can include external images (photos, screenshots, diagrams). Images are stored in the deck's `assets/` directory and referenced with relative paths.

### When to use images

- **Screenshots / photos** — use `<img>` with relative path
- **Architecture diagrams** — if provided by the user, use `<img>`; if not, build with inline SVG
- **Icons / decorative graphics** — prefer inline SVG (BMW colors, no external deps)
- **Charts** — prefer inline SVG for simple charts; use images for complex ones

### Image sizing

Images inside a slide's `.content` area should be constrained:

```html
<img
  src="./assets/diagram.png"
  alt="Architecture"
  style="max-width:100%;max-height:100%;object-fit:contain;"
/>
```

For images that serve as slide backgrounds or full-bleed visuals, use CSS `background-image` in `overrides.css`:

```css
#slide-N .content {
  background: url(./assets/hero.jpg) center/cover no-repeat;
}
```

### Image lifecycle

1. **During iteration:** images use relative paths (`./assets/file.png`), preview HTML works locally
2. **On export:** the assemble script base64-encodes all images into the HTML — result is self-contained
3. **For PDF:** Playwright renders from the local file, so relative paths work via `file://`

## SVG Guidelines (HTML)

For charts, diagrams, and custom infographics, use inline SVG:

- Use BMW color variables via `fill` and `stroke` attributes (hardcode the hex values since SVG can't read CSS variables in all contexts)
- Primary: `#035970`, Accent: `#FBAE40`, Secondary: `#F26B43`, Accent2: `#548D9E`
- Keep SVGs simple: lines, rects, circles, paths, text
- Use `viewBox` for responsive scaling within flex/grid containers
- Prefer inline SVG over external SVG files

## Infographic Elements (PPTX — buildable in the free area)

These elements can be built with python-pptx shapes (rectangles, ovals, textboxes, connectors) in the free layout area:

**Hero number with context:**
Large number centered (48pt+, Bold, primary color). One line of context below (18pt, secondary color). Optional: trend arrow shape beside it.

**Comparison cards (3 or 4 side by side):**
Equal-size rounded rectangles. Each card: metric large at top, short label below. Optionally color-coded (primary, secondary, accent).

**Progress bar:**
Horizontal rectangle (background grey), a shorter rectangle on top (primary color) as fill level. Percentage value to the right.

**Before/After comparison:**
Two large numbers left and right. Between them an arrow shape or trend indicator. Short label below each.

**Traffic light / RAG status:**
Three circles (red/amber/green) side by side; the current status larger or highlighted with a border. Label below.

**Simple bar comparisons:**
Horizontal rectangles of varying width, stacked vertically. Label on the left, value at the right end of the bar.

## Tone by Audience

- **Management/Board:** Maximum 3 bullets per slide. Large numbers. Clear statements. Color used sparingly.
- **Department/Team:** More detail allowed. Tables ok. Technical terms acceptable.
- **External/Customers:** Visually engaging. Minimal text. Prefer images.

## Storyline Review Checklist

Before outputting the storyline, check every slide:

- Can I replace bullets with a visual representation?
- Is the key message readable in 3 seconds?
- Is there a number that works as a hero element?
- Are details in Speaker Notes instead of on the slide?

## Delivery Polish: Review Checklist (PPTX)

After the build, visually check every content slide. **Never touch the title placeholder.**

### Per-Slide Checklist

| Problem                     | Symptom                                                                                         | Fix                                                                                                                                                                                                                           |
| --------------------------- | ----------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Dead space                  | More than 60% of free area is empty                                                             | Redistribute content, increase font size, or vertically center. Intentional white space around a centered visual is ok.                                                                                                       |
| Bare bullets                | Text bullets with no visual structure                                                           | Choose a treatment that fits the slide's visual character: card backgrounds, accent underlines, numbered badges, key-value pairs, or strong typographic hierarchy (bold headlines + light body). Not every slide needs cards. |
| Missing separation          | Multi-column without visual separator                                                           | Divider line, card per column, or generous white space gap (>1cm)                                                                                                                                                             |
| No visual anchor            | No shapes and no strong typographic hierarchy                                                   | Consider adding a shape if the slide looks unstructured. Clean text-only with clear hierarchy is acceptable.                                                                                                                  |
| Process/steps               | Sequential items as a flat list                                                                 | Chevron chain, arrow steps on a bar, or numbered icon circles                                                                                                                                                                 |
| Oversized chevrons          | Chevrons fill >60% of slide height, large empty colored areas, text label in separate box below | Compact chevrons (~Cm(5) height): title + subtitle both inside the body, floating badge circle above. Never stretch chevrons to fill leftover space.                                                                          |
| Inconsistent chevron colors | Alternating primary/muted without semantic meaning                                              | All chevrons same color (`COLOR_PRIMARY`) unless a color encodes a distinct meaning (e.g. active vs inactive phase)                                                                                                           |
| Visual monotony             | 3+ slides in a row use the same shape type (e.g. all cards, all chevrons)                       | Vary the dominant shape across adjacent slides — see Transformation Table variation rule                                                                                                                                      |
| Corners too round           | Card edges look curved instead of straight                                                      | Reduce `adjustments[0]` (0.01–0.02), see Shape Geometry                                                                                                                                                                       |
| Alignment drift             | Arrows/connectors not exactly centered, boxes not symmetric                                     | Calculate positions arithmetically from total width, never eyeball                                                                                                                                                            |
| Connector overlap           | Center arrow/chevron intrudes into adjacent cards                                               | Compute from gap (`arrow_w <= gap - 2*margin`), or use `add_gap_chevron`                                                                                                                                                      |
| Weak kicker                 | Key message at bottom looks like a footnote (too small, too pale, plain text)                   | Use banner or takeaway box, target 20–22pt bold (min 18pt), clear spacing above                                                                                                                                               |

### Rules

1. **Content area only.** Never modify the title placeholder (idx 0) — no font, size, position, or color changes.
2. **Shapes behind text.** Push new background shapes behind content with `send_to_back()`.
3. **Preserve text.** Never delete or rewrite existing text content. Only add shapes around/behind it.
4. **Reposition placeholders.** Move content placeholders inward for card padding (~0.5 cm).
5. **Prefer 2–3 shape types per slide.** Complex compositions (infographics, dashboards) may use more — but every shape should serve a purpose. Avoid decorative clutter.
6. **Brand consistency, not visual uniformity.** Same colors, same fonts, same brand elements across all slides. But vary the visual treatment per slide — not every slide needs cards, accent strips, or the same layout pattern. The deck should feel like a curated collection, not a cookie-cutter template.
