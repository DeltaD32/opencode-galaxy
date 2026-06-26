# Delivery Step 2 — Build Slide Fragments

This is the build step of the internal delivery pipeline. Runs after `./phases/delivery-assets.md` and flows directly into `./phases/html/delivery-review.md` without a user gate.

Read the storyline file from disk. Build **one HTML fragment per slide** using parallel subagents — each subagent builds one slide. Then merge results and assemble the preview.

## Build Process

### Step 1 — Load references and parse storyline

Read these files:

- The storyline file (from disk — the user may have edited it)
- `./config.yaml` — footer, author, confidentiality defaults (for reference only)

**Do NOT read** `layout-primitives.md`, `template.html`, or `base.css` — the subagents read the layout primitives, and the assemble script consumes the rest.

Parse the storyline into a list of slides. For each slide, extract:

- **Slide number** (N)
- **Slide type and grid template** (from the `## Slide N [type]` heading — e.g., `cover`, `2col-wide-right`, `3x2`, `custom`)
- **Full storyline block** (everything from `## Slide N` to the next `## Slide` heading or end of file)

### Step 2 — Create deck directory structure

The storyline's `Output:` field points to the deck directory. Create:

```
<deck-dir>/
├── slides/          (create this directory)
└── assets/          (create only if images are referenced in storyline)
```

The storyline file should already be in `<deck-dir>/storyline.md` from the storyline phase.

### Step 3 — Launch parallel subagents to build slides

Launch **one Task subagent per slide**, all in parallel. Use `subagent_type: "general"`.

Each subagent:

1. Reads the layout primitives
2. Builds the HTML fragment
3. Writes it to `slides/slide-N.html`
4. Returns any CSS overrides needed for that slide

#### Subagent Prompt Template

For each slide N, launch a Task with this prompt:

````
You are building slide {N} of an HTML presentation. Write the HTML fragment and return any CSS overrides.

## Your task

1. Read the layout primitives: `{skill-dir}/references/html/layout-primitives.md`
2. Build the HTML fragment for this slide based on the storyline below
3. Write the fragment to: `{deck-dir}/slides/slide-{N}.html`
4. Return any CSS overrides this slide needs (or empty string if none)

## Storyline for this slide

```
{paste the full ## Slide N block from the storyline here}
```

## Total slide count: {total}

## Fragment rules

The fragment is ONLY the slide `<div>` — no `<html>`, no `<head>`, no `<style>`, no `<script>`.

**Content slide structure:**
```html
<!-- SLIDE {N} — {DESCRIPTION} -->
<div class="slide" id="slide-{N}">
  <div class="title-bar">
    <h2>Slide Title</h2>
    <span class="slide-num">{N} / {total}</span>
  </div>
  <div class="content">
    <!-- Grid template + card primitives from layout-primitives.md -->
  </div>
  <div class="footer">
    <span>{footer}</span>
    <span class="conf">{confidentiality}</span>
  </div>
</div>
```

**Cover slide structure** (slide 1, type `cover-bmw` — **default**):
```html
<!-- SLIDE 1 — BMW CORPORATE COVER -->
<div class="slide cover-bmw active" id="slide-1">
  <!-- Background image: use shared project assets (../../assets/) or deck assets (./assets/) -->
  <div class="cover-bmw-bg" style="background-image:url('../../assets/cover_default.jpg');"></div>
  <div class="cover-bmw-overlay"></div>

  <!-- Header: logos always come from shared assets -->
  <div class="cover-bmw-header">
    <div class="cover-bmw-logo-left">
      <img src="../../assets/bmw_group.png" alt="BMW Group">
    </div>
    <div class="cover-bmw-logo-right">
      <img src="../../assets/bmw_mini.png" alt="BMW and MINI">
    </div>
  </div>

  <!-- Body: title block bottom-left, dept badge bottom-right -->
  <div class="cover-bmw-body">
    <div class="cover-bmw-title-block">
      <div class="cover-bmw-title">{PRESENTATION TITLE,<br>TWO LINES MAX.}</div>
      <div class="cover-bmw-sub-divider"></div>
      <div class="cover-bmw-subtitle">{SUBTITLE, TWO LINES MAX.}</div>
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

**Outro slide** (last slide, type `cover-bmw`): background image + overlay + one closing statement. No header, no logos, no title block, no dept badge, no banner, no footer. Use the correct slide number for `id`. Do NOT add the `active` class.

- The closing statement comes from the storyline (field `**Closing:**` or similar)
- Position: right half of the slide, vertically slightly above center
- Style: large, white, bold — similar weight to the cover title

```html
<!-- SLIDE {N} — OUTRO -->
<div class="slide cover-bmw" id="slide-{N}">
  <div class="cover-bmw-bg" style="background-image:url('../../assets/cover_default.jpg');"></div>
  <div class="cover-bmw-overlay"></div>
  <div class="outro-statement">
    {Closing statement from storyline}
  </div>
</div>
```

CSS override needed for this slide (add to `overrides.css`):
```css
/* ── Slide {N} — Outro ── */
#slide-{N} .outro-statement {
  position: absolute;
  z-index: 3;
  right: 6%;
  top: 35%;
  width: 44%;
  color: #fff;
  font-size: 2.2rem;
  font-weight: 700;
  line-height: 1.25;
  text-transform: uppercase;
  letter-spacing: 0.01em;
}
```

The background image URL must match slide 1 exactly (same file path).

**Legacy cover structure** (only when `cover` — not `cover-bmw` — is specified in the storyline):
```html
<!-- SLIDE 1 — COVER -->
<div class="slide cover active" id="slide-1">
  <div class="cover-inner">
    <div class="cover-eyebrow">{eyebrow text}</div>
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

## Animation

Add `class="reveal"` to content elements inside the grid (cards, kv-rows, etc.) for staggered entrance animation. Do NOT add reveal to structural wrappers (the grid template div, .content, .slide).

## Critical rules

- **Use literal placeholders:** `{footer}`, `{confidentiality}`, `{total}`, `{department}` stay as literal text. The assemble script replaces them later.
- **`{department}` in `cover-bmw-dept`** — always use the literal placeholder `{department}` (not the actual dept name). The assemble script fills it from config.yaml.
- **Slide 1 (cover) gets the `active` class.** All other slides do NOT.
- **No `<style>` tags in the fragment.** CSS overrides are returned separately.
- **No emoji.** Use HTML entities or SVG for icons.
- **Images use relative paths:** `<img src="./assets/filename.png" alt="description">`
  - If the image doesn't exist yet, add: `<!-- TODO: add ./assets/filename.png -->`
- **1280×720 viewport.** Content must fit. Do not overfill.
- **Use CSS variables:** `var(--primary)`, `var(--accent)`, etc. Exception: `rgba()` for transparency.
- **Look up the grid template and card patterns** in layout-primitives.md. The slide heading specifies a grid template name (e.g., `2col-wide-right`), not a component name. Look up the grid template and card patterns in `layout-primitives.md`. Compose the slide by placing card primitives into the grid.

## CSS overrides

If this slide needs CSS overrides, return them scoped to `#slide-{N}`.

Dark background slides use `class="slide dark-bg"` on the slide element — no CSS overrides needed.

Custom component slides need their CSS scoped:
```css
#slide-{N} .my-class { ... }
```

**CRITICAL — Never set `display` in overrides.** The base CSS uses `.slide { display: none }` and `.slide.active { display: flex }` for navigation. Any `#slide-N { display: flex/grid/block }` override has higher specificity and will make the slide permanently visible on top of all others. If you need flex centering for a custom layout, scope it to `#slide-{N}.active { ... }` or apply flex/grid only to child elements, not the slide itself.

## Your output

After writing the HTML fragment to disk, return a message with:
1. Confirmation that `slides/slide-{N}.html` was written
2. The CSS overrides for this slide (or "No overrides needed" if none)
   Wrap overrides in a css code block so I can extract them.
````

### Step 4 — Merge overrides and write overrides.css

After all subagents return:

1. **Collect** the CSS overrides from each subagent's response
2. **Concatenate** them into `<deck-dir>/overrides.css`, ordered by slide number:

```css
/* ── Slide 3 ── */
#slide-3 { background: #0a1628; }
/* ... */

/* ── Slide 7 ── */
#slide-7 .hex-grid { display: grid; ... }
/* ... */
```

If no slide needs overrides, write:

```css
/* No slide-specific overrides for this deck */
```

### Step 5 — Handle images

If any slide references an image (`**Image:**` in storyline):

1. Create the `assets/` directory if it doesn't exist
2. Subagents already wrote `<img src="./assets/filename.png">` in fragments
3. If the user provides an image file path, copy it to `assets/`
4. TODO comments in fragments mark missing images

## Quality Checklist

After all subagents complete and overrides are merged, verify:

| #   | Check                        | How                                                                                         |
| --- | ---------------------------- | ------------------------------------------------------------------------------------------- |
| 1   | **All slides present**       | Count `slide-*.html` files matches storyline slide count                                    |
| 2   | **First slide has `active`** | `slide-1.html` has `class="slide cover-bmw active"` or `class="slide cover active"`         |
| 3   | **Overrides complete**       | Every custom slide has CSS in `overrides.css` (dark-bg slides use the class, not overrides) |
| 4   | **Image refs valid**         | Every `<img src="./assets/...">` has a corresponding file or TODO                           |

Do NOT re-read every fragment for detailed checks — the visual review step catches layout issues via screenshots.

## After Building — Assemble Preview

After all fragments are written and overrides.css is merged, run the assemble script:

```bash
node {skill-dir}/scripts/html/assemble.mjs <deck-dir>
```

This produces `<deck-dir>/<deck-name>-preview.html` — a complete HTML file with navigation that can be opened directly in a browser.

## After Assembling — Run the Visual Review

After assembling the preview, **automatically proceed to the visual review step** (`./phases/html/delivery-review.md`). Screenshot every slide, review for layout issues, and auto-fix problems before presenting to the user. This is part of the single internal delivery pipeline — do not stop between build and review. The user can skip the visual review by saying "skip review".

## Presenting to User

After building, assembling, and completing the visual review:

> "I've built and reviewed your slides:
> `[/path/to/deck/deck-name-preview.html]`
>
> Open in any browser — use arrow keys or click dots to navigate.
>
> Want me to:
>
> - Adjust a specific slide? (I'll only edit that one fragment)
> - Export as self-contained HTML? (images base64-encoded)
> - Export to PDF?"

## Iterating on Individual Slides

When the user requests changes to a specific slide:

1. **Read only** that slide's fragment (`slides/slide-N.html`)
2. **Edit** the fragment (directly — no subagent needed for single-slide edits)
3. **Update** `overrides.css` if CSS changed
4. **Re-run** the assemble script to update the preview:
   ```bash
   node {skill-dir}/scripts/html/assemble.mjs <deck-dir>
   ```
5. **Tell the user** what changed and that the preview is updated.

This is the key advantage of the multi-file architecture: editing one slide touches ~50 lines instead of an 800-line monolith.
