---
name: bmw-slides
description: >
  Use this skill when the user wants to create a presentation, build slides,
  generate a PPTX file, create an HTML slide deck, export slides to PDF,
  or asks to "make a presentation", "create slides", "build a deck",
  "make an HTML presentation", "create an HTML deck", "build HTML slides",
  "Präsentation erstellen", "Folien bauen", "HTML-Präsentation erstellen",
  or "Folien als HTML".
  Reads markdown content, creates a storyline with layout choices, and generates
  the final output as either PPTX (via python-pptx) or HTML slides with BMW design.
license: Proprietary
metadata:
  authors:
    - Christian Mueller <christian.MR.mueller@bmw.de>
  version: 1.1.0
  tags:
    - experimental
    - presentation
    - slides
    - pptx
    - html
    - powerpoint
    - deck
    - bmw
    - pdf
---

# Generating BMW Presentations

Transform markdown content into polished presentations in BMW corporate design. Supports two output formats: PowerPoint (PPTX) and HTML slide decks.

## Style Selection (Registry-Aware)

**Before the Format Detection step, always resolve the presentation style.** Skip only if the user is appending to / editing an existing deck.

### Style Resolution Steps

**1. Query the registry and get the live menu:**
```bash
python ~/.config/opencode/ppt-styles/list_styles.py --menu
```

**2. Present the style menu to the user:**

Copy the output of `list_styles.py --menu` verbatim. It shows each style's primary color, font, dark/light layout split, and whether it has a custom title background — so the user can make a meaningful choice. Example output:
```
🎨 Which presentation style would you like to use?

  1. BMW CI [default] — #035970, BMWGroupTN Condensed  [BMW Group standard, light backgrounds]
  2. <Name> — <primary_color>, <font>  [<tags: dark layouts, palette, etc>]

   Press Enter or type "1" for the default, or pick a number / name.
   Have a .pptx not listed? Share its path and I'll clone it first.
```

**3. Resolve:**

| User input | Action |
|------------|--------|
| Empty / "1" / "BMW" / "default" | Use BMW CI — follow the standard `template.pptx` workflow below |
| Number or style name from registry | Load `<style_dir>/brand-guide.md` + `<style_dir>/style.json`; use `<style_dir>/source.pptx` as the python-pptx template |
| New `.pptx` file path | Clone first: `python ~/.config/opencode/ppt-styles/clone_style.py "<file>" --name "<name>"`, then use the new style |

**4. Carry the resolved style through all phases:**

- **Phase 1 (storyline):** Reference the resolved brand guide when choosing layouts, colors, and visual motifs. Use `typography_summary.primary_color` as the dominant brand color. Note dark vs light layout split from `layout_stats`.
- **Phase 2 (delivery/build):** Pass `brand_guide_path` and `style_json_path` to sub-agents. Sub-agents load `style.json` for exact color hex codes, font names, and layout names; they use `source.pptx` (or `template.pptx` for BMW CI) as the python-pptx template base.
- **Font family constraint (all styles):** Only BMW Group typefaces are permitted — `BMWGroupTN Condensed`, `BMW Group Condensed`, or `BMW Group`. Check `brand-guide.md` → "Font Family Rule" section. Never substitute system fonts silently.
- **config.yaml overrides** still apply (department, footer, author, confidentiality).

---

## Pre-flight: Department & Output Path

Ask these two questions **once**, right after style selection and before format detection. If either value was already provided in the user's prompt, skip that question.

### 1 — Department

Ask:

> **Which department should appear on the title slide and slide master footer?**
> *(e.g. "FG-12", "AI4DevOps", "Digital Transformation", or press Enter to leave blank)*

Use the answer as the `DEPARTMENT` value for the entire deck. It overrides `config.yaml → department` for this build only — `config.yaml` stays unchanged.

- Write the value into `build_common.py` as a string literal: `DEPARTMENT = "<value>"`
- It feeds into: title-slide dept. badge (layout 0/19, placeholder idx 22), slide-master footer (`FußzeileAU1`), and the `FOOTER` string.
- If the user presses Enter / leaves blank: `DEPARTMENT = ""` and the badge placeholder is cleared.

### 2 — Output Location

Ask:

> **Where should the presentation be saved?**
>
> ```
>   1. OneDrive (default) — auto-detected for your OS
>   2. Enter a custom path
> ```
>
> *(Press Enter or type "1" for OneDrive)*

**OneDrive path detection logic (Option 1 / default):**

| OS | Candidate paths (check in order) |
|----|----------------------------------|
| macOS | `~/Library/CloudStorage/OneDrive-BMWGroup/Documents/Presentations/` → `~/Library/CloudStorage/OneDrive-BMW Group/Documents/Presentations/` → `~/Library/CloudStorage/OneDrive-Personal/Documents/Presentations/` → `~/OneDrive/Documents/Presentations/` |
| Windows | `%USERPROFILE%\OneDrive - BMW Group\Documents\Presentations\` → `%USERPROFILE%\OneDrive\Documents\Presentations\` |

Use `os.path.expanduser` / `os.path.expandvars` to resolve these. Pick the **first path whose parent directory (`CloudStorage/` or `OneDrive…`) exists** (i.e. OneDrive is mounted). Create the `Documents/Presentations/` subfolder chain if it doesn't exist.

> **macOS note:** the actual mount name is `OneDrive-BMWGroup` (no space, no hyphen-space) on most machines — check this first. `OneDrive-BMW Group` is a fallback for older mounts.

If no OneDrive mount is found, fall back to `~/Documents/Presentations/` and tell the user.

**Custom path (Option 2):** accept any absolute or `~/`-prefixed path the user types. Create it if it doesn't exist.

**Deck folder (always):** create one folder named after the **topic slug** directly inside the resolved base path — the topic slug is the only subfolder created; never nest an extra `Presentations/` inside the base:

```
<chosen-base>/
└── <topic-slug>/              ← deck root — named from the user's topic, created at build time
    ├── assets/                ← sourced images
    ├── build/                 ← slide_NN.py scripts + assembler
    ├── review/                ← self-review JPEGs
    ├── <topic-slug>-storyline.md
    └── <topic-slug>.pptx      ← final output
```

The **topic slug** is derived from the **topic/subject phrase the user provided** (not the full expanded presentation title): lowercase, spaces → hyphens, strip special characters, cap at 40 characters.

Examples:
- User topic: "How does OpenCode compare to GitHub Copilot?" → slug: `opencode-vs-copilot`
- User topic: "Q4 2025 EV Offensive Status Update" → slug: `q4-2025-ev-offensive`
- User topic: "BMW Angular migration guide" → slug: `bmw-angular-migration`

Prefer a **short, meaningful slug** (3–5 words) over a verbatim copy of a long topic sentence.

Confirm the resolved paths to the user before proceeding:

> **Output folder:** `<chosen-base>/<topic-slug>/`
> **PPTX will be saved to:** `<chosen-base>/<topic-slug>/<topic-slug>.pptx`
> **Open in Finder:** `[Open folder](file://<chosen-base>/<topic-slug>/)`  ← substitute the real absolute path

---

## Format Detection

Decide the output format once at the start based on user signals:

| Format   | Indicators in prompt                                  |
| -------- | ----------------------------------------------------- |
| **PPTX** | "PPTX", "PowerPoint", "template", ".pptx"             |
| **HTML** | "HTML", "web", "interactive", "PDF export", "browser" |

If no clear indicator is present, ask once:

> **Soll ich PowerPoint (PPTX) oder HTML-Slides erstellen?**

Then follow the format-specific instructions throughout all phases.

---

## Prerequisites

**PPTX format:**

```bash
pip install python-pptx Pillow
```

**HTML format — PDF export only (optional):**

```bash
npx playwright install chromium
pip install pypdf
```

---

## Configuration

Defaults for department, footer, and author are stored in `./config.yaml`:

```yaml
department: "YOUR-DEPARTMENT"
footer: "YOUR-DEPARTMENT | {date} | Your Name"
author: "Your Name"
confidentiality: "CONFIDENTIAL"
```

- `department` — PPTX: fills the "Dept." placeholder on title slides (layout 0/19, placeholder idx 22). HTML: used in the cover eyebrow line.
- `footer` — PPTX: updates the slide-master footer shape (`FußzeileAU1`) on every slide. HTML: rendered on every slide. `{date}` is replaced with today's date (YYYY-MM-DD) at build/assembly time.
- `author` — author name, used in the footer and available for speaker-notes attribution.
- `confidentiality` — the confidentiality label in the slide-master center footer (PPTX) or right side of each footer (HTML). Set to `""` to hide it.

**Override per deck:** The user can override any value in the prompt (e.g., "use FG-12 as department"). Use the override; config.yaml stays unchanged.

Every generated delivery build script (PPTX) must load this config and apply it. See `./references/pptx/build_common.py.md`.

---

## Template Reference (PPTX only)

**Template:** `./template.pptx` (bundled with this skill)

Slide size: 33.87 x 19.05 cm (12192000 x 6858000 EMU), Widescreen 16:9.

See `./references/pptx/template-layouts.md` for full layout details with placeholder indices and positions.

| Idx | Name                       | Use for                                            |
| --- | -------------------------- | -------------------------------------------------- |
| 0   | Title \| Full Area         | Title slide with background image, title, subtitle |
| 1   | Divider \| Half Area Right | Section divider, text left, image right            |
| 2   | Grid \| 1                  | Title only, entire area free for custom content    |
| 7   | Content \| 1               | Title + one content placeholder (full width)       |
| 8   | Content \| 2               | Title + two content columns                        |
| 9   | Content \| 3               | Title + three content columns                      |
| 10  | Content \| 4               | Title + four content columns                       |
| 11  | Content \| 2x2             | Title + 2x2 grid (4 quadrants)                     |
| 12  | Content \| Area            | Title only, free area below for custom placement   |
| 13  | Content \| Picture Left    | Title + image left, content right                  |
| 14  | Content \| Picture Right   | Title + content left, image right                  |
| 18  | Key Note                   | Full background image + large centered title       |
| 19  | Title \| Full Picture      | Like layout 0, alternative title style             |

**Common content area:** Most content layouts share the same content zone: top 3.93 cm, height 13.6 cm (from EMU 1413933 to 6308725). Title placeholder at top: 0.96 cm, height 1.11 cm.

---

## Output Structure (HTML only)

HTML decks use a **multi-file architecture** — one HTML fragment per slide:

```
my-deck/
├── storyline.md              # Storyline from Phase 1
├── slides/
│   ├── slide-1.html          # One HTML fragment per slide
│   ├── slide-2.html
│   └── slide-N.html
├── overrides.css             # Dark backgrounds, custom component CSS
├── assets/                   # Optional images
├── my-deck-preview.html      # Assembled preview (relative image paths)
└── my-deck.html              # Exported self-contained (base64 images)
```

**Why fragments?** Editing one slide touches ~50 lines instead of an 800-line monolith. Images use relative paths during development and are base64-encoded only on export.

**Navigation:** Keyboard (left/right arrows), touch/swipe, dot navigation, progress bar, 16:9 format (1280x720 px). Entrance animations (opt-in via `.reveal` classes), respects `prefers-reduced-motion`.

---

## Workflow

This skill runs a two-phase workflow for both formats. The only user-facing gate is the storyline approval. Everything else runs as one internal delivery pipeline.

- Phase 1 (storyline) stops for user approval.
- Phase 2 (delivery) runs assets + build + polish/review + QA internally, then asks the user once.
- Concurrency cap (PPTX): `MAX_PARALLEL_SLIDE_AGENTS = 4` (default), max 6. HTML: unbounded.
- Use an orchestrator as single state owner; sub-agents are stateless workers.
- PPTX inner loop per slide: build → structural gate → polish → polish gate → single-slide review.
- HTML inner loop per slide: build fragment → assemble → screenshot review → auto-fix.
- Full rules in `./references/delivery.md`.

```
Phase 1  Storyline  ─→ save storyline ─→ wait for "go" ─⟲ user edits ─→
Phase 2  Delivery   ─→ Assets + Build + Polish/Review + QA (all internal) ─→ ask user once ─→ done
```

HTML format adds on-demand steps after delivery (triggered only on user request):

```
Export  ─→ self-contained .html (base64 images)
PDF     ─→ one-page-per-slide landscape PDF
```

**Screenshot feedback (both formats):** After delivery, the user may paste a screenshot of the opened presentation. Use the screenshot to identify layout issues (overlapping text, wrong positioning, empty areas, misaligned shapes) and fix them in the next iteration.

**VS Code / GitHub Copilot users:** Copilot Chat in VS Code cannot read images automatically. When asking the user to share a screenshot, remind them to **attach the image explicitly** using the paperclip / attach button in the chat — simply pasting or dragging an image into the message box is not enough.

---

## Phase Instructions

Read **only the file for the current phase** — do not load all phases at once.

| Phase         | PPTX File                                                                                              | HTML File                                                                                              | When to read                                                            |
| ------------- | ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------- |
| 1 — Storyline | `./phases/phase1-storyline.md`                                                                         | `./phases/phase1-storyline.md`                                                                         | User provides markdown content to turn into slides                      |
| 2 — Delivery  | `./phases/delivery-assets.md` + `./phases/pptx/delivery-build.md` + `./phases/pptx/delivery-polish.md` | `./phases/delivery-assets.md` + `./phases/html/delivery-build.md` + `./phases/html/delivery-review.md` | After storyline approved (user says "go"), run as one internal pipeline |
| Export (HTML) | —                                                                                                      | `./phases/html/export.md`                                                                              | User asks for self-contained / shareable HTML                           |
| PDF (HTML)    | —                                                                                                      | `./phases/html/pdf.md`                                                                                 | User asks for PDF export                                                |

After storyline approval, work through the delivery files end-to-end (assets → build → polish/review → QA) as one pipeline. Do not stop between them.

---

## Key References (loaded on demand, not upfront)

### Shared

| File                                | Purpose                                                              | When to read               |
| ----------------------------------- | -------------------------------------------------------------------- | -------------------------- |
| `./references/design-principles.md` | Design heuristics, transformation rules, composition patterns        | Phase 1 (storyline design) |
| `./references/asset-sourcing.md`    | Approved image sources, search process, manifest format, attribution | Delivery (asset sourcing)  |
| `./references/delivery.md`          | The delivery pipeline: per-slide loops, concurrency, quality gates   | Delivery (orchestration)   |

### PPTX-specific

| File                                               | Purpose                                          | When to read                                         |
| -------------------------------------------------- | ------------------------------------------------ | ---------------------------------------------------- |
| `./references/pptx/template-layouts.md`            | Placeholder indices and positions per layout     | Phase 1 (layout selection) and Delivery (sub-agents) |
| `./references/pptx/build_common.py.md`             | Shared boilerplate template for build scripts    | Delivery build (Step 1)                              |
| `./references/pptx/sub-agent-context.md`           | Consolidated sub-agent context (API ref + rules) | Delivery build (sub-agent prompts — agents read it)  |
| `./references/pptx/python-pptx-building-blocks.md` | python-pptx API patterns and code snippets       | Delivery build (scripts)                             |
| `./references/pptx/polish.md`                      | Polish patterns and checklist                    | Delivery polish                                      |

### HTML-specific

| File                                     | Purpose                                                            | When to read                                  |
| ---------------------------------------- | ------------------------------------------------------------------ | --------------------------------------------- |
| `./references/html/layout-primitives.md` | Grid templates, card patterns, decorators, and composition recipes | Delivery build (HTML)                         |
| `./references/html/template.html`        | Slim HTML skeleton with placeholders — consumed by assemble script | **Do not read** — used by `assemble.mjs` only |
| `./references/html/base.css`             | All shared CSS (reset, variables, structural, components)          | **Do not read** — used by `assemble.mjs` only |

---

## Scripts

### PPTX Scripts

| Script                                                | Purpose                                                                 | When to use               |
| ----------------------------------------------------- | ----------------------------------------------------------------------- | ------------------------- |
| `./scripts/download_assets.py`                        | Robust image downloader with retries, preflight, JPG conversion         | Delivery (asset sourcing) |
| `./scripts/pptx/check_slide_structure.py`             | Per-slide structural gate before polish                                 | Delivery inner loop       |
| `./scripts/pptx/check_slide_polish.py`                | Per-slide polish gate (bottom takeaway + overlap checks)                | Delivery inner loop       |
| `./scripts/pptx/fastmode_orchestrator.py`             | Writes `issues_NN.json` + summary, routes fixes to build/polish workers | Delivery orchestration    |
| `./scripts/pptx/storyline_required_picture_slides.py` | Extract required picture-slide numbers for asset fail-fast              | Delivery (assets)         |
| `./scripts/pptx/validate_storyline.py`                | Validate storyline format and completeness                              | Phase 1                   |

### HTML Scripts

| Script                                  | Purpose                                                         | When to use               |
| --------------------------------------- | --------------------------------------------------------------- | ------------------------- |
| `./scripts/download_assets.py`          | Robust image downloader with retries, preflight, JPG conversion | Delivery (asset sourcing) |
| `./scripts/html/assemble.mjs`           | Assembles slide fragments into a complete HTML file             | Delivery build + Export   |
| `./scripts/html/screenshot.mjs`         | Screenshots each slide from assembled HTML to PNG               | Delivery review           |
| `./scripts/html/html_slides_to_pdf.mjs` | Playwright-based slide-to-PDF converter                         | PDF export                |

### Assembly Usage (HTML)

```bash
# Preview (relative image paths, for local viewing)
node {skill-dir}/scripts/html/assemble.mjs <deck-dir>
# -> produces <deck-dir>/<deck-name>-preview.html

# Export (base64-encoded images, self-contained)
node {skill-dir}/scripts/html/assemble.mjs <deck-dir> --export
# -> produces <deck-dir>/<deck-name>.html

# Custom output path
node {skill-dir}/scripts/html/assemble.mjs <deck-dir> --export -o /path/to/output.html
```

---

## Output

### PPTX

The output PPTX and all build artefacts go into a **topic folder** directly inside the chosen base location (resolved during Pre-flight):

```
<chosen-base>/
└── <topic-slug>/                ← one folder, named from the user's topic
    ├── assets/                  ← sourced images
    ├── build/                   ← build_common.py, slide_NN.py, build_assemble.py
    ├── review/                  ← self-review JPEGs
    ├── <topic-slug>-storyline.md
    └── <topic-slug>.pptx        ← final output
```

Rules:
- Never add an extra `Presentations/` subfolder inside the resolved base — the topic folder sits directly under `…/Documents/Presentations/<topic-slug>/` (not `…/Documents/Presentations/Presentations/<topic-slug>/`).
- Never flatten all files into a single directory. Never place the `.pptx` directly inside `build/`.
- After delivery, always emit the folder as a clickable link: `file://<chosen-base>/<topic-slug>`

### HTML

- **Storyline:** saved inside the deck directory as `storyline.md`
- **Preview HTML:** `<deck-dir>/<deck-name>-preview.html` — for iterating locally
- **Export HTML:** `<deck-dir>/<deck-name>.html` — self-contained, shareable
- **PDF:** `<deck-dir>/<deck-name>.pdf` — one page per slide, landscape

Default location: the user's working directory or as specified by the user.
