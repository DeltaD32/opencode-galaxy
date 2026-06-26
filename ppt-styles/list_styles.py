#!/usr/bin/env python3
"""
ppt-style-list — list all styles in the local registry.

Usage:
  python list_styles.py [--json] [--slug <slug>]

Options:
  --json          Output raw JSON
  --slug SLUG     Show details for a single style
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REGISTRY_FILE = Path.home() / ".config" / "opencode" / "ppt-styles" / "registry.json"


def load_registry() -> dict:
    if not REGISTRY_FILE.exists():
        return {"version": 1, "styles": {}}
    return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))


def _color_swatch(hex_color: str | None) -> str:
    """Return a simple text representation of a color."""
    if not hex_color:
        return "—"
    return hex_color


def _layout_summary(entry: dict) -> str:
    stats = entry.get("layout_stats", {})
    if not stats:
        return "—"
    dark  = stats.get("dark", 0)
    light = stats.get("light", 0)
    total = stats.get("total", dark + light)
    if dark > 0 and light > 0:
        return f"{dark}🌑 {light}⬜ / {total} layouts"
    elif dark > 0:
        return f"all dark ({total} layouts)"
    elif light > 0:
        return f"all light ({total} layouts)"
    return f"{total} layouts"


def _font_short(font_name: str | None) -> str:
    """Shorten a font name for display."""
    if not font_name:
        return "—"
    # "BMWGroupTN Condensed" → "BMWGroupTN Condensed" (already short enough)
    # "BMW Group Condensed" → "BMW Group Condensed"
    return font_name


def _menu_line(i: int, entry: dict) -> str:
    """One-line menu entry for the style-selection prompt shown to users."""
    typo     = entry.get("typography_summary", {})
    color    = typo.get("primary_color") or typo.get("dominant_color") or "—"
    font     = _font_short(typo.get("title_font") or typo.get("primary_font"))
    stats    = entry.get("layout_stats", {})
    dark     = stats.get("dark", 0)
    total    = stats.get("total", 0)
    has_bg   = entry.get("has_title_bg", False)
    builtin  = " [default]" if entry.get("is_builtin") else ""

    # Build tags list for right-hand descriptors
    tags = []
    if dark > 0:
        tags.append(f"{dark}/{total} dark layouts")
    if has_bg:
        tags.append("custom title bg")
    palette  = typo.get("palette", [])
    others   = [c for c in palette if c != color][:2]
    if others:
        tags.append(f"palette: {', '.join(others)}")
    # If no meaningful tags yet, add a descriptor
    if not tags:
        if entry.get("is_builtin"):
            tags.append("BMW Group standard, light backgrounds")
        else:
            tags.append("BMW CI–derived, light backgrounds")

    tag_str = f"  [{', '.join(tags)}]" if tags else ""

    return (f"  {i}. {entry['name']}{builtin} — "
            f"{color}, {font}{tag_str}")


def main() -> None:
    parser = argparse.ArgumentParser(description="List available presentation styles.")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--slug", default="", help="Show full details for a specific style slug")
    parser.add_argument("--menu", action="store_true",
                        help="Output the style-selection menu as shown to users")
    args = parser.parse_args()

    registry = load_registry()
    styles = registry.get("styles", {})

    if not styles:
        print("No styles registered yet.")
        print(f"\nTo clone a style:  python {Path(__file__).parent}/clone_style.py <file.pptx> --name 'My Style'")
        return

    if args.json:
        if args.slug:
            entry = styles.get(args.slug)
            if not entry:
                print(f"Style '{args.slug}' not found.")
                return
            print(json.dumps(entry, indent=2))
        else:
            print(json.dumps(styles, indent=2))
        return

    if args.menu:
        # Output the exact menu block that presentation skills show users
        style_list = list(styles.values())
        if len(style_list) == 1:
            e = style_list[0]
            typo = e.get("typography_summary", {})
            color = typo.get("primary_color") or typo.get("dominant_color") or "—"
            font  = _font_short(typo.get("title_font") or typo.get("primary_font"))
            print(f"🎨 Style: {e['name']} (default) — {color}, {font}")
            print(f"")
            print(f"   Have a .pptx you'd like to match the style of instead?")
            print(f"   Share the file path and I'll clone its style first.")
        else:
            print("🎨 Which presentation style would you like to use?")
            print("")
            for i, entry in enumerate(style_list, 1):
                print(_menu_line(i, entry))
            print("")
            print("   Press Enter or type \"1\" for the default, or pick a number / name.")
            print("   Have a .pptx not listed? Share its path and I'll clone it first.")
        return

    if args.slug:
        entry = styles.get(args.slug)
        if not entry:
            print(f"Style '{args.slug}' not found.")
            return
        print(f"\nStyle: {entry['name']} [{entry['slug']}]")
        print(f"  Description:   {entry['description']}")
        print(f"  Cloned at:     {entry.get('cloned_at', '—')}")
        print(f"  Source file:   {entry.get('source_file', '—')}")
        print(f"  Directory:     {entry.get('style_dir', '—')}")
        print(f"  Has title bg:  {entry.get('has_title_bg', False)}")
        dims = entry.get("slide_dimensions", {})
        print(f"  Dimensions:    {dims.get('width_in')}\" × {dims.get('height_in')}\" ({dims.get('aspect_ratio')})")
        typo = entry.get("typography_summary", {})
        print(f"  Font:          {typo.get('title_font') or typo.get('primary_font', '—')}")
        print(f"  Title size:    {typo.get('title_size_pt', '—')}pt")
        print(f"  Body size:     {typo.get('body_size_pt', '—')}pt")
        print(f"  Primary color: {typo.get('primary_color') or typo.get('dominant_color', '—')}")
        palette = typo.get("palette", [])
        if palette:
            print(f"  Palette:       {', '.join(palette)}")
        stats = entry.get("layout_stats", {})
        if stats:
            print(f"  Layouts:       {_layout_summary(entry)}")
        return

    # Table view
    print(f"\n{'#':<4} {'Slug':<30} {'Name':<30} {'Font':<25} {'Primary Color':<12} {'Layouts'}")
    print("-" * 120)
    for i, (slug, entry) in enumerate(styles.items(), 1):
        typo    = entry.get("typography_summary", {})
        builtin = " [default]" if entry.get("is_builtin") else ""
        color   = typo.get("primary_color") or typo.get("dominant_color") or "—"
        font    = _font_short(typo.get("title_font") or typo.get("primary_font") or "—")
        print(
            f"{i:<4} {slug:<30} {(entry['name'] + builtin):<30} "
            f"{font:<25} {color:<12} {_layout_summary(entry)}"
        )
    print(f"\n{len(styles)} style(s) available.")
    print(f"\nDefault style: bmw-ci  (used when no style is specified)")
    print(f"To clone a new style:  python {Path(__file__).parent}/clone_style.py <file.pptx> --name 'My Style'")
    print(f"Style menu (as shown to users):  python {Path(__file__).parent}/list_styles.py --menu")


if __name__ == "__main__":
    main()
