"""Agent registry — agents are DATA (Module F enabler).

For the foundation this loads from agents/<name>.md if present, else a small
built-in default. Later (Module F) this is backed by the `agents` table and the
Architect can create new ones autonomously.
"""
from __future__ import annotations
import os, pathlib

AGENTS_DIR = pathlib.Path(os.environ.get("JARVIS_AGENTS_DIR", "agents"))

# Minimal built-in defaults so the foundation runs before you author prompts.
_DEFAULTS = {
    "programming-expert": {
        "tools": ["read_file", "write_file", "bash"],
        "model": None,  # None -> JARVIS_MODEL default (claude-sonnet-4-6)
        "prompt": "You are a senior software engineer. Implement the assigned task by "
                  "editing only files within your file scope. Keep changes minimal and correct.",
    },
    "design-expert": {
        "tools": ["read_file", "write_file"],
        "model": None,
        "prompt": "You are a product/UX designer. Produce design artifacts (specs, tokens, "
                  "copy) within your file scope.",
    },
    "data-analyst": {
        "tools": ["read_file", "write_file", "bash"],
        "model": None,
        "prompt": "You are a data analyst. Analyze inputs and write findings within your file scope.",
    },
}


def available() -> list[str]:
    names = set(_DEFAULTS)
    if AGENTS_DIR.is_dir():
        names |= {p.stem for p in AGENTS_DIR.glob("*.md")}
    return sorted(names)


def get(name: str) -> dict:
    md = AGENTS_DIR / f"{name}.md"
    if md.is_file():
        # an agent .md is one consolidated system prompt (gateway constraint)
        return {"tools": _DEFAULTS.get(name, {}).get("tools", ["read_file", "write_file"]),
                "model": _DEFAULTS.get(name, {}).get("model"),
                "prompt": md.read_text()}
    if name in _DEFAULTS:
        return _DEFAULTS[name]
    # unknown agent -> generic safe default
    return {"tools": ["read_file", "write_file"], "model": None,
            "prompt": f"You are the {name}. Complete the assigned task within your file scope."}
