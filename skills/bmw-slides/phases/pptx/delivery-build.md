# Delivery Step 2 — Build PPTX

This is the build step of the internal delivery pipeline. Runs after `./phases/delivery-assets.md` and flows directly into `./phases/pptx/delivery-polish.md` without a user gate.

**Source of truth: the storyline markdown file.** Before generating any code, read the storyline file from disk with the Read tool. Do not rely on the in-memory storyline — the user may have edited the file after Phase 1.

```
STORYLINE_PATH = /path/to/<deck-name>-storyline.md
Read this file now. Parse each ## Slide N block: layout, title, content, image, notes.
```

Before code generation, validate the storyline file:

```bash
uv run python ./scripts/pptx/validate_storyline.py /path/to/<deck-name>-storyline.md
```

If validation fails, stop and fix the storyline first.

The build step uses a **sub-agent architecture**: one file per slide, all assembled at the end. This avoids generating a single monolithic script (which gets slow and error-prone for decks with more than a few slides).

## Build directory structure

The deck root is `<chosen-base>/<topic-slug>/` (resolved during Pre-flight — topic slug derived from the user's topic phrase). All artefacts live inside it:

```
<chosen-base>/
└── <topic-slug>/                     ← deck root (named from user's topic)
    ├── assets/                       ← sourced images (from asset sourcing step)
    ├── build/                        ← delivery build files only
    │   ├── build_common.py           ← shared boilerplate (orchestrator writes this)
    │   ├── slide_01.py               ← slide 1 code (sub-agent writes this)
    │   ├── slide_02.py               ← slide 2 code (sub-agent writes this)
    │   ├── ...
    │   └── build_assemble.py         ← exec chain + save (orchestrator writes this)
    ├── review/                       ← self-review JPEGs (never mix with assets/)
    ├── <topic-slug>-storyline.md     ← storyline (from Phase 1)
    └── <topic-slug>.pptx             ← final output (never inside build/)
```

**Rules:**
- The `.pptx` output file is always at deck root level — **never** inside `build/` or `assets/`.
- `assets/` contains only sourced images — never build scripts or review artefacts.
- `review/` contains only JPEG renders — created by `self-review.sh`.
- `build/` contains only Python build scripts — no images, no final PPTX.

## Step 1: Write `build_common.py`

Write the shared boilerplate using the template from `./references/pptx/build_common.py.md`. Replace the placeholder values:

- `{assets_dir}` → absolute path to the `assets/` folder
- `{output_path}` → absolute path to the output `.pptx` file

This file defines all imports, constants, colors, helpers, loads the template, deletes example slides, and applies master config. After execution, `prs` is ready for slides to be added.

## Step 2: Launch sub-agents for each slide (bounded parallel)

For each slide in the storyline, launch a **Task sub-agent** (type: `general`) that writes a single `slide_NN.py` file.

Use bounded parallelism to reduce thrash and timeouts:

- `MAX_PARALLEL_SLIDE_AGENTS = 4` (default)
- `MAX_PARALLEL_SLIDE_AGENTS = 6` only for very stable environments

Process slides in batches of up to `MAX_PARALLEL_SLIDE_AGENTS`, wait for each batch to complete, then launch the next batch.

Each sub-agent prompt must contain:

1. **The task:** "Write a python-pptx script for slide N and save it to `{path}`."
2. **The slide's storyline block** (copy the `## Slide N` section from the storyline file)
3. **The layout's placeholder info** (copy the relevant section from `./references/pptx/template-layouts.md`)
4. **The consolidated context file:** "Read `{skill_dir}/references/pptx/sub-agent-context.md` for available variables, the full pptx_lib API reference, layout reference, and all code generation rules." — where `{skill_dir}` is the absolute skill directory (see below).

### Sub-agent prompt template

Use this exact template, filling in the `{...}` placeholders:

```
You are a python-pptx code generator. Your job is to write a single Python script
that adds ONE slide to an existing presentation.

## Task

Write a Python script and save it to: {build_dir}/slide_{NN}.py
The script will be executed via exec() after build_common.py, so all imports,
constants, colors, helpers, and the `prs` object are already in scope.
Do NOT import anything or redefine any variable from build_common.py.
Do NOT call prs.save() — that happens in the assembler.

## Slide storyline

{paste the ## Slide N block from the storyline file}

## Layout reference

{paste the relevant layout section from ./references/pptx/template-layouts.md}

## Context

Read `{skill_dir}/references/pptx/sub-agent-context.md` for:
- Available variables and helpers (all in scope from build_common.py)
- Full pptx_lib API reference (importable functions for shapes, cards, tables, etc.)
- Layout reference (all placeholder indices and positions)
- All code generation rules you MUST follow

## Output

Write the script to {build_dir}/slide_{NN}.py using the Write tool.
The script should:
1. Add exactly one slide to prs
2. Fill all content from the storyline
3. Call remove_empty_placeholders(slide) at the end if using custom shapes
4. Call set_notes(slide, "...") with the notes from the storyline
5. NOT import anything, NOT call prs.save(), NOT redefine helpers/constants

Reply with the file path you wrote to. Nothing else.
```

**Important:** Do not launch an unbounded number of slide agents at once. Use bounded batches with the concurrency cap above.

**`{skill_dir}` placeholder:** Use the directory this skill is installed in. Typical values:

- GitHub Copilot: `~/.copilot/skills/bmw-slides`
- Claude / OpenCode: `~/.claude/skills/bmw-slides`

Check which exists and fill the placeholder accordingly.

## Step 3: Write `build_assemble.py`

After all sub-agents complete, write the assembler script:

```python
"""
build_assemble.py — Execute common + all slide scripts in order, then save.
"""
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

BUILD_DIR = "{build_dir}"

# Execute shared boilerplate (defines prs, helpers, constants)
exec(open(os.path.join(BUILD_DIR, "build_common.py")).read())

# Execute each slide script in order
for f in sorted(glob.glob(os.path.join(BUILD_DIR, "slide_*.py"))):
    print(f"  Executing {os.path.basename(f)} ...")
    exec(open(f).read())

prs.save(OUTPUT)
print(f"\nSaved: {OUTPUT}")
print(f"Slides: {len(prs.slides)}")

# ── Post-save think-cell cleanup ───────────────────────────────────────────────
# The BMW template is built with think-cell, which embeds OLE objects, tag data,
# and graphicFrames in every slide layout. python-pptx re-serialises layouts on
# save, so these artefacts survive into the output and corrupt the file in
# Microsoft PowerPoint (LibreOffice is unaffected). We strip them directly from
# the saved ZIP — that alone is enough for PowerPoint to open without a repair
# dialog. Do not re-serialise through LibreOffice afterwards: LO normalises the
# custom trapezoid geometry on the department-badge placeholder (layout 0/19,
# idx 22) into a plain rectangle.
print("\nStripping think-cell artefacts from saved file...")

_PML_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_SLIDE_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide"
_TC_TAG_PREFIXES = ("THINKCELL", "MIO_CHANGETRACKING")


def _strip_think_cell(path):
    tmp = path + ".tmp"

    # Pass 1: build slide rId re-mapping (fix ordering gap left by template deletion)
    _slide_rid_map = {}
    with zipfile.ZipFile(path, "r") as zin:
        rels_root = etree.fromstring(zin.read("ppt/_rels/presentation.xml.rels"))
        non_slide = [r for r in rels_root if r.get("Type") != _SLIDE_TYPE]
        slide_rels = [r for r in rels_root if r.get("Type") == _SLIDE_TYPE]
        slide_rels.sort(key=lambda r: int(re.search(r"slide(\d+)\.xml$", r.get("Target", "slide0.xml")).group(1)))
        max_rid = max((int(re.match(r"rId(\d+)$", r.get("Id", "rId0")).group(1)) for r in non_slide if re.match(r"rId(\d+)$", r.get("Id", "rId0"))), default=0)
        for i, r in enumerate(slide_rels, start=1):
            _slide_rid_map[r.get("Target")] = (r.get("Id"), f"rId{max_rid + i}")
    rid_to_target = {n: t for t, (o, n) in _slide_rid_map.items()}
    old_to_new = {o: n for t, (o, n) in _slide_rid_map.items()}

    # Pass 2: write cleaned ZIP
    with zipfile.ZipFile(path, "r") as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)

            if re.match(r"ppt/slideLayouts/_rels/slideLayout\d+\.xml\.rels$", item.filename):
                root = etree.fromstring(data)
                for r in list(root):
                    if r.get("Id") == "rId3":
                        root.remove(r)
                data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)

            elif re.match(r"ppt/slideLayouts/slideLayout\d+\.xml$", item.filename):
                root = etree.fromstring(data)
                for spTree in root.iter(f"{{{_PML_NS}}}spTree"):
                    for gf in list(spTree):
                        if gf.tag != f"{{{_PML_NS}}}graphicFrame":
                            continue
                        for oleObj in gf.iter(f"{{{_PML_NS}}}oleObj"):
                            if oleObj.get(f"{{{_REL_NS}}}id") == "rId3":
                                spTree.remove(gf)
                                break
                data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)

            elif re.match(r"ppt/tags/tag\d+\.xml$", item.filename):
                root = etree.fromstring(data)
                for t in list(root):
                    if t.tag == f"{{{_PML_NS}}}tag" and any(t.get("name", "").startswith(p) for p in _TC_TAG_PREFIXES):
                        root.remove(t)
                data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)

            elif item.filename == "ppt/_rels/presentation.xml.rels":
                root = etree.fromstring(data)
                non_slide_rels = [r for r in root if r.get("Type") != _SLIDE_TYPE]
                new_slide_rels = [r for r in root if r.get("Type") == _SLIDE_TYPE]
                new_slide_rels.sort(key=lambda r: int(re.search(r"slide(\d+)\.xml$", r.get("Target", "slide0.xml")).group(1)))
                for child in list(root):
                    root.remove(child)
                for r in non_slide_rels:
                    root.append(r)
                for tgt, (o_rid, n_rid) in sorted(_slide_rid_map.items(), key=lambda x: int(re.search(r"slide(\d+)\.xml$", x[0]).group(1))):
                    for r in new_slide_rels:
                        if r.get("Target") == tgt:
                            r.set("Id", n_rid)
                            root.append(r)
                            break
                data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)

            elif item.filename == "ppt/presentation.xml":
                root = etree.fromstring(data)
                for sld_id in root.iter(f"{{{_PML_NS}}}sldId"):
                    old = sld_id.get(f"{{{_REL_NS}}}id")
                    if old in old_to_new:
                        sld_id.set(f"{{{_REL_NS}}}id", old_to_new[old])
                for sldIdLst in root.iter(f"{{{_PML_NS}}}sldIdLst"):
                    slides_sorted = sorted(list(sldIdLst), key=lambda el: int(re.search(r"slide(\d+)\.xml$", rid_to_target.get(el.get(f"{{{_REL_NS}}}id", ""), "slide0.xml")).group(1)))
                    for child in list(sldIdLst):
                        sldIdLst.remove(child)
                    for child in slides_sorted:
                        sldIdLst.append(child)
                data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)

            zout.writestr(item, data)

    os.replace(tmp, path)


_strip_think_cell(OUTPUT)
print("  Done.")
```

Do **not** re-serialise through LibreOffice afterwards: LO normalises placeholder geometry and destroys the custom trapezoid on the department badge (layout 0/19, placeholder 22). The python-side think-cell strip is sufficient for PowerPoint to open without a repair dialog.

## Step 4: Run the assembler

```bash
uv run python {build_dir}/build_assemble.py
```

If a slide script fails, fix only that slide's file and re-run the assembler. You do NOT need to regenerate all slides.

## Integration with Sourced Assets

In each `slide_NN.py`, reference downloaded assets by their local path using the `ASSETS` constant from `build_common.py`:

```python
# Title slide background (layout 0, picture placeholder idx 21)
fill_placeholder_image(slide, 21, os.path.join(ASSETS, "title_bg.jpg"))

# Picture Right layout (layout 14, picture placeholder idx 12)
fill_placeholder_image(slide, 12, os.path.join(ASSETS, "diagram.jpg"))

# Free-area image placement (layout 12)
add_image_preserved_ratio(slide, os.path.join(ASSETS, "icon.png"),
    target_left, target_top, target_width, target_height)
```

**Never** use raw `slide.placeholders[idx].insert_picture()` — it silently fails when placeholders lose their type after template manipulation. Always use `fill_placeholder_image()`.

## Fixing a single slide

If the user reports an issue with one slide (via text or screenshot), or if self-review finds a problem:

1. Identify which `slide_NN.py` needs fixing
2. Regenerate **only** that slide file (re-launch one sub-agent, or edit the file directly)
3. Re-run `uv run python {build_dir}/build_assemble.py`
4. Selective re-review: `bash ./scripts/pptx/self-review.sh /path/to/output.pptx --only N` (only the fixed slide)

You do NOT need to regenerate all slides. This is the key advantage of the sub-agent architecture.

## Self-Review after Build

After running the assembler, **always** render and review before continuing to the polish step.

### First review: contact sheet scan

```bash
bash ./scripts/pptx/self-review.sh /path/to/output.pptx --scan
```

Read `review/contact.jpg` (one image with all slides in a 2-column grid). Scan for obvious problems:

- Completely blank slides or empty content areas
- Wrong layout (image placeholder without image shows blank box)
- Grossly misaligned or overlapping content

If the contact sheet looks clean, skip individual reads and continue the delivery loop.

> **Important:** All review images are JPEG. Read `slide-01.jpg`, `slide-02.jpg`, etc. — **never** `.png`.

### Detailed review (if needed)

If the contact sheet reveals issues, or if `montage` is not installed:

```bash
bash ./scripts/pptx/self-review.sh /path/to/output.pptx
```

Read **2-3 consecutive `slide-NN.jpg` files per Read call** (they are ~50-80 KB each at 100 DPI). Do NOT read files marked SKIP. For each slide, check:

- Placeholder text visible ("Click to add Text") → placeholder not filled
- Text overflow / cut off at edges
- Empty slides or blank content areas
- Wrong layout (e.g. image placeholder without image shows blank box)
- Bottom conclusions do not appear as tiny footer text (if present, they should be banner/box style)
- Footer and "CONFIDENTIAL" label present on every slide

### Fixing and selective re-review

After fixing a slide, **only re-review the changed slides:**

```bash
# Re-run assembler
uv run python {build_dir}/build_assemble.py
# Re-review only the fixed slides (e.g. slides 3 and 7)
bash ./scripts/pptx/self-review.sh /path/to/output.pptx --only 3,7
```

Read only the re-rendered slides. Do NOT re-read all slides.

## Build/Polish Inner Loop

This step runs internally. Do not stop for a separate user approval.

1. Ensure assets were sourced internally using the rules in `./phases/delivery-assets.md` (relevant slides only) before build.
2. Use one slide agent per slide (parallel) so each slide runs in bounded context. Treat each run as fresh context/thread.
3. Use `./scripts/pptx/fastmode_orchestrator.py` as the state owner for issue routing:

   - write `issues_NN.json` per slide + `issues_summary.json`
   - route ownership: structural failures -> `build`, polish failures -> `polish`
   - if both fail for a slide, apply fixes in order `build -> polish`

   ```bash
   uv run python ./scripts/pptx/fastmode_orchestrator.py \
     --storyline /path/to/<deck>-storyline.md \
     --build-pptx /path/to/build-output.pptx \
     --final-pptx /path/to/final-output.pptx \
     --issues-dir /path/to/issues
   ```

4. For each changed slide `N`, run the inner loop:
   - build/update `slide_NN.py` and run assembler
   - structural gate (mandatory): `uv run python ./scripts/pptx/check_slide_structure.py --pptx /path/to/build-output.pptx --slide N --layout X`
   - run slide-scoped polish for `N`: `uv run python build/build_polish.py --only N`
   - polish gate (mandatory): `uv run python ./scripts/pptx/check_slide_polish.py --pptx /path/to/final-output.pptx --slide N`
   - render/review only that slide: `bash ./scripts/pptx/self-review.sh /path/to/final.pptx --only N`
5. After all slides are clean, run one collection pass (full polish consistency sweep).
6. Run one final full-deck `--scan`.
7. Continue to the polish step (`./phases/pptx/delivery-polish.md`) for final polish/QA handoff.

Reference: `./references/delivery.md`.

## Delivery Completion Message

After the assembler succeeds and QA passes, **always** end with a completion message in this exact format:

```
✅  Deck ready — [N] slides · BMW CI · MN-12

📄  [<topic-slug>.pptx](<topic-slug>.pptx)
📁  [Open folder](file:///absolute/path/to/<topic-slug>/)

Deck layout:
| # | Title | Visual |
|---|-------|--------|
| 1 | ...   | ...    |
...
```

**Clickable link rules:**
- The folder link uses `file://` URI scheme: `file:///absolute/path/to/<topic-slug>/` (three slashes on macOS/Linux, `file:///C:/...` on Windows).
- Render it as a Markdown link so the terminal / OpenCode UI makes it clickable: `[Open folder](file:///path/to/folder/)`.
- Always link to the **topic folder** (deck root), not to the `.pptx` file directly — the user can then browse `assets/`, `build/`, and `review/` from there.
- Also render the `.pptx` filename as a relative Markdown link for direct-open convenience.
- If the path contains spaces, percent-encode them (`%20`) in the URI but show the human-readable path in the link label.

Example for a deck at `/Users/QTE2362/Library/CloudStorage/OneDrive-BMWGroup/opencode-vs-copilot/`:

```
✅  Deck ready — 10 slides · BMW CI · MN-12

📄  [opencode-vs-copilot.pptx](file:///Users/QTE2362/Library/CloudStorage/OneDrive-BMWGroup/opencode-vs-copilot/opencode-vs-copilot.pptx)
📁  [Open folder](file:///Users/QTE2362/Library/CloudStorage/OneDrive-BMWGroup/opencode-vs-copilot/)
```
