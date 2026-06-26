"""
reranker.py
===========
Async, semaphore-guarded reranker for the deep-web-research skill.

Uses cohere/rerank-3-5 via BMW LLM API to rerank merged lane findings
by semantic relevance to the original user question. Retries on HTTP 429
(rate limit) and 5xx (server errors) with exponential backoff.

Extracted from ~/.opencode/skills/deep-web-research/SKILL.md — single source of truth.
Import this module directly; do not regenerate this code inline.

Usage:
    import sys, pathlib, asyncio, os
    sys.path.insert(0, str(pathlib.Path.home() / ".opencode/skills/deep-web-research"))
    from reranker import rerank_findings

    # From async context:
    top = await rerank_findings(user_question, all_findings, top_n=8)

    # From sync context:
    top = asyncio.run(rerank_findings(user_question, all_findings, top_n=8))
"""

from __future__ import annotations

import asyncio
import os
import pathlib

try:
    import requests as _requests
except ImportError as exc:
    raise ImportError(
        "reranker requires 'requests'. "
        "Use the clipjoint venv: ~/.opencode/plugins/clipjoint/.venv/bin/python3"
    ) from exc

_DEFAULT_CA = str(
    pathlib.Path.home() / ".opencode/plugins/clipjoint/BMW_Trusted_Certificates_Latest.pem"
)
_RERANK_MODEL = "cohere/rerank-3-5"
_semaphore    = asyncio.Semaphore(5)   # cap simultaneous rerank calls


async def rerank_findings(
    question: str,
    findings: list[str],
    top_n: int = 8,
    max_retries: int = 4,
    base_delay: float = 1.0,
) -> list[str]:
    """
    Rerank *findings* against *question* using cohere/rerank-3-5.

    Returns the top_n most relevant findings in descending relevance order.
    Retries HTTP 429 / 5xx with exponential backoff.

    If findings has ≤ top_n items, all are returned in ranked order (no trimming).

    Args:
        question   : The original user question used as the rerank query.
        findings   : List of candidate finding strings (merged from all lanes).
        top_n      : Number of top findings to return (default: 8).
        max_retries: Number of retry attempts on rate-limit / server errors.
        base_delay : Base delay in seconds for exponential backoff.

    Returns:
        List of finding strings, ordered by descending relevance score.

    Raises:
        RuntimeError: If all retries are exhausted.
        KeyError    : If LLM_API_KEY / LLM_API_BEARER_TOKEN are not set.
    """
    if not findings:
        return []

    raw_url  = os.environ.get("LLM_API_BASE_URL",
                              "https://api.gcp.cloud.bmw/llmapi/v1")
    base_url = raw_url.rstrip("/").removesuffix("/v1")
    api_key  = os.environ["LLM_API_KEY"]
    token    = os.environ["LLM_API_BEARER_TOKEN"]
    ca       = _DEFAULT_CA if pathlib.Path(_DEFAULT_CA).exists() else True

    async with _semaphore:
        loop = asyncio.get_running_loop()
        for attempt in range(max_retries):
            resp = await loop.run_in_executor(
                None,
                lambda: _requests.post(
                    f"{base_url}/v1/rerank",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "x-apikey":      api_key,
                        "Content-Type":  "application/json",
                    },
                    json={
                        "model":     _RERANK_MODEL,
                        "query":     question,
                        "documents": findings,
                        "top_n":     min(top_n, len(findings)),
                    },
                    verify=ca,
                    timeout=30,
                ),
            )
            if resp.status_code in (429,) or resp.status_code >= 500:
                await asyncio.sleep(base_delay * (2 ** attempt))
                continue
            resp.raise_for_status()
            ranked = resp.json()["results"]   # [{index, relevance_score}, ...]
            return [findings[r["index"]] for r in ranked]

        raise RuntimeError(
            f"rerank_findings: failed after {max_retries} retries "
            f"(question={question[:60]!r})"
        )
