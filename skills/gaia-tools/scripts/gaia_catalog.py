# /// script
# requires-python = ">=3.10"
# dependencies = ["requests"]
# ///
"""
gaia_catalog.py
===============
Fetches and caches the full public GAIA app catalog locally so the orchestrator
can do fast keyword/semantic matching without a 60s API round-trip per request.

Cache location: ~/.opencode/skills/gaia-tools/cache/apps.json
Cache TTL:      24 hours (configurable via GAIA_CATALOG_TTL_HOURS env var)

Usage:
    # Refresh the catalog (run manually or via cron)
    python3 gaia_catalog.py --refresh

    # Print the cache summary
    python3 gaia_catalog.py --stats

    # Search the catalog (keyword match against name + description)
    python3 gaia_catalog.py --search "jira ticket"

    # As a library
    from gaia_catalog import GaiaCatalog
    catalog = GaiaCatalog()
    apps = catalog.search("agile sprint planning")
    best = apps[0]  # {"id": "...", "name": "...", "description": "...", "score": 0.87}
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_SKILL_DIR = pathlib.Path(__file__).parent.parent
_CACHE_DIR = _SKILL_DIR / "cache"
_CACHE_FILE = _CACHE_DIR / "apps.json"
_DEFAULT_TTL_HOURS = 24


# ---------------------------------------------------------------------------
# Catalog manager
# ---------------------------------------------------------------------------


class GaiaCatalog:
    """Local cache of the GAIA public app catalog with keyword search."""

    def __init__(self, ttl_hours: float | None = None) -> None:
        self.ttl_seconds = (
            float(os.environ.get("GAIA_CATALOG_TTL_HOURS", ttl_hours or _DEFAULT_TTL_HOURS))
            * 3600
        )
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Cache I/O
    # ------------------------------------------------------------------

    def _load_cache(self) -> dict | None:
        """Return cache dict if it exists and is fresh, else None."""
        if not _CACHE_FILE.exists():
            return None
        try:
            data = json.loads(_CACHE_FILE.read_text())
            age = time.time() - data.get("fetched_at", 0)
            if age > self.ttl_seconds:
                return None
            return data
        except (json.JSONDecodeError, KeyError):
            return None

    def _save_cache(self, apps: list[dict]) -> None:
        payload = {
            "fetched_at": time.time(),
            "count": len(apps),
            "apps": apps,
        }
        _CACHE_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2))

    # ------------------------------------------------------------------
    # Fetch from API
    # ------------------------------------------------------------------

    def refresh(self, verbose: bool = True) -> list[dict]:
        """Fetch the full public catalog from the GAIA API and write to cache."""
        # Import here so gaia_catalog.py can be imported without requests installed
        sys.path.insert(0, str(pathlib.Path(__file__).parent))
        from gaia_client import GaiaClient  # type: ignore

        if verbose:
            print("Fetching GAIA public app catalog...", flush=True)

        client = GaiaClient()
        raw_apps = client.list_apps()  # returns a list

        # Normalise: keep only fields useful for matching
        apps = []
        for app in raw_apps:
            apps.append(
                {
                    "id": app.get("id", ""),
                    "name": app.get("name") or app.get("displayName") or "",
                    "description": app.get("description") or "",
                    "type": app.get("type") or app.get("appType") or "",
                    "status": app.get("status") or "",
                    "author": app.get("author") or "",
                }
            )

        self._save_cache(apps)
        if verbose:
            print(f"Cached {len(apps)} apps → {_CACHE_FILE}")
        return apps

    # ------------------------------------------------------------------
    # Load (with auto-refresh)
    # ------------------------------------------------------------------

    def load(self, auto_refresh: bool = True) -> list[dict]:
        """Return the catalog, refreshing from API if cache is stale."""
        cached = self._load_cache()
        if cached:
            return cached["apps"]
        if auto_refresh:
            return self.refresh(verbose=False)
        raise FileNotFoundError(
            f"GAIA catalog cache not found or stale. "
            f"Run: python3 {__file__} --refresh"
        )

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0,
        app_type: str | None = None,
        enrich_top: int = 0,
    ) -> list[dict]:
        """Keyword search across app name (+ description when available).

        Since the GAIA list endpoint does not return descriptions, scoring is
        name-only.  Scoring rules (additive):

          +3.0  exact full-phrase match in name
          +2.0  per query word that is a complete token in the name
          +1.0  per query word that appears as a substring in the name
          +0.5  per query word found in description (when available)
          +0.1  coverage bonus = (matched_words / total_words) — rewards breadth

        Ties are broken by name length (shorter = more focused app).

        Returns a list of dicts with an added ``score`` field, sorted descending.

        Args:
            query:      Free-text search string.
            top_k:      Max results to return.
            min_score:  Minimum score threshold (0 = return all matches).
            app_type:   Optional filter: 'chat_app', 'external_app', etc.
            enrich_top: If > 0, fetch individual app details for the top N
                        results to populate descriptions.  Adds one API call
                        per enriched app.  Use only when you have a client
                        available (pass via GaiaClient kwarg if needed).
        """
        apps = self.load()
        query_lower = query.lower()
        # Filter noise words shorter than 3 chars
        words = [w for w in query_lower.split() if len(w) > 2]

        results: list[dict] = []
        for app in apps:
            if app_type and app.get("type") != app_type:
                continue

            name = app["name"].lower()
            desc = (app["description"] or "").lower()
            name_tokens = set(name.replace("-", " ").replace("_", " ").split())

            score = 0.0
            matched = 0

            # Exact full-phrase in name — strongest signal
            if query_lower in name:
                score += 3.0
                matched = len(words)
            else:
                for word in words:
                    if word in name_tokens:          # complete token match
                        score += 2.0
                        matched += 1
                    elif word in name:               # substring match
                        score += 1.0
                        matched += 1
                    if desc and word in desc:
                        score += 0.5

            # Coverage bonus
            if words:
                score += 0.1 * (matched / len(words))

            if score > min_score:
                results.append({**app, "score": round(score, 2)})

        # Sort: score desc, then name length asc (more focused app wins ties)
        results.sort(key=lambda x: (-x["score"], len(x["name"])))
        return results[:top_k]

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> dict[str, Any]:
        cached = self._load_cache()
        if not cached:
            return {"cached": False}
        age_minutes = (time.time() - cached["fetched_at"]) / 60
        return {
            "cached": True,
            "count": cached["count"],
            "age_minutes": round(age_minutes, 1),
            "ttl_hours": self.ttl_seconds / 3600,
            "cache_file": str(_CACHE_FILE),
        }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="GAIA app catalog manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--refresh", action="store_true", help="Fetch catalog from API and save to cache")
    group.add_argument("--stats", action="store_true", help="Print cache statistics")
    group.add_argument("--search", metavar="QUERY", help="Keyword search the catalog")
    parser.add_argument("--top", type=int, default=5, help="Max results for --search (default 5)")
    parser.add_argument("--type", dest="app_type", default=None, help="Filter by app type (e.g. chat_app)")
    args = parser.parse_args()

    catalog = GaiaCatalog()

    if args.refresh:
        catalog.refresh(verbose=True)

    elif args.stats:
        s = catalog.stats()
        if not s["cached"]:
            print("No cache found. Run: python3 gaia_catalog.py --refresh")
        else:
            print(f"Cache: {s['cache_file']}")
            print(f"  Apps:      {s['count']}")
            print(f"  Age:       {s['age_minutes']} min  (TTL {s['ttl_hours']}h)")

    elif args.search:
        results = catalog.search(args.search, top_k=args.top, app_type=args.app_type)
        if not results:
            print(f"No matches for: {args.search!r}")
        else:
            print(f"Top {len(results)} matches for {args.search!r}:\n")
            for i, app in enumerate(results, 1):
                print(f"  {i}. [{app['score']:4.1f}] {app['name']}")
                print(f"       id:   {app['id']}")
                if app["description"]:
                    print(f"       desc: {app['description'][:100]}")
                print()


if __name__ == "__main__":
    _cli()
