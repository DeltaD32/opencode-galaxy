#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Select one BMW saying from the local snapshot, preferring light context matches."""

from __future__ import annotations

import argparse
import fcntl
import json
import random
import re
import secrets
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SNAPSHOT = SKILL_DIR / "references" / "quotes.json"
DEFAULT_HISTORY = Path.home() / ".copilot" / "state" / "bmw-wisdom-history.json"
DEFAULT_HISTORY_SIZE = 40
DEFAULT_RELEVANCE_BIAS = 0.45
TOKEN_PATTERN = re.compile(r"[0-9A-Za-zÄÖÜäöüß]+")
TOKEN_ALIASES = {
    "pr": {"pull", "request"},
}
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "bei",
    "das",
    "dem",
    "den",
    "der",
    "die",
    "do",
    "ein",
    "eine",
    "einen",
    "einer",
    "eines",
    "es",
    "for",
    "have",
    "i",
    "im",
    "in",
    "is",
    "it",
    "mit",
    "now",
    "of",
    "on",
    "the",
    "to",
    "und",
    "wir",
    "with",
    "zu",
}


def tokenize(text: str) -> set[str]:
    """Tokenize free-form text for lightweight keyword matching."""
    tokens = {
        token
        for token in TOKEN_PATTERN.findall(text.casefold())
        if len(token) > 1 and token not in STOPWORDS
    }
    expanded_tokens = set(tokens)
    for token in tokens:
        expanded_tokens.update(TOKEN_ALIASES.get(token, set()))
    return expanded_tokens


def load_snapshot(snapshot_path: Path) -> dict[str, object]:
    """Load the quotes snapshot from disk."""
    if not snapshot_path.is_file():
        raise FileNotFoundError(
            f"Snapshot file not found: {snapshot_path}. Run sync_sayings.py to create it."
        )
    return json.loads(snapshot_path.read_text(encoding="utf-8"))


def load_history(history_path: Path) -> list[str]:
    """Load recently used quote IDs from local state."""
    if not history_path.is_file():
        return []
    try:
        payload = json.loads(history_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    recent_ids = payload.get("recent_quote_ids", [])
    return [quote_id for quote_id in recent_ids if isinstance(quote_id, str)]


def write_history(
    history_path: Path, selected_id: str, recent_ids: list[str], *, limit: int
) -> None:
    """Persist the most recently used quote IDs with file locking."""
    updated_ids = [selected_id, *[quote_id for quote_id in recent_ids if quote_id != selected_id]]
    history_path.parent.mkdir(parents=True, exist_ok=True)
    content = (
        json.dumps({"recent_quote_ids": updated_ids[:limit]}, indent=2, ensure_ascii=False) + "\n"
    )
    with open(history_path, "w", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            fh.write(content)
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def quote_score(context_tokens: set[str], quote: dict[str, str]) -> int:
    """Score a saying by keyword overlap with the current task context."""
    if not context_tokens:
        return 0
    quote_tokens = tokenize(quote["text"]) | tokenize(quote.get("section", ""))
    return len(context_tokens & quote_tokens)


def build_rng(seed: str | None) -> random.Random:
    """Create a deterministic RNG for tests or a random one for normal usage."""
    if seed is not None:
        return random.Random(seed)
    return random.Random(secrets.randbits(128))


def weighted_choice(
    candidates: list[dict[str, str]],
    *,
    score_by_id: dict[str, int],
    rng: random.Random,
) -> dict[str, str]:
    """Choose a quote from the candidate pool while still preferring relevant ones."""
    if not candidates:
        raise ValueError("weighted_choice called with empty candidate list.")
    weights = [1 + 2 * score_by_id.get(candidate["id"], 0) for candidate in candidates]
    total_weight = sum(weights)
    if total_weight == 0:
        return rng.choice(candidates)
    roll = rng.randrange(total_weight)
    running_total = 0

    for candidate, weight in zip(candidates, weights):
        running_total += weight
        if roll < running_total:
            return candidate

    return candidates[-1]


def select_saying(
    quotes: list[dict[str, str]],
    *,
    context: str = "",
    seed: str | None = None,
    recent_ids: list[str] | None = None,
    relevance_bias: float = DEFAULT_RELEVANCE_BIAS,
) -> dict[str, str]:
    """Select one saying with long rotation, soft relevance, and repeat avoidance."""
    if not quotes:
        raise ValueError("No quotes available in snapshot.")

    rng = build_rng(seed)
    context_tokens = tokenize(context)
    score_by_id = {quote["id"]: quote_score(context_tokens, quote) for quote in quotes}
    recent_id_set = set(recent_ids or [])

    available_quotes = [quote for quote in quotes if quote["id"] not in recent_id_set]
    if not available_quotes:
        available_quotes = quotes[:]

    relevant_quotes = [quote for quote in available_quotes if score_by_id[quote["id"]] > 0]
    if relevant_quotes and rng.random() < relevance_bias:
        return weighted_choice(relevant_quotes, score_by_id=score_by_id, rng=rng)

    return rng.choice(available_quotes)


def format_saying(quote: dict[str, str], *, include_source: bool = False) -> str:
    """Render the selected saying for shell/agent consumption."""
    rendered_quote = f"“{quote['text']}”"
    if not include_source:
        return rendered_quote
    return f"{rendered_quote} [{quote['source_file']} / {quote['section']}]"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=DEFAULT_SNAPSHOT,
        help=f"Path to the local sayings snapshot (default: {DEFAULT_SNAPSHOT})",
    )
    parser.add_argument(
        "--context",
        default="",
        help="Short one-line summary of the task that just completed.",
    )
    parser.add_argument(
        "--seed",
        help="Optional deterministic seed for testing or reproducible selection.",
    )
    parser.add_argument(
        "--history-file",
        type=Path,
        default=DEFAULT_HISTORY,
        help=f"Path to the local quote history file (default: {DEFAULT_HISTORY})",
    )
    parser.add_argument(
        "--history-size",
        type=int,
        default=DEFAULT_HISTORY_SIZE,
        help=f"How many recent quote IDs to remember (default: {DEFAULT_HISTORY_SIZE})",
    )
    parser.add_argument(
        "--with-source",
        action="store_true",
        help="Include source file and section in the output.",
    )
    return parser.parse_args()


def main() -> int:
    """Entry point."""
    args = parse_args()
    try:
        snapshot = load_snapshot(args.snapshot)
        quotes = snapshot.get("quotes", [])
        recent_ids = load_history(args.history_file)
        selected = select_saying(
            quotes,
            context=args.context,
            seed=args.seed,
            recent_ids=recent_ids,
        )
        write_history(
            args.history_file,
            selected["id"],
            recent_ids,
            limit=max(args.history_size, 1),
        )
        print(format_saying(selected, include_source=args.with_source))
        return 0
    except (FileNotFoundError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
