# Delivery Step 3 — Visual Review & QA

This is the final step of the internal delivery pipeline. Runs after `delivery-build.md` assembled the preview. After this step, the user is asked once for final changes.

## When to Run

Run this step automatically as part of the delivery pipeline — immediately after the preview is assembled. Skip only if:

- The deck has only 1 slide (cover only), or
- The user explicitly said "skip review".

If the user later asks to re-check a specific slide (e.g. "review slide 3" after edits), run Steps 1–3 **only for that slide**.

### Reviewing individual slides

If the user specifies a slide number (e.g. "review slide 3"), run Steps 1–3 **only for that slide**:

- Screenshot only that slide
- Launch only one subagent for that slide
- Report results for that slide only

## Step 1 — Screenshot All Slides

Run the screenshot script against the assembled preview:

```bash
NODE_PATH=$HOME/node_modules node {skill-dir}/scripts/html/screenshot.mjs <deck-dir>/<deck-name>-preview.html
```

> **Note:** `NODE_PATH=$HOME/node_modules` is needed because Playwright is installed globally in the user's home directory, not in the skill repo.

This produces `<deck-dir>/_review/slide-1.png`, `slide-2.png`, etc.

## Step 2 — Launch Parallel Review Subagents

Launch **one Task subagent per slide**, all in parallel. Each subagent receives:

1. The screenshot image (via Read tool on the PNG file)
2. The slide fragment source (via Read tool on the HTML file)
3. The review checklist below

Use `subagent_type: "general"` for each.

### Subagent Prompt Template

For each slide N, launch a Task with this prompt:

````
You are reviewing slide {N} of an HTML presentation for visual quality issues.

## Your inputs

1. Read the screenshot image: `{deck-dir}/_review/slide-{N}.png`
2. Read the slide fragment source: `{deck-dir}/slides/slide-{N}.html`

## Review checklist

Look at the screenshot and check for these issues:

| # | Check | What to look for |
|---|-------|-------------------|
| 1 | **Content overflow** | Text or elements cut off at slide edges, content extending beyond the visible 1280×720 area |
| 2 | **Empty/blank areas** | Large unexpected white/empty spaces where content should be |
| 3 | **Broken layout** | Elements overlapping, misaligned columns, grid not forming properly |
| 4 | **Missing content** | Slide appears to have fewer items than expected from the HTML source |
| 5 | **Text readability** | Text too small to read, insufficient contrast against background |
| 6 | **Footer present** | Bottom of slide has the footer bar with text |
| 7 | **Title bar present** | Top of slide has the title bar (except cover slides which have a different layout) |
| 8 | **Dark slide contrast** | If background is dark: text is light, elements are visible |
| 9 | **Animation visibility** | If `.reveal` classes are used, verify that content is visible on the active slide (not stuck at opacity: 0 due to missing `.active` class on parent slide) |
| 10 | **Progress bar** | Progress bar visible at top of deck and updates on navigation |
| 11 | **Dead space** | If >60% of the content area appears visually empty (no cards, text, or images), flag as low-density. Intentional white space around a single centered visual is acceptable. |

## Your output

Return a JSON object with exactly this structure:

```json
{
  "slide": {N},
  "pass": true or false,
  "issues": [
    {
      "check": "content overflow",
      "severity": "high|medium|low",
      "description": "The bullet list extends below the footer, last 2 items are cut off",
      "suggestion": "Reduce font size or split content across two slides"
    }
  ]
}
```

If all checks pass, return `{"slide": {N}, "pass": true, "issues": []}`.

IMPORTANT:
- Be strict. If something looks even slightly off, flag it.
- Only flag issues you can actually SEE in the screenshot. Do not invent issues from the HTML alone.
- "severity" levels: high = content is lost/unreadable, medium = looks wrong but content is intact, low = minor aesthetic issue
````

## Step 3 — Collect Results and Fix

After all subagents return:

1. **Parse** the JSON results from each subagent
2. **Report** a summary table to the user:

```
Review complete — N slides checked

| Slide | Status | Issues |
|-------|--------|--------|
| 1     | ✓ pass |        |
| 2     | ✗ fail | Content overflow (high): bullet list cut off |
| 3     | ✓ pass |        |
```

3. **Auto-fix high-severity issues:**

   - Read the failing slide fragment
   - Fix the issue (reduce content, adjust layout, fix CSS in overrides.css)
   - Re-assemble the preview
   - Re-screenshot and re-review ONLY the fixed slides (launch subagents again for just those slides)

4. **Report medium/low issues** to the user without auto-fixing:

   > "Slide 5 has a minor alignment issue — the grid items are slightly uneven. Want me to fix this?"

5. **Limit review loops to 2 iterations.** If a slide still fails after 2 fix attempts, report it to the user and move on.

## Step 4 — Clean Up

After review is complete (all passes or user accepts):

```bash
rm -rf <deck-dir>/_review/
```

The `_review/` directory is temporary and should not persist.

## Presenting to User

After review completes:

> "Visual review complete — all N slides checked.
> [X slides passed, Y had issues (Z auto-fixed).]
>
> Ready to export or make further changes?"
