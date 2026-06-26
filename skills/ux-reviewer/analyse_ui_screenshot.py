"""
analyse_ui_screenshot.py — Vision analysis helper for ux-reviewer.

Sends a UI screenshot (file path, URL, or base64 data URL) to gpt-4o and returns
a typed UXScreenAnalysis Pydantic model with no JSON parsing required.

Usage:
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path.home() / ".opencode/skills/ux-reviewer"))
    from analyse_ui_screenshot import analyse_ui_screenshot, UXScreenAnalysis

    # Single screenshot:
    analysis = analyse_ui_screenshot("path/to/screenshot.png", context="Dashboard home")
    print(analysis.layout_description)   # typed str
    print(analysis.visible_text)         # typed List[str]
    print(analysis.potential_issues)     # typed List[str]

    # Multiple screens (iterate):
    analyses = [analyse_ui_screenshot(p, context=ctx) for p, ctx in screens]
"""

import base64
import os
import pathlib

import httpx
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List

VISION_MODEL = "gpt-4o"

_ca_default = str(
    pathlib.Path.home()
    / ".opencode/plugins/clipjoint/BMW_Trusted_Certificates_Latest.pem"
)


def _client() -> OpenAI:
    ca = os.environ.get("BMW_CA_BUNDLE") or _ca_default
    return OpenAI(
        base_url=os.environ.get(
            "LLM_API_BASE_URL", "https://api.gcp.cloud.bmw/llmapi/v1"
        ),
        api_key=os.environ.get("LLM_API_KEY", "unused"),
        http_client=httpx.Client(
            headers={"x-apikey": os.environ["LLM_API_KEY"]},
            verify=ca if pathlib.Path(ca).exists() else True,
        ),
        default_headers={
            "Authorization": f"Bearer {os.environ['LLM_API_BEARER_TOKEN']}"
        },
    )


class UXScreenAnalysis(BaseModel):
    """Typed, validated result of a UI screenshot analysis."""

    layout_description: str = Field(
        description="Overall layout, structure, and visual organisation"
    )
    visible_text: List[str] = Field(
        description=(
            "Every piece of visible text "
            "(labels, headings, CTAs, errors, nav, footer)"
        )
    )
    components: List[str] = Field(
        description=(
            "All UI components visible "
            "(e.g. 'primary button', 'data table', 'side nav')"
        )
    )
    visual_hierarchy: str = Field(
        description="Visual weight, focal points, and information flow"
    )
    potential_issues: List[str] = Field(
        description=(
            "Visible UX problems "
            "(unclear labels, poor contrast, missing feedback…)"
        )
    )


def _build_image_block(image_source: str) -> dict:
    """Convert a file path, URL, or data URL into a vision content block."""
    if image_source.startswith(("http", "data:")):
        return {"type": "image_url", "image_url": {"url": image_source}}
    suffix = pathlib.Path(image_source).suffix.lower().lstrip(".")
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png",
            "webp": "webp", "gif": "gif"}.get(suffix, "png")
    b64 = base64.b64encode(pathlib.Path(image_source).read_bytes()).decode()
    return {"type": "image_url", "image_url": {"url": f"data:image/{mime};base64,{b64}"}}


def analyse_ui_screenshot(
    image_source: str,
    context: str = "",
) -> UXScreenAnalysis:
    """
    Send a UI screenshot to gpt-4o and return a typed UXScreenAnalysis.

    Args:
        image_source: File path, https:// URL, or "data:image/...;base64,..." string.
        context: Optional description of the screen/feature (improves results).

    Returns:
        UXScreenAnalysis — fully typed, Pydantic-validated. No JSON parsing needed.
    """
    context_line = f"\nContext: {context}" if context else ""
    prompt = f"You are a UX analyst reviewing a UI screenshot.{context_line} Analyse this screen."

    completion = _client().beta.chat.completions.parse(
        model=VISION_MODEL,
        max_tokens=1500,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                _build_image_block(image_source),
            ],
        }],
        response_format=UXScreenAnalysis,
    )
    return completion.choices[0].message.parsed


def compare_screenshots(
    image_sources: list[str],
    context: str = "",
) -> UXScreenAnalysis:
    """
    Send multiple screenshots to gpt-4o for comparison.

    Useful for before/after analysis or desktop-vs-mobile comparison.

    Args:
        image_sources: List of file paths, URLs, or data URLs.
        context: Optional description of what to compare.

    Returns:
        UXScreenAnalysis describing inconsistencies between screens.
    """
    context_line = f"\nContext: {context}" if context else ""
    prompt = (
        f"Compare these screens. Identify UX inconsistencies between them.{context_line}"
    )
    content = [{"type": "text", "text": prompt}]
    for src in image_sources:
        content.append(_build_image_block(src))

    completion = _client().beta.chat.completions.parse(
        model=VISION_MODEL,
        max_tokens=1000,
        messages=[{"role": "user", "content": content}],
        response_format=UXScreenAnalysis,
    )
    return completion.choices[0].message.parsed
