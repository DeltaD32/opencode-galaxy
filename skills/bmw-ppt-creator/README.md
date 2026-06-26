# BMW Brand Skill

A custom skill that ensures brand consistency by applying styling patterns—either extracted from a user-provided PPT template or from pre-extracted BMW defaults—to all presentations and reports.

## What This Skill Does

This skill supports **two flows** for creating branded presentations and documents:

| Flow | When to Use | Style Source |
|------|-------------|--------------|
| **Template flow** | User provides a PPT template | Styles extracted at runtime via `extract_style_pattern.py` |
| **Default flow** | No template provided | Pre-extracted BMW brand assets in `references/` |

Both flows provide:
- **Color schemes**: From template extraction or official BMW palette
- **Typography**: Correct fonts, sizes, and formatting rules
- **Layout specifications**: Margins, positioning, slide dimensions
- **Logo handling**: Logos render from layout SmartArt — no manual overlay needed
- **Communication principles**: Top-down structure, pyramid principle

## Quick Start
I
### Step 1: Add Skill to Your Workspace

Clone or copy this skill folder into your VS Code workspace:

```bash
git clone git@cc-github.bmwgroup.net:yogita-sureshsuryawanshi/AIForPOs.git
```

### Step 2: Invoke the Skill

Reference the skill in your Copilot prompt. The AI will ask for two things:
1. **Template** — Do you want to provide a sample PPT template for styling?
2. **Department Code** — e.g., `DE-841`. Defaults to `Dept.` if not provided.

Based on your answers, the skill follows one of two flows:

---

## Flow A: Default Flow (No Template Provided)

Use this when you want standard BMW corporate styling and don't have a specific template.

### What you provide
- A topic / content description
- Department code (optional)

### What happens behind the scenes
1. The skill loads `Presentation1.pptx` as the base template
2. It reads `references/brand-styling-guide.md` for all styling rules
3. It generates your presentation using these pre-extracted defaults:

| Element | Default Value |
|---------|---------------|
| Primary Color | Ocean Blue `#035970` |
| Text Color | Black `#000000` on white backgrounds |
| Title Font | BMWGroupTN Condensed, 26pt, UPPERCASE |
| Body Font | BMWGroupTN Condensed, 18pt |
| Bullet | `▪` (small filled square) |
| Title Slide | `"Title \| Full Picture"` layout with BMW gradient JPEG background |
| Content Slide | `"Grid \| 1"` layout, white background |
| Logos | BMW Roundel (left) + GROUP wordmark (right) — rendered automatically from SmartArt in title layout |
| Footer | Master's built-in `FußzeileAU1` shape — updated with "Dept \| Date \| Topic" |
| Margins | 0.54" all sides, 16:9 aspect ratio |

### Example prompt (default flow)
```
Using bmw-brand-skill, create a presentation about Pros and Cons of OpenClaw.
Department code: DE-777.
```

### Key rules for default flow
- **Do NOT modify** `references/brand-styling-guide.md` — it is the authoritative default reference
- Title slides use the `"Title | Full Picture"` layout — **never draw a manual gradient rectangle**
- Logos render from SmartArt placeholders — **do NOT overlay PNG images**
- Footer uses the master slide's built-in shapes — **do NOT draw manual footer elements**

---

## Flow B: Template Flow (User Provides a PPT Template)

Use this when you have an existing BMW presentation whose look & feel you want to replicate for new content. This is the **recommended** flow for team-specific or event-specific styling.

### What you provide
- A topic / content description
- A `.pptx` template file (the "style source")
- Department code (optional)

### What happens behind the scenes

**Step 1 — Style Extraction:** The skill runs `extract_style_pattern.py` on your template to extract:
- Theme name and full color scheme (dk1, lt1, dk2, accent1–6, etc.)
- Major and minor fonts (resolves `+mj-lt` / `+mn-lt` references to actual font names)
- Title, body, and footer text properties from the slide master's `txStyles` (font size, color, casing, bullet characters)
- Slide layout names and placeholder positions (title, body, department badge, SmartArt logos)
- Slide dimensions and margins

**Step 2 — Guide Generation:** The extracted styling is written to `references/brand-styling-guide.template.md`. This file is regenerated each time a new template is provided. The default guide (`brand-styling-guide.md`) is **never modified**.

**Step 3 — Presentation Creation:** The new presentation is built by:
- Opening the user's template as the base (inheriting its masters, layouts, and theme)
- Deleting existing slides, keeping masters/layouts intact
- Creating new slides using the template's layout names
- Applying exact fonts, colors, sizes, and bullet characters from the extracted guide
- Updating the master footer text with department, date, and topic

**Step 4 — Validation:** The output is verified against `brand-styling-guide.template.md` for brand compliance.

### Example prompt (template flow)
```
Using bmw-brand-skill, create a presentation about SOGS for management.
Use 2024-12-11 JD All Hands Telematics_new.pptx as the style template.
Department code: DE-841.
Target audience: Management.
```

### Key rules for template flow
- Always run `extract_style_pattern.py` first — **do not guess styling from the template**
- Write extracted results to `brand-styling-guide.template.md` — **do not overwrite the default guide**
- Use the template's actual layout names (e.g., `"Grid | 1"`, `"Dunkel_Neutral_Teilung_1a"`) — don't assume default layout names
- If the template uses dark backgrounds, body text must be white (`#FFFFFF`), not black
- Title color, font, size, and casing come from the **extracted** master `titleStyle`, not the default guide
- Bullet character comes from the **extracted** master `bodyStyle`, not the default guide

### Running the extractor manually

```bash
cd bmw-brand-skill/bmw-brand-skill
source .venv/bin/activate
python extract_style_pattern.py "/path/to/your/template.pptx" /tmp/style_output.json
```

The JSON output contains font frequencies, text sizes, and colors found across all slides. Use this alongside the theme XML extraction (done by the AI) to populate the template guide completely.

## Folder Structure

```
bmw-brand-skill/
├── SKILL.md                    # Skill definition and instructions (dual-flow)
├── README.md                   # This file
├── Presentation1.pptx          # Default reference template
├── extract_style_pattern.py    # Style extractor for template flow
├── examples/
│   ├── create_anthropic_skills_presentation.py   # Default flow — Agent Skills topic
│   ├── create_latest_ai_models_presentation.py   # Default flow — Top 5 AI Models
│   ├── create_ai_for_pos_presentation.py          # Template flow — AI for Product Owners
│   └── create_sogs_management_presentation.py     # Template flow — SOGS for Management
└── references/
    ├── brand-styling-guide.md           # Default flow styling specs (from Presentation1.pptx)
    ├── brand-styling-guide.template.md  # Template flow styling specs (regenerated per template)
    ├── extracted-assets/                # Background images and logos
    │   ├── title-bg-default.jpeg        # Title slide background (default template)
    │   ├── title-bg-template.jpeg       # Title slide background (user template)
    │   ├── bmw-roundel-default.png      # BMW roundel (default template)
    │   ├── bmw-roundel-template.png     # BMW roundel (user template)
    │   ├── bmw-group-logo-default.png   # BMW GROUP wordmark (default template)
    │   ├── bmw-group-logo-template.png  # BMW GROUP wordmark (user template)
    │   └── slide1-objekt-14.emf         # EMF vector asset
    └── master-slide-assets/             # Theme XML, master slide definitions
        ├── slideMaster1.xml             # Master slide layout specs
        ├── theme1.xml                   # BMW Group 21 theme (colors, fonts)
        ├── image1.emf                   # EMF vector asset
        ├── image2.png                   # BMW roundel logo
        ├── image3.svg                   # SVG vector asset
        ├── image4.png                   # BMW wordmark
        ├── image5.svg                   # SVG vector asset
        └── image6.jpeg                  # JPEG image asset
```

## Brand Quick Reference (Default Flow)

These values apply when no user template is provided (see Flow A above). For the template flow (Flow B), values are extracted at runtime and written to `brand-styling-guide.template.md`.

| Element | Value |
|---------|-------|
| **Primary Color** | Ocean Blue `#035970` |
| **Text Color** | Black `#000000` |
| **Background** | White `#FFFFFF` (content); Picture placeholder with BMW gradient JPEG (title) |
| **Accent Colors** | Teal `#548D9E`, Blue-Gray `#85ACB9`, Ice Blue 3 `#ABC4CF`, Ice Blue 4 `#C8D7E0`, Ice Blue 5 `#DEE5EC`, Ice Blue 6 `#E8EBF1` |
| **Title Font** | BMWGroupTN Condensed (Arial fallback), 26pt, UPPERCASE |
| **Body Font** | BMWGroupTN Condensed (Arial fallback), 18pt |
| **Bullet** | `▪` (small filled square) |
| **Slide Dimensions** | 16:9 aspect ratio |
| **Margins** | 0.54" all sides |

---

## Usage Examples

### Default flow prompts

```
Using bmw-brand-skill, create a presentation about Pros and Cons of OpenClaw.
Department code: DE-777.
```

```
Using bmw-brand-skill, create a 3-slide status report:
1. Title slide: "Q1 2026 Telematics Update"
2. Progress slide with 4 bullet points
3. Next steps slide
Department code: DE-841
```

### Template flow prompts

```
Using bmw-brand-skill, create a presentation about SOGS for management.
Use 2024-12-11 JD All Hands Telematics_new.pptx as the style template.
Department code: DE-841.
Target audience: Management.
```

```
Using bmw-brand-skill, create a presentation on AI for POs.
Use PSPO-AI-Essentials_Overview.pptx as the style template.
Department code: DE-841.
You can use data from this Confluence page: "What the heck AI"
```

### Code generation prompt

```
Using the examples in bmw-brand-skill/examples/, create a Python
script that generates a presentation about OTL Collector features
with proper BMW branding.
```

### Example Scripts

The `examples/` folder contains ready-to-run Python scripts for reference:

| Script | Flow | Topic | Template Used |
|--------|------|-------|---------------|
| `create_anthropic_skills_presentation.py` | Default | Agent Skills (Anthropic) | `Presentation1.pptx` |
| `create_latest_ai_models_presentation.py` | Default | Top 5 AI Models 2026 | `Presentation1.pptx` |
| `create_ai_for_pos_presentation.py` | Template | AI for Product Owners | `PSPO-AI-Essentials_Overview.pptx` |
| `create_sogs_management_presentation.py` | Template | SOGS for Management | `JD All Hands Telematics_new.pptx` |

Run any script from the skill root:

```bash
cd bmw-brand-skill/bmw-brand-skill
source .venv/bin/activate
python examples/create_openclaw_pros_cons_presentation.py
```

Each script demonstrates:
- Loading the correct template (default `Presentation1.pptx` or user-provided)
- Deleting existing slides while keeping masters/layouts
- Creating slides with proper layout names
- Applying brand fonts, colors, sizes, and bullet characters
- Updating the master footer via `_update_master_footer()`
- Saving the output `.pptx`

## Communication Principles

The skill enforces BMW communication standards:

1. **Top-Down Structure**: Answer first, then provide supporting evidence
2. **Pyramid Principle**: Start with conclusion, back up with data
3. **Conciseness**: Get to the point, eliminate fluff
4. **Action-Oriented**: Every section drives toward decisions

## Important Do's and Don'ts

### Do's ✅
- **Do** provide a department code — it appears on the title slide badge and in the footer
- **Do** provide a `.pptx` template if you want team/event-specific styling
- **Do** let the AI run `extract_style_pattern.py` before creating a template-flow presentation
- **Do** check the output `.pptx` visually — open it in PowerPoint to verify fonts, colors, and layouts

### Don'ts ❌
- **Don't** manually edit `references/brand-styling-guide.md` — it is the pre-extracted default
- **Don't** draw manual gradient rectangles on title slides — the layout already has a JPEG background
- **Don't** overlay PNG logo images — logos render automatically from SmartArt in the title layout
- **Don't** draw manual footer lines, text boxes, or page numbers — the master slide handles those
- **Don't** guess styling from a template — always extract it first

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Wrong colors applied | Check the active guide (`brand-styling-guide.md` for default, `brand-styling-guide.template.md` for template flow) |
| Title slide has no background | Use `"Title \| Full Picture"` layout — it has a picture placeholder with the BMW gradient JPEG. Never draw a manual gradient rectangle. |
| Fonts not matching | Default flow uses BMWGroupTN Condensed (Arial fallback); template flow uses extracted fonts |
| Fonts show as `+mj-lt` / `+mn-lt` | These are theme font references. Run theme XML extraction to resolve them to actual font names (e.g., `BMWGroupTN Condensed`). |
| Body text invisible on dark slide | Template uses dark layouts (e.g., `Dunkel_*`). Body text should be white `#FFFFFF`, not black. Check the template guide. |
| Wrong bullet character | Default flow uses `▪` (small filled square); template flow uses the extracted bullet style — always check `brand-styling-guide.template.md`. |
| Logo not appearing | Logos render from SmartArt in the `"Title \| Full Picture"` layout. Do NOT overlay PNGs — this causes duplicates. |
| Layout issues | Verify the active guide's dimensions and margins |
| Template extraction failed | Ensure `python-pptx` is installed in the `.venv` and the PPT file is valid |

## Related Resources

- [BMW Group Brand Portal](https://brand.bmwgroup.com) (internal)
- `references/brand-styling-guide.md` — Default flow specifications (from `Presentation1.pptx`)
- `references/brand-styling-guide.template.md` — Template flow specifications (regenerated per template)
- `extract_style_pattern.py` — Style extraction script (template flow)
- `examples/` — 4 Python scripts covering both default and template flows

## Prerequisites

The skill requires a Python virtual environment with `python-pptx`:

```bash
cd bmw-brand-skill/bmw-brand-skill
python -m venv .venv
source .venv/bin/activate
pip install python-pptx
```

## Support

For questions or issues with this skill, contact the TSP team or create an issue in the repository.
