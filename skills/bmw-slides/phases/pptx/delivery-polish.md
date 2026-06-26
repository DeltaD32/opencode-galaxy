# Delivery Step 3 — Polish & QA

This is the polish step of the internal delivery pipeline. It runs immediately after `delivery-build.md` without a separate user approval gate. The single user-facing stop happens at the end of this step, after final deck QA.

Implementation rule: `build_polish.py` must support slide-scoped runs (e.g. `--only N,M`) for per-slide inner loops, plus a full run for the final collection pass.

Run modes:

```bash
# slide-scoped polish for inner loop
uv run python build/build_polish.py --only 3,7

# full collection pass
uv run python build/build_polish.py
```

Generate and execute a **second** Python script that opens the build step's output and enhances content areas. **Never touch title placeholders (idx 0) — no font size, position, or style changes.**

Read `./references/pptx/polish.md` for full details:

- **Polish Checklist** — 5 checks per slide (dead space, plain bullets, column separation, visual anchors, attribution)
- **Enhancement Patterns** — cards, accent strips, icon circles, step indicators, connector lines, pillars, comparisons
- **Polish Rules** — 8 rules (content area only, z-order, padding, font minimums, consistent styling, no over-decorating)
- **Polish Script Template** — boilerplate with color palette, `SKIP_LAYOUTS`, per-slide loop (helpers come from `build_common.py.md`)
- **Self-Review Checklist** — what to verify after running the polish script

### Self-review (polish-scoped)

The build step already validated structural correctness (placeholders filled, no text overflow, correct layouts). The polish step only checks **polish-specific concerns**.

```bash
bash ./scripts/pptx/self-review.sh /path/to/final.pptx --scan
```

Read `review/contact.jpg` and check **only** (all review images are `.jpg` — never `.png`):

- Card backgrounds and accent strips present and correctly positioned
- No shapes overlapping title placeholder
- Text not touching card edges (≥ 0.4 cm gap visible)
- Bottom conclusion lines are not footer-like: use banner/box treatment and readable size
- Visual balance — no slide is just plain white with tiny text
- Consistent accent color across polished slides

If the contact sheet looks clean, proceed to the STOP gate. If a specific slide looks off, read that `slide-NN.jpg` for detail.

After fixing a slide, use selective re-review:

```bash
bash ./scripts/pptx/self-review.sh /path/to/final.pptx --only N
```

Before each selective visual re-review, run:

```bash
uv run python ./scripts/pptx/check_slide_polish.py --pptx /path/to/final.pptx --slide N
```

Then refresh routing artifacts so the orchestrator can close `issues_NN.json` for fixed slides:

```bash
uv run python ./scripts/pptx/fastmode_orchestrator.py \
  --storyline /path/to/<deck>-storyline.md \
  --build-pptx /path/to/build-output.pptx \
  --final-pptx /path/to/final.pptx \
  --issues-dir /path/to/issues \
  --slides N
```

## ⛔ STOP — Final Delivery Handoff

This is the **single user-facing stop** after storyline approval. Everything up to here — assets, build, polish, review, QA — ran internally as one pipeline.

Tell the user the polished file has been saved, share the slide-by-slide self-review findings, and ask:

> "I've delivered the presentation — assets sourced, slides built, polished, reviewed, and QA'd. Saved to `[path]`.
> Here's what changed during polish and what I found in the review:
> [list of per-slide changes and any issues fixed]
>
> Please open it in PowerPoint for a final check. You can paste a **screenshot** of any slide that needs adjusting.
> _(VS Code / GitHub Copilot users: attach the screenshot via the paperclip button — do not just paste it into the chat.)_
>
> What would you like to change? Or reply **done** if the presentation is ready."

**If the user requests changes** (via text or screenshot): re-enter the inner loop for only the affected slide(s) — update the slide file, re-run the assembler, re-run slide-scoped polish, and re-review that slide. Repeat until the user says done.
