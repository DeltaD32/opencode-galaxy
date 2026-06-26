# /// script
# requires-python = ">=3.10"
# dependencies = ["requests"]
# ///
"""
gaia_router.py
==============
Given a task description, find the best matching public GAIA app and
(optionally) call it, returning the response.

This is the entry point used by the OpenCode orchestrator for GAIA auto-routing.

Usage (CLI):
    # Find best match for a task description (dry run — no API call)
    python3 gaia_router.py --task "help me write a jira ticket" --dry-run

    # Find best match AND call the app
    python3 gaia_router.py --task "help me write a jira ticket" --prompt "Create a story for adding dark mode to our Angular app"

    # Output JSON (for agent consumption)
    python3 gaia_router.py --task "agile sprint planning" --dry-run --json

Usage (library):
    from gaia_router import route_to_gaia

    result = route_to_gaia(
        task="help me create a jira ticket for the login bug",
        prompt="Create a bug ticket: login fails on iOS 17 with SSO enabled",
    )
    if result["matched"]:
        print(f"Used: {result['app_name']}")
        print(f"Response: {result['response']}")
    else:
        print("No suitable GAIA app found.")
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from gaia_catalog import GaiaCatalog  # type: ignore
from gaia_client import GaiaClient  # type: ignore

# ---------------------------------------------------------------------------
# Confidence threshold — below this score, don't auto-call
# ---------------------------------------------------------------------------
_MIN_SCORE = 2.0   # at least one word must match the name (score ≥ 2.0)
_HIGH_CONFIDENCE = 4.0   # name + multiple keywords → call without asking


def route_to_gaia(
    task: str,
    prompt: str | None = None,
    top_k: int = 3,
    min_score: float = _MIN_SCORE,
    auto_call: bool = True,
    poll_interval: float = 2.0,
    poll_max_attempts: int = 30,
) -> dict[str, Any]:
    """Find the best public GAIA app for a task and optionally call it.

    Args:
        task:              Short description of what the user needs (used for
                           catalog matching — not sent to the app).
        prompt:            The actual prompt to send to the app. If None and
                           auto_call=True, ``task`` is used as the prompt.
        top_k:             How many candidates to return in the result.
        min_score:         Minimum catalog match score to consider an app.
        auto_call:         If True and a match is found, call the app and
                           return its response.
        poll_interval:     Seconds between poll attempts.
        poll_max_attempts: Max poll attempts before timeout.

    Returns:
        dict with keys:
            matched      (bool)   — whether a suitable app was found
            app_id       (str)    — UUID of the best-matching app (if matched)
            app_name     (str)    — display name of the app (if matched)
            app_score    (float)  — match confidence score
            candidates   (list)   — top_k matches with scores
            response     (str)    — app response text (if auto_call=True and matched)
            error        (str)    — error message if something went wrong
    """
    catalog = GaiaCatalog()
    candidates = catalog.search(task, top_k=top_k, min_score=min_score)

    if not candidates:
        return {
            "matched": False,
            "candidates": [],
            "app_id": None,
            "app_name": None,
            "app_score": 0.0,
            "response": None,
            "error": None,
        }

    best = candidates[0]
    result: dict[str, Any] = {
        "matched": True,
        "app_id": best["id"],
        "app_name": best["name"],
        "app_score": best["score"],
        "candidates": candidates,
        "response": None,
        "error": None,
    }

    if auto_call:
        actual_prompt = prompt or task
        try:
            client = GaiaClient()
            result["response"] = client.chat(
                app_id=best["id"],
                prompt=actual_prompt,
                poll_interval=poll_interval,
                poll_max_attempts=poll_max_attempts,
            )
        except Exception as exc:
            result["error"] = str(exc)

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="Route a task to the best public GAIA app",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--task", required=True, help="Task description for catalog matching")
    parser.add_argument("--prompt", default=None, help="Prompt to send to the app (defaults to --task)")
    parser.add_argument("--dry-run", action="store_true", help="Match only — do not call the app")
    parser.add_argument("--top", type=int, default=3, help="Number of candidates to show (default 3)")
    parser.add_argument("--min-score", type=float, default=_MIN_SCORE, help=f"Min match score (default {_MIN_SCORE})")
    parser.add_argument("--json", dest="as_json", action="store_true", help="Output raw JSON (for agent use)")
    args = parser.parse_args()

    result = route_to_gaia(
        task=args.task,
        prompt=args.prompt,
        top_k=args.top,
        min_score=args.min_score,
        auto_call=not args.dry_run,
    )

    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if not result["matched"]:
        print(f"No GAIA app matched task: {args.task!r}  (min_score={args.min_score})")
        return

    print(f"Best match:  {result['app_name']}")
    print(f"App ID:      {result['app_id']}")
    print(f"Score:       {result['app_score']}")

    if len(result["candidates"]) > 1:
        print("\nOther candidates:")
        for c in result["candidates"][1:]:
            print(f"  [{c['score']:4.1f}] {c['name']}  ({c['id'][:8]}...)")

    if not args.dry_run:
        print(f"\nPrompt sent: {args.prompt or args.task}")
        if result["error"]:
            print(f"\n❌ Error: {result['error']}")
        else:
            print(f"\nResponse:\n{result['response']}")


if __name__ == "__main__":
    _cli()
