# Delivery Workflow

After storyline approval, the skill runs a single internal delivery phase. Asset sourcing, per-slide build, per-slide polish/review, and final QA are not separate user-facing phases — they are steps of one pipeline that finishes before asking the user again.

## User-Visible Workflow

```
Phase 1  Storyline     ─→ save ─→ wait for "go"
Phase 2  Delivery      ─→ Assets → per-slide Build/Polish/Review → Collection pass → Final QA
                       ─→ ask user once ─→ done
```

**HTML only:** on-demand Export (self-contained HTML with base64 images) and PDF phases follow after user approval — see `./phases/html/export.md` and `./phases/html/pdf.md`.

## Internal Pipeline

1. **Parse storyline and build slide manifest.**

   - Orchestrator initializes run state: `slide -> layout -> required asset`.
   - Orchestrator owns state/versioning and routes all issues.
   - Sub-agents are stateless workers; each run starts in a fresh thread/context.

2. **Source assets (format-specific rules).**

   - **If PPTX mode:**
     - Always: layouts 0, 1, 13, 14, 18, 19
     - Conditional: layouts 2, 12 only when storyline calls for an image
     - Never: layouts 7-11
   - **If HTML mode:**
     - Source assets for any slide whose storyline calls for an image.
     - Use the asset-sourcing reference and manifest format from the HTML skill.

3. **Download via `./scripts/download_assets.py`** and keep resolved manifest metadata.

   - **If PPTX mode:** Use `--require-slides "$(uv run python ./scripts/pptx/storyline_required_picture_slides.py /path/to/<deck>-storyline.md)"` for fail-fast. Prefer direct binary URLs; avoid `source.unsplash.com`.
   - **If HTML mode:** Download into the deck's `assets/` directory. Prefer direct binary URLs; avoid `source.unsplash.com`.

4. **Launch parallel slide agents.**

   - Input to each agent: only one `## Slide N ...` storyline block + layout/component reference.
   - Agents may use nested sub-agents if needed, but only for that slide.
   - **If PPTX mode:** Bounded parallelism. Concurrency cap: `MAX_PARALLEL_SLIDE_AGENTS = 4` (default), max 6.
   - **If HTML mode:** Unbounded parallelism. One sub-agent per slide fragment.

5. **Per-slide inner loop:**

   **If PPTX mode:**

   - Build: generate/fix `slide_NN.py` and run assembler.
   - Structural gate (non-visual, mandatory): run `check_slide_structure.py` for slide `N`.
   - Polish: run slide-scoped polish for slide `N` only.
   - Polish gate (non-visual, mandatory): run `check_slide_polish.py` for slide `N`.
   - Orchestrator writes `issues_NN.json` and routes ownership:
     - `owner=build` for structure failures
     - `owner=polish` for polish failures
     - Resolve in order `build -> polish` when both exist
   - Review: render and review only slide `N` (`self-review.sh --only N`).
   - Iterate until slide `N` is clean.

   **If HTML mode:**

   - Build: generate/fix `slide-N.html` fragment.
   - Assemble: run `assemble.mjs <deck-dir>` to produce preview HTML.
   - Screenshot review: run `screenshot.mjs` to capture slide `N`, then visually review the PNG.
   - Auto-fix: if issues are found, edit the fragment and re-assemble.
   - Iterate until slide `N` is clean.

6. **Collection pass:**

   **If PPTX mode:**

   - Full polish consistency sweep across all slides.
   - Single full-deck `--scan` QA.

   **If HTML mode:**

   - Full assemble of all fragments into preview HTML.
   - Screenshot every slide and run a final visual check for cross-slide consistency (fonts, spacing, color accents, footer uniformity).

7. **Ask user once** for final changes.

## Per-Slide Commands

**If PPTX mode:**

Structural gate:

```bash
uv run python ./scripts/pptx/check_slide_structure.py \
  --pptx /path/to/build-output.pptx \
  --slide N \
  --layout X
```

Polish gate:

```bash
uv run python ./scripts/pptx/check_slide_polish.py \
  --pptx /path/to/final-output.pptx \
  --slide N
```

Single-slide review render:

```bash
bash ./scripts/pptx/self-review.sh /path/to/output.pptx --only N
```

Orchestrator issue routing:

```bash
uv run python ./scripts/pptx/fastmode_orchestrator.py \
  --storyline /path/to/<deck>-storyline.md \
  --build-pptx /path/to/build-output.pptx \
  --final-pptx /path/to/final-output.pptx \
  --issues-dir /path/to/issues
```

This writes:

- `issues/issues_NN.json` per slide
- `issues/issues_summary.json` for deck-wide routing (`build`, `polish`, `global`)

Polish script requirement:

- `build_polish.py` must support slide-scoped execution (`--only N,M`) for inner-loop use.
- Run full polish without `--only` for collection pass.

**If HTML mode:**

Assemble preview:

```bash
node {skill-dir}/scripts/html/assemble.mjs <deck-dir>
```

Screenshot for review:

```bash
node {skill-dir}/scripts/html/screenshot.mjs <deck-dir>/<deck-name>-preview.html
```

Export (self-contained):

```bash
node {skill-dir}/scripts/html/assemble.mjs <deck-dir> --export
```

## Review Policy

- In inner loops, do one visual review after the final quality step (PPTX: after polish; HTML: after assemble + screenshot).
- Do not run an additional post-build visual review in the inner loop.
- **If PPTX mode:** Structural quality is enforced by `check_slide_structure.py` before polish.
- **If HTML mode:** Visual quality is enforced by screenshot review after each fragment build.

## Quality Guardrails (Must Keep)

### Shared Principles

1. No unresolved placeholder prompts in any slide.
2. Attribution completeness is mandatory.
3. Footer and confidentiality label present on every slide.
4. Final full-deck QA is mandatory before user handoff.

### Format-Specific Checks

**If PPTX mode:**

1. Title placeholders are never modified during polish.
2. Structural correctness is mandatory:
   - Slide 1 is layout 0 or 19 and has image.
   - No missing required picture slides.
3. Polish correctness is mandatory:
   - Readable font sizes, card padding, no title overlap, consistent accents.
   - Bottom conclusions (if used) must be banner/boxed takeaway style, not tiny plain text.
4. Final full-deck contact sheet QA is mandatory before user handoff.

**If HTML mode:**

1. Every fragment is valid, self-contained HTML (no broken tags, no external dependencies beyond shared CSS).
2. Images use relative paths during development; base64-encoded only on export.
3. Consistent component usage across slides (fonts, spacing, color accents match the component library).
4. Navigation (keyboard arrows, dot nav) works correctly in assembled preview.
5. Final screenshot review of every slide is mandatory before user handoff.

## Keep Complexity Low

- No binary PPTX merge logic (PPTX) or monolithic HTML editing (HTML).
- No heavyweight caching framework.
- Track changed slides as `N,M,...`.
- Inner loop is always slide-scoped (`--only` for PPTX; single fragment for HTML).

## Stop Gate

After the collection pass and final QA, ask once:

> "I've completed assets, build, polish, and final QA and saved the presentation to `[path]`.
> Please open it and share any final slide changes (text or screenshot), or reply **done**."
