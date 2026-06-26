---
name: bmw-ppt-creator
description: A custom skill that ensures brand consistency by applying styling patterns—either extracted from a user-provided PPT template or from pre-extracted BMW defaults—to all presentations and reports.
metadata:
  author: Yogita-suresh Suryawanshi <Yogita-suresh.Suryawanshi@bmw.de>
  version: "1.0.1"
  tags:
    - poco
    - powerpoint
    - presentation
    - ppt
---

# BMW Brand Skill

## Purpose

This skill creates presentations based on a user-provided PPT template. If no template is provided, it uses the default `Presentation1.pptx` and its pre-extracted brand references.

## Quick Reference

**Default flow** — Pre-extracted brand assets in `references/` folder:
- `references/brand-styling-guide.md` - Complete color scheme, typography, and layout specs
- `references/master-slide-assets/` - Logo files, theme XML, and master slide definitions

**Template flow** — Generated at runtime from user's PPT:
- `references/brand-styling-guide.template.md` - Auto-extracted guide (created by `extract_style_pattern.py`)
- User's template masters, layouts, and assets take precedence

## Skill Execution Instructions

**CRITICAL: When this skill is invoked, ALWAYS follow these steps:**

### Step 0: Style Selection (Registry-Aware)

Before creating any presentation, resolve the style to use via the **PPT Style Registry**.

#### Step 0a — Query the registry and get the live menu

```bash
python ~/.config/opencode/ppt-styles/list_styles.py --menu
```

#### Step 0b — Present the style menu to the user

Copy the output of `list_styles.py --menu` verbatim. It shows each style's primary color, font, layout character (dark/light), and palette — so the user can make a meaningful choice. Example:
```
🎨 Which presentation style would you like to use?

  1. BMW CI [default] — #035970, BMWGroupTN Condensed  [BMW Group standard, light backgrounds]
  2. <Name> — <primary_color>, <font>  [<tags>]

   Press Enter or type "1" for the default, or pick a number / name.
   Have a .pptx not listed? Share its path and I'll clone it first.
```

#### Step 0c — Resolve the selection

- **Empty input / "1" / "BMW" / "BMW CI" / "default"** → use `bmw-ci` (built-in)
- **Number or name matching a registered style** → use that style's `brand_guide_path`
- **User provides a new `.pptx` file path** → clone it first:
  ```bash
  python ~/.config/opencode/ppt-styles/clone_style.py \
    "<path/to/file.pptx>" --name "<name>" --description "<description>"
  ```
  Then use the newly created style.

#### Step 0d — Load the resolved brand guide

- **BMW CI (built-in):** use `references/brand-styling-guide.md` in this skill folder  
- **Any other style:** read `<style_dir>/brand-guide.md` as the primary style reference  
  AND read `<style_dir>/style.json` for layout names, colors, and font specifics
- **Font family constraint (all styles):** Check `brand-guide.md` → "Font Family Rule" section. Only BMW Group typefaces are permitted (`BMWGroupTN Condensed`, `BMW Group Condensed`, `BMW Group`). Never substitute Arial, Calibri, or other system fonts.

#### Step 0e — Ask for Department Code

Ask for the exact department code/text for the Department badge on the title slide.  
Use **"Dept."** if the user does not provide a value.

### Step 1: Load Brand Reference

The brand reference is determined by the style resolved in Step 0:

- **BMW CI flow (default):** Use `references/brand-styling-guide.md` in this skill folder.
    - **Color codes:** Ocean Blue `#035970` (primary), accent colors, custom brand palette
    - **Typography:** BMWGroupTN Condensed (Arial fallback), 26pt titles (UPPERCASE), 18pt body
    - **Layout specs:** 16:9 slides, 0.54" margins, title positioning
    - **Logos:** Roundel (left), GROUP text (right) on title slides only — rendered by layout SmartArt, no manual overlay
- **Registry style flow:** Read `<style_dir>/brand-guide.md` and `<style_dir>/style.json` as resolved in Step 0d.
- **Legacy template flow (user drops a .pptx in chat):** clone it via the registry first (Step 0c), then follow the registry style flow.

### Step 1.1: Extract Style Patterns (If New .pptx Provided)

If the user provides a new `.pptx` file that is NOT already in the registry, clone it first:

```bash
python ~/.config/opencode/ppt-styles/clone_style.py \
  "<path/to/file.pptx>" \
  --name "<style name>" \
  --description "<short description>"
```

The clone script writes:
- `<registry_dir>/<slug>/style.json` — machine-readable full style profile
- `<registry_dir>/<slug>/brand-guide.md` — human-readable brand guide
- `<registry_dir>/<slug>/title-bg.jpeg` — extracted title background (if present)

**Do NOT overwrite `references/brand-styling-guide.md`** (the BMW CI default). Cloned styles always go into `~/.config/opencode/ppt-styles/<slug>/`.

### Step 2: Apply Styling Patterns

Apply the exact styling patterns to any deliverables created:
- **Registry style flow:** Use `<style_dir>/brand-guide.md` and `<style_dir>/style.json`.
- **BMW CI flow (default):** Use `references/brand-styling-guide.md`.
- **CRITICAL SLIDE STRUCTURE RULE: EXACTLY 1 TITLE SLIDE ONLY** — Every presentation must have exactly one title slide as the first slide. All subsequent slides must be content slides using appropriate content layouts. **Never create multiple title slides.**
- **Title slide layout:** Always use `"Title | Full Picture"` layout — it has a built-in picture placeholder (idx=21) with the BMW gradient background JPEG. **Never draw a manual gradient rectangle.**
- **Content slide layout:** Use `"Grid | 1"` or similar content layouts. Clear inherited placeholders if adding custom shapes.
- **Logos:** SmartArt placeholders in the title layout (idx=24 roundel, idx=23 group) render logos automatically. **Do NOT overlay PNG images** — this causes duplicate logos.
- **Footer:** The master slide has built-in footer shapes (`FußzeileAU1` for dept/date/author, `SeitenzahlAU1` for page numbers, `BMW Group Trennlinie` separator line). Update the master's `FußzeileAU1` text with the department, date, and topic. **Do NOT draw manual footer elements** (lines, text boxes, page numbers) — these duplicate the master's inherited footer.
- Follow layout specifications for margins and positioning.

### Code Patterns (both flows)

When generating Python code for presentations, use these patterns:

#### Footer — update the master's built-in shape (do NOT draw manual elements)

```python
def _update_master_footer(prs, footer_text):
    """Update the master slide's built-in FußzeileAU1 footer text."""
    for master in prs.slide_masters:
        for shape in master.shapes:
            if shape.name == 'FußzeileAU1' or shape.name == 'Fu\u00dFzeileAU1':
                for run in shape.text_frame.paragraphs[0].runs:
                    run.text = ''
                shape.text_frame.paragraphs[0].runs[0].text = footer_text

# Call after loading the template:
_update_master_footer(prs, "DE-841 | February 2026 | Topic Name")
```

#### Logos — rendered automatically by SmartArt

The title layout's SmartArt placeholders (idx=24, idx=23) render the BMW logos automatically. No additional code is needed for logos.

### Step 3: Validate Brand Compliance

Before finalizing, verify against the active brand guide:
- **BMW CI flow:** Validate against `references/brand-styling-guide.md`.
- **Registry style flow:** Validate against `<style_dir>/brand-guide.md` and `<style_dir>/style.json`.

---

## Brand Visual Style (Pre-Extracted)

**Default flow only:** This section applies only when no template is provided. If a template is provided, use the extracted template guide instead.

| Element | Value |
|---------|-------|
| Primary Color | Ocean Blue `#035970` |
| Text Color | Black `#000000` |
| Background | White `#FFFFFF` (content), Gradient (title) |
| Accent Colors | Teal `#548D9E`, Blue-Gray `#85ACB9`, Cyan `#079EDA` |
| Title Font | BMWGroupTN Condensed , 26pt, UPPERCASE |
| Body Font | BMWGroupTN Condensed , 18pt |
| Bullet Character | ▪ (small black square) |

### Title Slide Specifics

**Default flow only:** Use these specifics only for the default template. For user templates, follow the extracted template guide.

| Element | Value |
|---------|-------|
| **Layout Name** | `"Title | Full Picture"` (has built-in JPEG background in picture placeholder) |
| Background | Picture placeholder (idx=21) with BMW gradient JPEG — **do NOT draw a manual rectangle** |
| Title Placeholder | `ctrTitle` — 40pt UPPERCASE white, y ≈ 4.2" |
| Subtitle Placeholder | `subTitle` (idx=1) — 20pt UPPERCASE white, y ≈ 5.86" |
| Department Badge | `body` placeholder (idx=22) — bottom-right, Ocean Blue fill, 18pt white text |
| Logo Areas | SmartArt placeholders (idx=24 roundel, idx=23 group) — render automatically, **no PNG overlay needed** |

> **Key:** Always use the `"Title | Full Picture"` layout via `add_slide(layout)`. The layout's picture placeholder already contains the BMW gradient background image. Never draw a `MSO_SHAPE.RECTANGLE` with a gradient fill — that ignores the template's built-in background.

---

## Slide Structure Patterns

Reference the correct guide based on the resolved style:

- **BMW CI flow:** Reference `references/brand-styling-guide.md`.
- **Registry style flow:** Reference `<style_dir>/brand-guide.md` and `<style_dir>/style.json`. The patterns below are BMW CI defaults; replace with values from the resolved style's brand guide.

| Pattern | BMW CI Flow | Registry Style Flow |
|---------|-------------|---------------------|
| **Title slide format** | Gradient background, text placement, department badge | As defined in `brand-guide.md` for that style |
| **Content slide layouts** | White background, Ocean Blue titles, bullet formatting | As defined in `brand-guide.md` for that style |
| **Diagram and flowchart styling** | Brand colors, shapes, connectors | Use style's dominant color palette |
| **Bullet point treatment** | ▪ character, 18pt, black text | Use style's extracted bullet character, font, size |
| **Footer format** | Master slide's built-in footer (`FußzeileAU1`) — update text, don't draw manual elements | Use style's footer pattern |

---

## Communication Principles

### 1. Top-Down Structure
- Answer first, then provide supporting evidence
- Lead with the conclusion

### 2. Pyramid Principle
- Start with the main conclusion
- Back up with supporting data and analysis

### 3. Conciseness Over Completeness
- Get to the point immediately
- Eliminate fluff and unnecessary content

### 4. Action-Oriented
- Every section should drive toward decisions or recommendations
- Include clear next steps

---

## Deliverable Guidelines

### For PowerPoint Presentations

1. **EXACTLY ONE TITLE SLIDE RULE** - Every presentation must have exactly one title slide as slide 1. All subsequent slides must use content layouts (Grid, Two Content, etc.). **Never create multiple title slides.**
2. **Follow master slide layout** from the correct guide:
   - **Default flow:** `references/brand-styling-guide.md`
   - **Template flow:** `references/brand-styling-guide.template.md`
3. **One key message per slide** - Slide title = the takeaway
4. **Use diagrams liberally** - Flowcharts, process visuals, frameworks
5. **Minimize bullet points** - Maximum 5 per slide
6. **Include visual hierarchy** - Icons, color blocks, connecting arrows
7. **Match styling** - Colors, fonts, and footer style from the active brand guide (default or template-specific)

### For Word Documents (Reports)

1. **Executive Summary** - 1-page maximum, answer + 3-5 key points
2. **Structure** - Clear section headers with numbering
3. **Visuals** - Embed tables and charts using colors from the active brand guide
4. **Formatting** - Consistent with the active brand color scheme (default or template-extracted)
5. **Recommendations** - Bulleted, specific and actionable

---

## Workflow Summary

```
┌──────────────────────────────────────────────────────────────────────┐
│               BMW PPT-CREATOR SKILL WORKFLOW (v2 — Registry-Aware)   │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  0a. QUERY     →   python list_styles.py                             │
│                                                                      │
│  0b. MENU      →   Present style choices to user                     │
│                    (BMW CI is always the default)                    │
│                                                                      │
│  0c. RESOLVE   →   BMW CI → use references/brand-styling-guide.md   │
│                    Other  → read <style_dir>/brand-guide.md          │
│                    New    → clone_style.py first, then read guide    │
│                                                                      │
│  0d. DEPT CODE →   Ask for department badge text (default: "Dept.")  │
│                                                                      │
│  1. LOAD       →   Read the resolved brand guide + style.json        │
│                                                                      │
│  2. APPLY      →   Use extracted guide values:                       │
│                    colors, fonts, layout names, footer pattern       │
│                    Logos: inherit from layout SmartArt               │
│                    Footer: update master's FußzeileAU1              │
│                                                                      │
│  3. VALIDATE   →   Validate against the resolved brand guide         │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Reference Files

### Default Flow Resources (in `references/` folder)

Used when no user template is provided:

| Resource | Path | Description |
|----------|------|-------------|
| **Brand Guide (default)** | `references/brand-styling-guide.md` | Complete color scheme, typography, layout specs for `Presentation1.pptx` |
| **Title Background** | `references/extracted-assets/title-bg-default.jpeg` | BMW gradient background JPEG (from picture placeholder) |
| **Theme XML** | `references/master-slide-assets/theme1.xml` | Full color definitions |
| **Master Slide** | `references/master-slide-assets/slideMaster1.xml` | Layout specifications |

### Template Flow Resources (generated at runtime)

Created when a user provides a PPT template:

| Resource | Path | Description |
|----------|------|-------------|
| **Brand Guide (template)** | `references/brand-styling-guide.template.md` | Auto-generated guide extracted from the user's template |
| **Style Extractor** | `extract_style_pattern.py` | Script that extracts fonts, colors, sizes, and dimensions from any PPT |
| **Title Background (template)** | `references/extracted-assets/title-bg-template.jpeg` | Background image from template's picture placeholder |

> **Note:** `brand-styling-guide.template.md` is regenerated each time a new template is provided. It does not overwrite the default guide.

### Example Scripts (in `examples/` folder)

Python scripts demonstrating how to generate BMW-branded presentations:
- `examples/create_anthropic_skills_presentation.py` - Agent Skills topic example (default flow)
- `examples/create_latest_ai_models_presentation.py` - Top 5 AI Models example (default flow)

### Original Source

**Master Reference Deck:** `Presentation1.pptx` - Default source file from which brand assets were pre-extracted. Used only in the default flow.

---

## Quality Checklist

Before finalizing any deliverable, verify against the correct flow:

### Common Checks (both flows)

- [ ] **EXACTLY ONE TITLE SLIDE** - Presentation has exactly one title slide (slide 1) and all other slides use content layouts
- [ ] Correct brand guide was identified and consulted
- [ ] Department badge text matches user input (or "Dept." default)
- [ ] Layout follows correct aspect ratio with proper margins
- [ ] Content follows communication principles (pyramid principle, conciseness)

### BMW CI Flow Checks

- [ ] `references/brand-styling-guide.md` was used as the reference
- [ ] Color scheme matches BMW palette (Ocean Blue `#035970` primary)
- [ ] Typography uses BMWGroupTN Condensed (26pt titles, 18pt body)
- [ ] Titles are UPPERCASE with BMW brand colors
- [ ] Logos render from layout SmartArt (idx=24 roundel, idx=23 group) — no PNG overlay added
- [ ] Title slide uses `"Title | Full Picture"` layout (not a blank layout with manual gradient)
- [ ] Picture placeholder (idx=21) provides the background — no manual rectangle drawn
- [ ] Department badge uses body placeholder (idx=22) with Ocean Blue fill (not Night Blue)
- [ ] Bullet character is ▪ (small filled square)
- [ ] Footer uses master's built-in `FußzeileAU1` shape — no manual lines/textboxes drawn
- [ ] Master footer text updated with "Department | Date | Topic" via `_update_master_footer()`

### Registry Style Flow Checks

- [ ] `<style_dir>/brand-guide.md` was loaded and consulted
- [ ] `<style_dir>/style.json` was read for layout names, colors, font specifics
- [ ] Color scheme matches the cloned style's extracted dominant colors
- [ ] Typography matches the cloned style's extracted fonts and sizes
- [ ] Slide dimensions match those in `style.json` → `slide_dimensions`
- [ ] Title slide layout matches the layout name detected from source file
- [ ] Footer pattern follows the cloned style's footer spec
- [ ] Master footer text updated via `_update_master_footer()` if applicable
