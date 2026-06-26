#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Sync sayings from the upstream bmw_sprueche repository into a local JSON snapshot."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_HOST = "cc-github.bmwgroup.net"
DEFAULT_OWNER = "markusfidorra"
DEFAULT_REPO = "bmw_sprueche"
SOURCE_FILES = ("README.md", "bmw_schulungen.md")
SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = SKILL_DIR / "references" / "quotes.json"


def fetch_file(*, host: str, owner: str, repo: str, file_path: str) -> str:
    """Fetch a raw file from GitHub using gh CLI."""
    command = [
        "gh",
        "api",
        "--hostname",
        host,
        f"repos/{owner}/{repo}/contents/{file_path}",
        "-H",
        "Accept: application/vnd.github.raw+json",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "unknown gh api error"
        raise RuntimeError(f"Failed to fetch {file_path}: {message}")
    return result.stdout


def slugify(text: str) -> str:
    """Return a stable slug for headings and IDs."""
    characters = []
    previous_dash = False
    for char in text.casefold():
        if char.isalnum():
            characters.append(char)
            previous_dash = False
        elif not previous_dash:
            characters.append("-")
            previous_dash = True
    return "".join(characters).strip("-")


_NON_QUOTE_PREFIXES = ("![", "[", "<", "---", "```", "|")

INCLUDED_SECTIONS = frozenset({"bmw-sprueche"})


def _looks_like_metadata(line: str) -> bool:
    """Return True for lines that are markdown formatting rather than quotes."""
    return any(line.startswith(prefix) for prefix in _NON_QUOTE_PREFIXES)


def parse_markdown(
    source_file: str,
    content: str,
    *,
    allowed_sections: frozenset[str] | None = None,
) -> list[dict[str, str]]:
    """Extract quotes from the simple markdown structure used in the source repo.

    When *allowed_sections* is given, only quotes whose slugified section name
    is in the set are kept.  Pass ``None`` to keep everything (useful in tests).
    """
    section = Path(source_file).stem
    quotes: list[dict[str, str]] = []
    ordinal = 0

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            heading = line.lstrip("#").strip()
            if heading:
                section = heading
            ordinal = 0
            continue

        if _looks_like_metadata(line):
            continue

        ordinal += 1

        if allowed_sections is not None and slugify(section) not in allowed_sections:
            continue

        quotes.append(
            {
                "id": f"{Path(source_file).stem}:{slugify(section)}:{ordinal:03d}",
                "text": line,
                "source_file": source_file,
                "section": section,
            }
        )

    return quotes


def build_snapshot(
    *,
    source_dir: Path | None = None,
    host: str = DEFAULT_HOST,
    owner: str = DEFAULT_OWNER,
    repo: str = DEFAULT_REPO,
) -> dict[str, object]:
    """Build the normalized snapshot from upstream files or a local source directory."""
    sayings: list[dict[str, str]] = []
    seen_texts: set[str] = set()

    for source_file in SOURCE_FILES:
        if source_dir is not None:
            source_path = source_dir / source_file
            if not source_path.is_file():
                raise FileNotFoundError(f"Source file not found: {source_path}")
            content = source_path.read_text(encoding="utf-8")
        else:
            content = fetch_file(host=host, owner=owner, repo=repo, file_path=source_file)

        for quote in parse_markdown(source_file, content, allowed_sections=INCLUDED_SECTIONS):
            if quote["text"] in seen_texts:
                continue
            seen_texts.add(quote["text"])
            sayings.append(quote)

    return {
        "source": {
            "host": host,
            "owner": owner,
            "repo": repo,
            "url": f"https://{host}/{owner}/{repo}",
            "files": list(SOURCE_FILES),
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "quotes": sayings,
    }


def write_snapshot(snapshot: dict[str, object], output_path: Path) -> None:
    """Write the snapshot to disk with stable formatting."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Path to the generated sayings snapshot (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        help="Read source markdown files from a local directory instead of fetching via gh api.",
    )
    parser.add_argument(
        "--hostname", default=DEFAULT_HOST, help=f"GitHub host (default: {DEFAULT_HOST})"
    )
    parser.add_argument(
        "--owner", default=DEFAULT_OWNER, help=f"Repository owner (default: {DEFAULT_OWNER})"
    )
    parser.add_argument(
        "--repo", default=DEFAULT_REPO, help=f"Repository name (default: {DEFAULT_REPO})"
    )
    return parser.parse_args()


def main() -> int:
    """Entry point."""
    args = parse_args()
    try:
        snapshot = build_snapshot(
            source_dir=args.source_dir,
            host=args.hostname,
            owner=args.owner,
            repo=args.repo,
        )
        write_snapshot(snapshot, args.output)
        print(f"Wrote {len(snapshot['quotes'])} sayings to {args.output}")
        return 0
    except (FileNotFoundError, RuntimeError) as error:
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
