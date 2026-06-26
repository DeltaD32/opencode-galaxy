---
name: ppt-style-registry
version: "1.0.0"
description: >
  Manage a local registry of presentation styles. Clone the visual style of any
  .pptx file into the registry for reuse, and select a registered style when
  building new presentations. The default style is always BMW CI.
  Trigger on: "clone style", "save style", "list styles", "use [style name] style",
  "what styles are available", "style from pptx", "extract presentation style".
metadata:
  authors:
    - Generated for QTE2362 opencode setup
  tags:
    - powerpoint
    - presentation
    - style
    - brand
    - registry
    - clone
---

# PPT Style Registry Skill

## Purpose

The **PPT Style Registry** is a local store of cloned presentation styles. Any `.pptx` file can be cloned into the registry — its fonts, colors, slide dimensions, layout names, and background assets are extracted and saved. When building a new presentation, the user picks a style from the registry (or accepts the default BMW CI style).

---

## Registry Location

```
~/.config/opencode/ppt-styles/
├── registry.json               ← Index of all saved styles
├── clone_style.py              ← Style cloner script
├── list_styles.py              ← Registry lister script
└── <slug>/                     ← One folder per cloned style
    ├── style.json              ← Machine-readable full style profile
    ├── brand-guide.md          ← Human-readable brand guide (used by agents)
    ├── title-bg.jpeg           ← Extracted title background (if found)
    └── source.pptx             ← Copy of original file
```

The **default style** is always `bmw-ci` (BMW Corporate Identity). It is pre-registered at bootstrap and points to the brand guide in `~/.opencode/skills/bmw-ppt-creator/references/brand-styling-guide.md`.

---

## Workflows

### Workflow A — Clone a Style from a .pptx File

**Trigger:** User says something like:
- "Clone the style from this deck"
- "Save the style of this presentation"
- "Extract style from `quarterly_report.pptx`"

**Steps:**

1. **Confirm the source file.** Ask the user to provide the path to the `.pptx` file if not already given.

2. **Ask for a style name.** Suggest using the filename stem as default.
   > "What would you like to call this style? (default: `[filename stem]`)"

3. **Optionally ask for a description** if the user seems to have a clear intent:
   > "Any short description? (e.g. 'ACME Corp dark theme' — press Enter to skip)"

4. **Run the cloner script:**
   ```bash
   python ~/.config/opencode/ppt-styles/clone_style.py \
     "<path/to/source.pptx>" \
     --name "<Style Name>" \
     --description "<description>"
   ```

5. **Report results** to the user:
   - Style slug and directory
   - Detected primary font and dominant color
   - Number of layouts found
   - Path to the generated `brand-guide.md`
   - Confirmation that the style is now available for selection

6. **Offer immediate use:**
   > "Would you like to create a presentation using this new style now?"

**Example output to user:**
```
✓ Style "ACME Dark Theme" cloned successfully
  Slug:         acme-dark-theme
  Font:         Calibri, 24pt titles / 14pt body
  Primary color: #1E3A5F
  Layouts:      12
  Saved to:     ~/.config/opencode/ppt-styles/acme-dark-theme/

You can now use this style by saying "use the ACME Dark Theme style" when
creating a presentation.
```

---

### Workflow B — List Available Styles

**Trigger:** User says:
- "What styles are available?"
- "List my saved presentation styles"
- "Show me the style registry"

**Steps:**

1. Run the lister script (table view):
   ```bash
   python ~/.config/opencode/ppt-styles/list_styles.py
   ```

2. Or get the user-facing menu directly:
   ```bash
   python ~/.config/opencode/ppt-styles/list_styles.py --menu
   ```
   The `--menu` flag outputs the exact prompt block to show users, with live primary colors, font names, dark/light layout counts, and palette hints.

3. Always highlight that **BMW CI is the default** (used when no style is chosen).

4. Offer to show details for any specific style:
   ```bash
   python ~/.config/opencode/ppt-styles/list_styles.py --slug <slug>
   ```

---

### Workflow C — Resolve a Style Selection

**Used by:** `bmw-ppt-creator`, `bmw-pptx`, `bmw-slides` when starting a new presentation.

This workflow is invoked internally by the presentation skills to resolve which style to use.

**Input:** A user-provided style preference string (or empty/none for default).

**Logic:**

```
if user_preference is empty or "default" or "bmw" or "bmw ci":
    resolved_slug = "bmw-ci"
else:
    run list_styles.py --json
    fuzzy-match user_preference against names and slugs in registry
    if single match found with confidence ≥ 0.7:
        resolved_slug = match.slug
    elif multiple matches:
        ask user to confirm which one
    else:
        tell user no match found, offer to list or clone
```

**Output:** `resolved_slug`, `style_dir`, `brand_guide_path`

**Loading the resolved style:**
- Read `<style_dir>/brand-guide.md` for the human-readable guide
- Read `<style_dir>/style.json` for machine-readable details
- If `is_builtin == true` (bmw-ci): point to `~/.opencode/skills/bmw-ppt-creator/references/brand-styling-guide.md`
- Pass the `brand_guide_path` to the presentation skill for use as the primary style reference

---

### Workflow D — Style Selection Prompt (at Presentation Start)

**Used by:** All presentation skills, before beginning the storyline phase.

**When to ask:**
- Always ask once, at the very start of any "create presentation" request
- Skip if the user has already named a style in their original request

**Prompt template:**

Run `python ~/.config/opencode/ppt-styles/list_styles.py --menu` and copy its output verbatim. The script generates the correct menu from the live registry, including:
- Primary brand color per style (e.g. `#F69954` for dark-theme decks, `#035970` for BMW CI)
- Active font name
- Tags: dark layout count, custom title bg flag, supporting palette
- `[default]` marker on BMW CI

Example output:
```
🎨 Which presentation style would you like to use?

  1. BMW CI [default] — #035970, BMWGroupTN Condensed  [BMW Group standard, light backgrounds]
  2. Aiconic Grand Prix — #F69954, BMWGroupTN Condensed  [20/21 dark layouts, custom title bg, palette: #035970]

   Press Enter or type "1" for the default, or pick a number / name.
   Have a .pptx not listed? Share its path and I'll clone it first.
```

---

## Style Profile Schema (`style.json`)

```jsonc
{
  "slide_dimensions": {
    "width_in": 13.333,
    "height_in": 7.5,
    "aspect_ratio": "16:9",
    "width_emu": 12192000,
    "height_emu": 6858000
  },
  "typography": {
    "primary_font": "BMWGroupTN Condensed",
    "title_font": "BMWGroupTN Condensed",
    "title_size_pt": 26.0,
    "title_size_max_pt": 40.0,      // largest layout override (e.g. full-bleed title slides)
    "body_size_pt": 18.0,
    "footer_size_pt": 7.0,
    "title_color_hex": "#FFFFFF",   // actual rendered title color (from txStyles)
    "title_color_scheme": "bg1",
    "body_color_hex": "#000000",
    "dominant_colors": ["#F69954", "#035970"],  // noise-filtered; excludes pure black/white and CONFIDENTIAL reds
    "all_fonts": { "BMWGroupTN Condensed": 211 },
    "all_sizes_pt": { "18.0": 88, "26.0": 32 },
    "all_colors": { "#F69954": 44, "#035970": 31 }
  },
  "theme_colors": {},
  "layouts": [
    {
      "name": "Title Slide",
      "placeholder_count": 3,
      "placeholders": [
        { "idx": 0, "type": "CENTER_TITLE", "name": "Title", "left_in": 0.5, "top_in": 2.1, "width_in": 12.3, "height_in": 1.5 }
      ]
    }
  ],
  "slide_backgrounds": [
    { "slide": 1, "bg_color": null },
    { "slide": 2, "bg_color": "#F5F5F5" }
  ],
  "extraction_stats": {
    "slide_shape_records": 180,
    "master_shape_records": 40,
    "layout_shape_records": 120,
    "total_slides": 12,
    "total_layouts": 8
  }
}
```

---

## Registry Schema (`registry.json`)

```jsonc
{
  "version": 1,
  "styles": {
    "bmw-ci": {
      "slug": "bmw-ci",
      "name": "BMW CI (Default)",
      "description": "Official BMW Group Corporate Identity — Ocean Blue #035970, BMWGroupTN Condensed.",
      "source_file": "Presentation1.pptx",
      "source_sha256": null,
      "cloned_at": "2026-02-01T00:00:00+00:00",
      "style_dir": "/Users/QTE2362/.opencode/skills/bmw-ppt-creator",
      "brand_guide_path": "/Users/QTE2362/.opencode/skills/bmw-ppt-creator/references/brand-styling-guide.md",
      "is_builtin": true,
      "slide_dimensions": { "width_in": 13.333, "height_in": 7.5, "aspect_ratio": "16:9" },
      "typography_summary": {
        "primary_font":  "BMWGroupTN Condensed",
        "title_font":    "BMWGroupTN Condensed",
        "title_size_pt": 26.0,
        "body_size_pt":  18.0,
        "primary_color": "#035970",   // meaningful brand color for menu display
        "dominant_color": "#035970",  // backward-compat alias for primary_color
        "palette": ["#035970", "#548D9E", "#85ACB9"]
      },
      "theme_summary": {
        "scheme_name": "BMW Group 21",
        "dk2": "#035970", "accent1": "#548D9E",
        "major_font": "BMWGroupTN Condensed", "minor_font": "BMWGroupTN Condensed"
      },
      "layout_stats": { "total": 20, "dark": 0, "light": 20 },
      "has_title_bg": false
    },
    "custom-dark-theme": {
      "slug": "custom-dark-theme",
      "name": "Custom Dark Theme",
      "description": "Dark branded corporate template",
      "source_file": "template.pptx",
      "is_builtin": false,
      "has_title_bg": true,
      "typography_summary": {
        "primary_font":  "BMWGroupTN Condensed",
        "title_font":    "BMWGroupTN Condensed",
        "title_size_pt": 26.0, "body_size_pt": 18.0,
        "primary_color": "#F69954",   // extracted from dark layout backgrounds
        "palette": ["#F69954", "#035970"]
      },
      "layout_stats": { "total": 21, "dark": 20, "light": 1 }
    }
  }
}
```

---

## Dependency

- `python-pptx` must be installed: `pip install python-pptx`
- `Pillow` is optional (used for thumbnail generation): `pip install Pillow`

---

## Error Handling

| Situation | Response |
|-----------|----------|
| Source `.pptx` not found | Ask user to confirm path |
| `python-pptx` not installed | `pip install python-pptx` |
| Style slug already exists | Warn, ask to confirm overwrite (add `--overwrite` flag) |
| Registry is empty (only bmw-ci) | Offer to clone from a user file |
| No match for user style preference | List all registered styles; ask user to pick by number |
| Built-in style cloning attempted | Explain it's protected; suggest cloning under a new name |
