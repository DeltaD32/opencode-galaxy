# /// script
# requires-python = ">=3.10"
# ///
"""
parse_backlog_page.py — Extract Jira issue keys from Confluence page HTML.

Reads a Confluence page body (storage format HTML) from a JSON file and
extracts all Jira issue keys matching the given project key.

Usage:
    uv run scripts/parse_backlog_page.py --input-file page.json --project-key DX

Output:
    JSON array of {issue_key, summary, status} objects to stdout.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


class _JiraKeyExtractor(HTMLParser):
    """Extracts Jira issue keys and surrounding text from Confluence HTML."""

    def __init__(self, project_key: str) -> None:
        super().__init__()
        self._pattern = re.compile(rf"\b({re.escape(project_key)}-\d+)\b")
        self.found_keys: list[str] = []
        self._current_href: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            for name, value in attrs:
                if name == "href" and value:
                    match = self._pattern.search(value)
                    if match:
                        self.found_keys.append(match.group(1))
                    self._current_href = value

    def handle_data(self, data: str) -> None:
        for match in self._pattern.finditer(data):
            self.found_keys.append(match.group(1))


def extract_keys(html_body: str, project_key: str) -> list[str]:
    """Return deduplicated, naturally sorted Jira issue keys."""
    parser = _JiraKeyExtractor(project_key)
    parser.feed(html_body)
    seen: set[str] = set()
    unique: list[str] = []
    for key in parser.found_keys:
        if key not in seen:
            seen.add(key)
            unique.append(key)
    unique.sort(key=lambda k: (k.rsplit("-", 1)[0], int(k.rsplit("-", 1)[1])))
    return unique


def main() -> None:
    ap = argparse.ArgumentParser(description="Extract Jira keys from Confluence page HTML")
    ap.add_argument("--input-file", required=True, help="JSON file with page body (key: 'body')")
    ap.add_argument("--project-key", required=True, help="Jira project key (e.g. DX)")
    args = ap.parse_args()

    path = Path(args.input_file)
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(path.read_text(encoding="utf-8"))
    body = data.get("body") or data.get("content") or data.get("html") or ""
    if not body:
        print("WARNING: no body content found in input file", file=sys.stderr)

    keys = extract_keys(body, args.project_key)
    result = [{"issue_key": k} for k in keys]
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
