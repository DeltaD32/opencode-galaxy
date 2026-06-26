# Phase 1: Storyline

Read the user's markdown. **Do not just map content 1:1 onto slides.** Think like a presentation designer: transform raw data into visual stories. Consult `./references/design-principles.md` for design heuristics, transformation rules, and visual patterns.

Create a numbered storyline choosing the best layout/component per slide.

## Storyline Format

The storyline is written in a structured markdown format. It is saved to disk and used by the delivery build step as the source of truth. Follow this format exactly — the build step reads it line by line.

**If PPTX mode:** Use layout indices: `## Slide N [layout X, description]`
(See `./references/pptx/template-layouts.md` for available layouts)

**If HTML mode:** Use grid templates: `## Slide N [content, grid-template]` (e.g., `## Slide N [content, 2col-wide-right]`)
Optional modifier: `## Slide N [content, sidebar-left, dark-bg]`
(See `./references/html/layout-primitives.md` for available grid templates and card primitives)

### PPTX Example

```markdown
# Storyline: [Deck Name]

Title: [Presentation Title]
Audience: [Target audience, if provided]
Department: [Department name — from Pre-flight answer, or blank]
Output: /absolute/path/to/<topic-slug>/<topic-slug>.pptx

---

## Slide 1 [layout 0, title]

**Title:** Q4 2025: EV Offensive Pays Off
**Subtitle:** Status Update for Management
**Image:** hero_bg.jpg
**Notes:** Title slide. Hero image sourced from Unsplash.

## Slide 2 [layout 7]

**Title:** Revenue Up 15% Despite Market Pressure
**Content:**

- Quarterly revenue: EUR 2.3B (+15% YoY)
- Key driver: EV segment (+34%)
- European market share stable at 12.8%
  **Layout:** Three bullets with bold numbers — bold label followed by value on each bullet.
  **Kicker:** EV segment now drives one third of total revenue.
  **Notes:** Revenue increase primarily driven by EV segment...

## Slide 3 [layout 14]

**Title:** EV Sales Doubled in 12 Months
**Content:**

- 2024: 42,000 units
- 2025: 84,000 units (+100%)
- Target 2026: 120,000 units
  **Image:** ev_sales_chart.png (right side)
  **Layout:** Content placeholder left with comparison numbers, image right.
  **Notes:** EV sales doubled year-over-year...

## Slide 4 [layout 12]

**Title:** Top Markets Compared
**Layout:** Free composition. Four cards side by side (Germany, USA, China, Rest of Europe), each with country name, sales figure, and trend arrow (green/red).
**Notes:** ...
```

### HTML Example

```markdown
# Storyline: [Deck Name]

Title: [Presentation Title]
Audience: [Target audience, if provided]
Department: [Department name — from Pre-flight answer, or blank]
Output: /absolute/path/to/<topic-slug>/

---

## Slide 1 [cover-bmw]

**Title:** AI-Native Teams
**Subtitle:** Warum 5–15% individuelle Produktivitätsgewinne nicht reichen
**Department:** YOUR-DEPARTMENT
**Cover Image:** cover_default.jpg
**Notes:** Opening slide. BMW Corporate Cover with background image from shared assets.

## Slide 2 [content, 2col-wide-right]

**Title:** Was ist ein AI-Native Team?
**Content:**

- Left card: Definition text + litmus test quote (`.quote-card`)
- Right grid: 4 dimension cards (Rollen, Prozesse, Tools, Artefakte) (`.numbered-card`)
  **Takeaway:** Kleineres Team · überproportionaler Output
  **Notes:** Core definition with the litmus test...

## Slide 3 [content, sidebar-left, dark-bg]

**Title:** Was ist erreichbar — mit Operating-Model-Wandel
**Content:**

- Hero: 5–15% vs 5–6× contrast (hero `.m-cell` left)
- Metrics: 2x speed, 2x throughput, 7x workflows, 9–12M→1W timeline, 51% merges, 6x roles (`.m-cell` tiles right)
  **Image:** ./assets/metrics-chart.png (optional — reference a local image)
  **Notes:** Evidence from McKinsey, DORA, Filev...

## Slide 4 [content, 3x2]

**Title:** Das AI-Native Operating Model — 6 Säulen
**Content:**

- 1: Kleinere Teams (`.numbered-card`)
- 2: Rollen → Orchestrator
- 3: Continuous Planning
- 4: Spec-Driven Development
- 5: AI-Friendly Codebase
- 6: Transformation managen
  **Notes:** The six pillars...
```

### Output Field

**If PPTX mode:** The `Output:` field is the absolute path to the `.pptx` file inside its topic folder: `<chosen-base>/<topic-slug>/<topic-slug>.pptx`. The storyline is saved alongside it as `<topic-slug>-storyline.md`. All other artefacts (`assets/`, `build/`, `review/`) live as siblings in the same topic folder.

**If HTML mode:** The `Output:` field points to the **deck directory** (not a file). The build step creates the directory structure:

```
<output-dir>/
├── slides/
│   ├── slide-1.html
│   ├── slide-2.html
│   └── ...
├── overrides.css          (if any slide needs dark background or custom CSS)
└── assets/                (if any images are referenced)
```

The storyline file itself is saved **inside** this directory as `storyline.md`.

## Key Rules for the Storyline File

- One slide header per slide — the layout index (PPTX) or grid template (HTML) is mandatory and read by the build step
- `**Content:**` block uses `- ` bullets for list items; plain prose for single-paragraph content
- `**Image:**` is the asset filename (from the delivery asset manifest) or omitted if no image
- `**Notes:**` becomes the slide's speaker notes
- Do not add extra markdown syntax inside the content block — keep it clean for parsing

**Content Density Limits** (both formats — split across multiple slides if exceeded):

- Title/cover slides: max 2 lines title, max 2 lines subtitle
- Content slides: 4–6 bullets max, or 2 short paragraphs
- Card grids: max 6 cards (3×2 or 2×2+2)
- Code/data slides: 8–10 lines max
- Metric tiles: max 6 tiles + 1 hero

**PPTX-specific fields:**

- `**Layout:**` describes visual arrangement in plain language — the build step translates this to code
- `**Kicker:**` (optional) is the bottom takeaway text — the build step renders it via `add_bottom_banner` or `add_takeaway_box`. Omit when the visual is self-explanatory.

**HTML-specific fields:**

- `**Takeaway:**` — bordered box below content, centered text (`.takeaway` class)
- `**Banner:**` — full-width colored bar below content (`.banner` class)
- `**Department:**` — department badge (for cover slides)

## Layout / Component Selection: Decision Hierarchy

Choose the layout (PPTX) or grid template (HTML) not mechanically by content type — work through this hierarchy instead:

### Layout Roles (PPTX) — read first

Before picking a layout, know what each group is for:

- **Semantic / fixed-role layouts (pick by role, not creatively):**

  - `0`, `19` — Title slide (Slide 1). Hero image + dept. badge + subtitle.
  - `1` — Section divider (half-bleed picture + heading).
  - `18` — Key-note slide (full-bleed image with headline).
  - `13`, `14` — Content + picture side by side. Use when storyline calls for a prominent image alongside text. The pre-positioned picture slot is a feature.

- **Free canvas layouts (this is where creative composition happens):**

  - `12` — Title + free area (13.6 cm). **Default for any non-trivial content slide.**
  - `2` — Free area with shorter title zone (15.46 cm body). Use when the composition benefits from the extra vertical room.

- **Placeholder-grid layouts — exception case, not default:**
  - `7`, `8`, `9`, `10`, `11` — 1 / 2 / 3 / 4 / 2×2 content placeholders in a fixed grid.
  - These lock the sub-agent into the template's grid geometry and make custom connectors, off-grid accents, and asymmetric compositions hard.
  - **Only pick these when the content is genuinely "plain bullets in N columns" and you explicitly want the template's built-in grid.** For everything else — cards, tiles, infographics, mixed compositions — use Layout 12, not 11. `add_mece_tiles(...)` on Layout 12 gives you tiles _and_ room for a banner, call-out, or gap connector; Layout 11 does not.

### Step 1 — Can the content be visually transformed?

First check `./references/design-principles.md` (Transformation Table): Can the content be presented more powerfully as an infographic, diagram, or free composition than as placeholder bullets? Examples:

- Number comparison → Hero Number or Before/After composition
- Equal-weight points → Cards, Tiles, Hexagon Grid
- Process / steps → Timeline, Chevron Chain, Numbered Badges
- Two content blocks with a relationship → asymmetric two-column layout with visual connector (arrow, chevron)
- Decision / recommendation → Pyramid, Comparison Table
- Status update → RAG Dashboard, Progress Rings

**If PPTX mode:** If yes → **Layout 12 (Content | Area) or 2 (Grid | 1)**. Describe the composition in the `**Layout:**` field. The sub-agent script builds the shapes freely in the content area.

Mapping to PPTX layouts:

- Number comparison → Hero Number or Before/After composition → Layout 12
- Equal-weight points → Cards, Tiles → Layout 12 or 2
- Process / steps → Timeline, Chevron Chain → Layout 12
- Two content blocks → asymmetric two-column → Layout 12 with visual connector
- Decision / recommendation → Pyramid, Comparison Table → Layout 12

**If HTML mode:** Map content patterns to grid templates:

- Number comparison → `sidebar-left, dark-bg` (hero `.m-cell` + `.m-cell` tiles)
- Before/After → `2col` (with arrow connector)
- 3–6 equal points → `3x2` or `2x2` (`.numbered-card`)
- Good vs Bad → `2col` (with VS badge)
- Definition + dimensions → `2col-wide-right` (`.quote-card` + `.numbered-card`)
- Key findings → `2col-wide-left` (`.kv-row` + `.insight-card`)
- Recommendations → `2col-wide-right` (`.accent-card` + `.step-card`)

### Step 2 — Is a custom/free composition needed?

If no existing layout or component fits the content:

**If PPTX mode:** Use Layout 12 or 2 and describe the composition in the `**Layout:**` field.

**If HTML mode:** Use `custom` and describe the layout:

```markdown
## Slide 5 [content, custom]

**Title:** Technology Stack Overview
**Layout:** custom — hexagon grid with 12 tech items, grouped by category (3 rows x 4 columns), each hex shows icon + label, color-coded by maturity
**Content:**

- Row 1: Core Platform (Kubernetes, ArgoCD, Terraform, Vault)
- Row 2: AI Stack (OpenAI, Claude, Copilot, LangChain)
- Row 3: Observability (Datadog, Grafana, PagerDuty, Sentry)
```

### Step 3 — Is a simple/placeholder layout sufficient?

Only if the content genuinely works best as a simple bullet list or text columns. **Default to Layout 12 whenever the composition is not trivially a bullet list** — placeholder layouts (7–11) lock the sub-agent into a predefined grid and should only be chosen when you actually want that grid. When unsure, pick Layout 12 and describe the composition in the `**Layout:**` field.

**If PPTX mode:**

- One topic block → Layout 7
- Two parallel topics → Layout 8
- 3–4 equal-weight short points → Layout 9/10/11

**If HTML mode:**

```markdown
## Slide 6 [content, 1col]

**Title:** Key Takeaways
**Content:**

- AI is an amplifier, not a fix
- Platform quality determines AI ROI
- Operating model change > tool change
```

**Note:** Avoid long runs of the same layout/grid template — vary where possible. But do not force free compositions when simpler layouts convey the content better. If you see 3+ consecutive simple layouts, revisit Step 1 to check whether a visual transformation would be effective.

### Fixed Assignments

**If PPTX mode:**

- **Title slide (Slide 1):** Layout 0 or 19
- **Section divider:** Layout 1 (Divider) or 18 (Key Note)
- **Closing/Outro:** Layout 18 or 12. **Never reuse Layout 0 or 19 for the outro** — those are reserved for the opening title slide only.

**If HTML mode:**

- **Slide 1:** Always `cover-bmw` (or `cover` if no image is available)
- **Last slide (if outro):** `cover-bmw` — shows the same background image as slide 1 with a single closing statement (right half, slightly above center). No logos, badges, or footer. Specify the closing text with `**Closing:**`. This is the preferred closing for BMW decks.
- **Last slide (alternative):** `2col-wide-right` with `.accent-card` + `.step-card` (recommendation/conclusion). Use when the deck ends with a concrete call to action rather than a visual outro.

### Images

Slides can reference images via the `**Image:**` field.

**If PPTX mode:**

- For picture layouts (`0, 1, 13, 14, 18, 19`), `**Image:**` is mandatory.
- `**Image:**` is the asset filename from the delivery asset manifest.

**If HTML mode:**

- Images are stored in the `assets/` subdirectory of the deck.
- The build step uses `<img src="./assets/filename.png">` in the HTML fragment.
- **Preview:** image paths stay relative (works when opened locally).
- **Export:** images are base64-encoded into the HTML (self-contained).

### Bottom Elements

**If PPTX mode:**

- `**Kicker:**` (optional) — bottom takeaway text. Use sparingly (target: 30–40% of content slides). Only add when the slide genuinely needs an explicit bottom conclusion that the visual alone does not convey. Most slides with a strong visual do **not** need a kicker. When in doubt, omit.

**If HTML mode:**
Each content slide can optionally have ONE of these bottom elements:

- `**Takeaway:**` — bordered box below content, centered text (`.takeaway` class)
- `**Banner:**` — full-width colored bar below content (`.banner` class)
- Omit both when the visual speaks for itself (target: 30–40% of content slides have a bottom element)

## Deck Composition Brief (plan before writing individual slides)

Before writing individual slide blocks, plan the visual rhythm of the entire deck. This step prevents the most common uniformity problem: slides that all look the same because each was designed in isolation.

### Step A — Identify the hero moment

Which slide carries the single most important message or number? Mark it. This slide gets the most dramatic visual treatment (hero number, full-bleed image, pull-quote, or a unique composition that no other slide in the deck uses).

### Step B — Assign a visual character to each content slide

Every content slide (not title, divider, or closing) gets one of these characters. **No character may appear more than twice in a row:**

- **Data-forward:** Hero number, progress rings, bar comparisons, RAG dashboard
- **Structure-forward:** Tiles/cards, pillars, hexagon grid, tabbed headers
- **Flow-forward:** Timeline, chevron chain, zigzag blocks, numbered badges, arrow bar steps
- **Narrative-forward:** Pull-quote, sidebar layout, pyramid, key-value pairs
- **Comparison-forward:** Comparison table, Venn, funnel, before/after columns

Write the character into the `**Layout:**` (PPTX) or slide heading (HTML) field, e.g.: `**Layout:** [flow-forward] Chevron chain with 4 stages...`

### Step C — Check visual contrast between neighbors

For each pair of adjacent content slides, verify they differ in at least 2 of these dimensions:

1. Layout number / grid template
2. Dominant shape type (e.g. cards vs. chevrons vs. rings)
3. Content density (sparse hero vs. information-rich grid)
4. Use of imagery (photo slide vs. shape-only slide)

If two adjacent slides match in 3+ dimensions, change one of them.

## Layout Description (PPTX-specific)

The `**Layout:**` field is the creative core description of the slide.

**For free layouts (2, 12)** it describes the complete composition — as detailed as needed so the build step can build it:

- Spatial arrangement: "left half three stacked cards, right half bullet groups with section headers, between them a chevron as visual connector"
- Visual elements: "Hero Number 48pt centered at top, three comparison cards below"
- Relationships: "Arrow from left to right connecting the two blocks"

**For placeholder layouts (7-14)** it describes special formatting wishes:

- "Bullets with bold numbers at the start"
- "First line as headline, rest as sub-bullets"

## Slide Types (HTML-specific)

The `[cover]` or `[content, grid-template]` in the heading maps directly to CSS classes and HTML patterns in `./references/html/layout-primitives.md`.

### Available Slide Types

**Cover / Title:**

- `cover-bmw` — **Default.** BMW Corporate cover: full-bleed background image, BMW Group + brand logos top, large title bottom-left, dept. badge bottom-right. Always use this for BMW presentations.
- `cover` — Simple gradient (no image). Use only as fallback when no image is available.

**Grid Templates** (content area layout):

- `1col` — single column, full width
- `2col` — equal 2 columns
- `2col-wide-right` — narrow left + wide right
- `2col-wide-left` — wide left + narrow right
- `3col` — equal 3 columns
- `2x2` — 2x2 grid
- `3x2` — 3 columns x 2 rows
- `sidebar-left` — narrow panel left + fluid right
- `sidebar-right` — fluid left + narrow panel right
- `custom` — free CSS composition

**Modifiers** (append to slide heading):

- `dark-bg` — dark background with adjusted text colors

## Deck-Level Design Audit

Before writing the file, run this audit against your own draft. Fix any failing check first.

| #   | Check                                                       | Rule                                                                                                                                                                                                                                         |
| --- | ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **Hero stat on hero slide?**                                | The single most important number or contrast in the deck should be on a visually prominent slide (PPTX: Layout 12 free-area; HTML: `sidebar-left, dark-bg` or `custom`) with a large visual treatment — not buried in a bullet.              |
| 2   | **No bullet graveyard?**                                    | Slides with a "before/after", "contrast", or "X vs. Y" story should use a comparison layout (PPTX: Layout 12 or 8; HTML: `2col` with connector) — avoid burying contrasts in bullet prose.                                                   |
| 3   | **No process as a list?**                                   | Slides showing a sequence, workflow, or timeline should use a visual flow (arrows, swimlanes, chevrons, numbered badges). A well-structured numbered list is acceptable for simple 2-3 step sequences.                                       |
| 4   | **Visual character variety?**                               | No visual character (data-forward, structure-forward, etc.) appears more than twice in a row. Adjacent slides differ in at least 2 dimensions (layout/grid template, shape type, density, imagery).                                          |
| 5   | **Structural break for long decks?**                        | Decks with more than 8 content slides should include at least one section separator (PPTX: Divider Layout 1 or 18; HTML: dark background slide or different visual rhythm).                                                                  |
| 6   | **Bottom elements sparingly?**                              | Kickers (PPTX) / Takeaways+Banners (HTML) on max 30-40% of content slides. Omit when visual is self-explanatory.                                                                                                                             |
| 7   | **No function/grid-template repetition in 3-slide window?** | The same visualization function (PPTX) or grid template (HTML) must not appear on two slides within a 3-slide window. If the content pattern maps to the same function/grid template, pick a different option from the Transformation Table. |

Review these checks before proceeding. Fix clear violations; minor deviations are acceptable if they serve the content.

## STOP — Save storyline and wait for user

After creating the storyline and passing the audit:

1. **Resolve output path and department** using the values collected in the SKILL.md Pre-flight step.

   The **topic slug** is derived from the user's topic phrase (not the full expanded title): lowercase, spaces → hyphens, strip special characters, cap at 40 characters. Prefer short and meaningful (3–5 words). See SKILL.md Pre-flight for examples.

   **If PPTX mode:** All files go into `<chosen-base>/<topic-slug>/`. The storyline file is saved there as `<topic-slug>-storyline.md`. The `Output:` field in the storyline header must be the **absolute path to the `.pptx` file**: `<chosen-base>/<topic-slug>/<topic-slug>.pptx`.

   **If HTML mode:** The deck directory is `<chosen-base>/<topic-slug>/`. The storyline file is saved inside as `storyline.md`. The `Output:` field points to the deck directory: `<chosen-base>/<topic-slug>/`.

2. **Write the storyline file** using the format above. Use the Write tool.

2a. **Validate before presenting to user (PPTX mode only):**

```bash
uv run python ./scripts/pptx/validate_storyline.py /absolute/path/to/<deck>-storyline.md
```

If validation fails, fix the storyline file first.

3. **Ask the user how they want to preview the storyline:**

> "I've created your presentation storyline and saved it to:
> `[/path/to/<topic-slug>-storyline.md]`  [file:///path/to/<topic-slug>/]
>
> How would you like to preview it?
>
> ```
>   1. Markdown (.md) — open the raw file in your editor
>   2. HTML preview — I'll generate a styled .html file you can open in a browser
> ```
>
> *(Press Enter or type "1" for Markdown)*"

**If user chooses 1 / Markdown / default:** tell them the file path and remind them they can open it in any editor. No further output needed.

**If user chooses 2 / HTML:** write a self-contained `.html` file to disk at `<topic-slug>/<topic-slug>-storyline-preview.html` and give the user a clickable link to open it. Do NOT render the table inline in chat.

The HTML file must be a complete, standalone document with this structure — replace all placeholders with real data from the storyline file:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Storyline: [Deck Title]</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; max-width: 1100px; margin: 40px auto; padding: 0 24px; color: #1a1a1a; background: #f7f8fa; }
  h1 { font-size: 1.4rem; color: #035970; margin-bottom: 4px; }
  .meta { font-size: 0.85rem; color: #666; margin-bottom: 28px; }
  table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
  th { background: #035970; color: #fff; text-align: left; padding: 10px 14px; font-size: 0.82rem; font-weight: 600; letter-spacing: 0.03em; }
  td { padding: 10px 14px; font-size: 0.84rem; border-bottom: 1px solid #eef0f3; vertical-align: top; }
  tr:last-child td { border-bottom: none; }
  tr:nth-child(even) td { background: #f9fafb; }
  td:first-child { font-weight: 700; color: #035970; width: 40px; text-align: center; }
  td:nth-child(3) { color: #555; font-size: 0.78rem; }
  td:nth-child(4) { font-style: italic; color: #777; font-size: 0.78rem; }
  .hero { background: #fff8f0 !important; }
  .hero td:first-child::after { content: " ⭐"; }
  .divider td { color: #aaa; font-style: italic; }
  footer { margin-top: 20px; font-size: 0.75rem; color: #aaa; }
</style>
</head>
<body>
<h1>Storyline: [Deck Title]</h1>
<div class="meta">[N] slides · Dept: [Department] · Output: [Output path]</div>
<table>
<thead>
<tr><th>#</th><th>Title</th><th>Layout</th><th>Visual Character</th><th>Key Content</th></tr>
</thead>
<tbody>
<!-- one <tr> per slide; add class="hero" on the hero slide, class="divider" on section dividers -->
<tr><td>1</td><td>[title]</td><td>[layout tag]</td><td>[visual character]</td><td>[1-line content summary]</td></tr>
</tbody>
</table>
<footer>Edit: [/absolute/path/to/<topic-slug>-storyline.md] · Generated by bmw-slides skill</footer>
</body>
</html>
```

After writing the file, tell the user:

> "📄 Storyline preview saved:
> [`<topic-slug>-storyline-preview.html`](file:///absolute/path/to/<topic-slug>-storyline-preview.html)
> — open it in any browser.
>
> You can also edit the source directly: `<topic-slug>-storyline.md`"

Then ask:

> "Please review — things to check:
> - Slide order and flow
> - Layout choice per slide (`[layout N]` tag in each heading)
> - Content distribution (too much / too little per slide?)
> - Missing or unnecessary slides
>
> When you're happy, reply **go** and I'll run the delivery pipeline."

4. **Wait.** Do NOT proceed until the user replies **go** (or equivalent). If the user edits the file and says go, the delivery build step will pick up the edited version from disk.
