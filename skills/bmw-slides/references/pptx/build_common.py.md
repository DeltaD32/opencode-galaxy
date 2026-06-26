# build_common.py — Shared Boilerplate Template

This file is the **template** for `build_common.py`, the shared boilerplate that every delivery build uses. The orchestrator writes this file first, then each sub-agent's `slide_NN.py` runs after it via `exec()`.

**All variables and functions defined here are available to every `slide_NN.py` script.**

## Template

The orchestrator must replace the placeholder values marked with `{...}` before writing the file:

| Placeholder | Value |
|---|---|
| `{assets_dir}` | Absolute path to the `assets/` folder inside the deck root |
| `{output_path}` | Absolute path to the output `.pptx` file inside the deck root |
| `{department}` | Department string from the Pre-flight answer (empty string `""` if user left blank) |

```python
"""
build_common.py — Shared boilerplate for delivery sub-agent build.
All variables and helpers defined here are available to slide_NN.py scripts
via exec() chaining in build_assemble.py.
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu, Cm
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
from pptx.oxml.ns import qn
from lxml import etree
from datetime import date
from PIL import Image
import os
import sys
import yaml

# ── Paths ──────────────────────────────────────────────────────────────────────
# Resolve skill directory: works for both ~/.copilot/ (GitHub Copilot) and ~/.claude/ (Claude/OpenCode)
for _candidate in ["~/.copilot/skills/bmw-slides", "~/.claude/skills/bmw-slides"]:
    _expanded = os.path.expanduser(_candidate)
    if os.path.isdir(_expanded):
        SKILL_DIR = _expanded
        break
else:
    raise FileNotFoundError("Skill directory not found in ~/.copilot/ or ~/.claude/")
TEMPLATE  = os.path.join(SKILL_DIR, "template.pptx")
CONFIG_PATH = os.path.join(SKILL_DIR, "config.yaml")
ASSETS    = "{assets_dir}"       # absolute path to assets/ folder — inside <topic-slug>/assets/
OUTPUT    = "{output_path}"      # absolute path to output .pptx — inside <topic-slug>/

# ── Import pptx_lib (all building-block helpers) ──────────────────────────────
sys.path.insert(0, SKILL_DIR)
from pptx_lib import *

# ── Config ─────────────────────────────────────────────────────────────────────
with open(CONFIG_PATH) as f:
    cfg = yaml.safe_load(f)

# DEPARTMENT is set from the Pre-flight user answer — the orchestrator writes the literal
# value here so this deck's build is self-contained and config.yaml is never mutated.
# The orchestrator replaces {department} with the actual value before writing this file.
DEPARTMENT      = "{department}"
_footer_raw     = cfg.get("footer", "")
# Build footer: prefer a prompt-provided department over config.yaml default.
_footer_dept    = DEPARTMENT or cfg.get("department", "")
_footer_author  = cfg.get("author", "")
FOOTER          = f"{_footer_dept} | {date.today().isoformat()} | {_footer_author}".strip(" |")
CONFIDENTIALITY = cfg.get("confidentiality", "CONFIDENTIAL")

# ── Presentation setup ─────────────────────────────────────────────────────────
prs = Presentation(TEMPLATE)

# Delete all existing slides from template
while len(prs.slides._sldIdLst) > 0:
    rId = prs.slides._sldIdLst[0].get(
        "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    )
    prs.part.drop_rel(rId)
    del prs.slides._sldIdLst[0]


# Apply config to slide master
def _set_para_text_preserve_runs(para, text):
    """Set paragraph text without destroying run-level formatting."""
    runs = para.runs
    if runs:
        runs[0].text = text
        for extra in runs[1:]:
            extra._r.getparent().remove(extra._r)
    else:
        para.text = text

master = prs.slide_masters[0]
for shape in master.shapes:
    if not shape.has_text_frame:
        continue
    if shape.name == "FußzeileAU1":
        _set_para_text_preserve_runs(shape.text_frame.paragraphs[0], FOOTER)
    elif shape.name == "Textfeld 3" and CONFIDENTIALITY is not None:
        _set_para_text_preserve_runs(shape.text_frame.paragraphs[0], CONFIDENTIALITY)

# ── prs is now ready — slide_NN.py scripts add slides below ───────────────────
```

## Available to sub-agents after exec

After `build_common.py` is executed, these names are in scope:

**Modules:** `os`, `sys`, `yaml`, `etree`, `qn`, `Image`, `date`, `Presentation`, `Inches`, `Pt`, `Emu`, `Cm`, `PP_ALIGN`, `MSO_ANCHOR`, `MSO_SHAPE`, `RGBColor`

**Constants:** `SKILL_DIR`, `TEMPLATE`, `CONFIG_PATH`, `ASSETS`, `OUTPUT`, `DEPARTMENT` (literal string from Pre-flight — never read from `config.yaml` at runtime), `FOOTER`, `CONFIDENTIALITY`

**From `pptx_lib` (via `from pptx_lib import *`):** All constants (`COLOR_PRIMARY`, `COLOR_ACCENT`, `COLOR_ACCENT2`, `COLOR_SECONDARY`, `CARD_BG`, `CARD_BORDER`, `WHITE`, `DARK`, `PALETTE`, `FREE_LEFT`, `FREE_TOP`, `FREE_WIDTH`, `FREE_HEIGHT`, `FREE_BOTTOM`, `FREE2_TOP`, `FREE2_HEIGHT`, `FREE2_BOTTOM`), the `free_area(layout_idx)` function (returns correct free-area bounds per layout), the `ContentGrid` class for grid-based layouts (see Rules 22-24 in sub-agent-context.md), and all helper functions (see `./references/pptx/sub-agent-context.md` for the full API reference).

**The presentation object:** `prs` — template loaded, example slides deleted, master config applied. Ready for `prs.slides.add_slide(...)`.
