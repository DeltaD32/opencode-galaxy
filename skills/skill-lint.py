#!/usr/bin/env python3
"""
skill-lint.py — Post-install lint checker for OpenCode skills.

Checks every SKILL.md in ~/.opencode/skills/ (or a single named skill) for:
  1. Inline Python/Bash code blocks longer than INLINE_LIMIT lines
  2. Missing .py module when a code block exceeds INLINE_LIMIT

Exit codes:
  0 — all clean
  1 — one or more warnings (non-fatal, but should be addressed)

Usage:
  # Lint all installed skills
  python3 ~/.opencode/skills/skill-lint.py

  # Lint a single skill after install
  python3 ~/.opencode/skills/skill-lint.py <skill-name>
  python3 ~/.opencode/skills/skill-lint.py rag
  python3 ~/.opencode/skills/skill-lint.py dor-jira-updater
"""

import re
import sys
import pathlib

SKILLS_DIR = pathlib.Path.home() / ".opencode/skills"
INLINE_LIMIT = 20          # code block lines above this count as "large"
WARN_COLOUR  = "\033[33m"  # yellow
OK_COLOUR    = "\033[32m"  # green
RESET        = "\033[0m"

# Languages that indicate executable logic (not just config / JSON examples)
EXECUTABLE_LANGS = {"python", "python3", "py", "bash", "sh", "zsh"}


def count_code_blocks(text: str) -> list[dict]:
    """Return list of {lang, line_count, start_line, ignored} for every fenced block.

    A block is ignored (excluded from lint warnings) if the preceding non-blank
    line contains '<!-- skill-lint: ignore -->' or '# skill-lint: ignore'.
    """
    blocks = []
    lines = text.splitlines()
    in_block = False
    lang = ""
    block_start = 0
    block_lines = 0
    ignore_next = False

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not in_block:
            # Check for ignore directive on this line (before the fence)
            if "skill-lint: ignore" in stripped:
                ignore_next = True
                continue
            m = re.match(r"^```(\w*)", stripped)
            if m:
                in_block = True
                lang = m.group(1).lower()
                block_start = i
                block_lines = 0
                # If the opening fence itself contains an ignore marker
                if "skill-lint: ignore" in stripped:
                    ignore_next = True
            elif stripped:
                # Non-blank, non-fence line — reset ignore_next unless it was
                # set on the immediately preceding line (allow one blank between)
                pass
        else:
            if stripped == "```":
                blocks.append({
                    "lang": lang,
                    "line_count": block_lines,
                    "start_line": block_start,
                    "ignored": ignore_next,
                })
                in_block = False
                ignore_next = False
            else:
                block_lines += 1

    return blocks


def has_py_module(skill_dir: pathlib.Path) -> bool:
    """Return True if any .py file exists directly in skill_dir (not in subdirs)."""
    return any(skill_dir.glob("*.py"))


def lint_skill(skill_dir: pathlib.Path) -> list[str]:
    """Return list of warning strings for this skill. Empty = clean."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return []

    text = skill_md.read_text(encoding="utf-8")
    blocks = count_code_blocks(text)

    warnings = []
    large_executable = [
        b for b in blocks
        if b["lang"] in EXECUTABLE_LANGS
        and b["line_count"] > INLINE_LIMIT
        and not b.get("ignored", False)
    ]

    for b in large_executable:
        warnings.append(
            f"  ⚠  Large inline {b['lang']} block ({b['line_count']} lines) "
            f"at line {b['start_line']}"
        )

    if large_executable and not has_py_module(skill_dir):
        warnings.append(
            f"  ⚠  No .py module found in {skill_dir.name}/ — "
            f"consider extracting to a module and updating SKILL.md to import it"
        )

    return warnings


def lint_all(target: str | None = None) -> int:
    """Lint all skills or a single named skill. Returns exit code."""
    if target:
        candidates = [SKILLS_DIR / target]
        if not candidates[0].exists():
            print(f"Error: skill directory not found: {candidates[0]}")
            return 1
    else:
        candidates = sorted(
            d for d in SKILLS_DIR.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        )

    any_warnings = False
    for skill_dir in candidates:
        warnings = lint_skill(skill_dir)
        if warnings:
            any_warnings = True
            print(f"{WARN_COLOUR}[WARN] {skill_dir.name}{RESET}")
            for w in warnings:
                print(w)
        else:
            # Only print OK for single-skill runs (avoids flooding output)
            if target:
                print(f"{OK_COLOUR}[OK]   {skill_dir.name}{RESET}")

    if not any_warnings:
        if not target:
            print(f"{OK_COLOUR}All skills clean — no large inline code blocks found.{RESET}")
        return 0
    else:
        print(
            f"\n{WARN_COLOUR}Hint:{RESET} Extract large code blocks to a .py module "
            f"co-located in the skill directory, then replace the inline block in "
            f"SKILL.md with a short import snippet:\n"
            f"  import sys, pathlib\n"
            f"  sys.path.insert(0, str(pathlib.Path.home() / \".opencode/skills/<name>\"))\n"
            f"  from <module> import <function>\n"
        )
        return 1


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(lint_all(target))
