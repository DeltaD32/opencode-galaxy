"""
generate_story.py — BMW LLM API structured output for Jira story generation.

Calls the BMW LLM API with client.chat.completions.parse() to generate a typed
StoryContent from a git branch analysis dict. Returns a Pydantic-validated
StoryContent object — no JSON parsing or string extraction required.

Usage:
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path.home() / ".opencode/skills/jira-adhoc-story/scripts"))
    from generate_story import generate_story, StoryContent

    import subprocess, json
    branch_analysis = json.loads(
        subprocess.check_output(
            ["python3",
             str(pathlib.Path.home() / ".opencode/skills/jira-adhoc-story/scripts/analyze_branch.py")]
        )
    )
    story = generate_story(branch_analysis)
    print(story.summary)                # "Add PDF rotation"
    print(story.acceptance_criteria)    # ["PDF rotates correctly", ...]
    print(story.labels)                 # ["documentation", "ci"]
"""

import json
import os
from pydantic import BaseModel, Field
from typing import List
import openai


class StoryContent(BaseModel):
    summary: str = Field(
        description=(
            "One-line story title, max 100 chars. "
            "'Add …' for feature, 'Fix …' for fix."
        )
    )
    context: str = Field(
        description=(
            "Why this work was needed (2-3 sentences from commit messages)."
        )
    )
    changes_made: str = Field(
        description=(
            "Bullet list of key commits and file changes (Jira wiki markup)."
        )
    )
    impact: str = Field(
        description=(
            "How this affects the project or users (1-2 sentences)."
        )
    )
    acceptance_criteria: List[str] = Field(
        description=(
            "3-5 measurable criteria derived from actual changes. "
            "Checkbox-ready strings — no '- [ ]' prefix (caller adds it)."
        )
    )
    labels: List[str] = Field(
        description=(
            "Relevant labels (e.g. 'documentation', 'ci', 'frontend'). "
            "Empty list if none clearly apply."
        )
    )


def _client() -> openai.OpenAI:
    return openai.OpenAI(
        base_url=os.environ["LLM_API_BASE_URL"],
        api_key=os.environ.get("LLM_API_KEY", "unused"),
        default_headers={
            "Authorization": f"Bearer {os.environ['LLM_API_BEARER_TOKEN']}",
            "x-apikey": os.environ["LLM_API_KEY"],
        },
    )


_SYSTEM_PROMPT = (
    "You are a Jira story writer. Given git branch analysis data, "
    "generate a Jira story following the schema exactly. "
    "summary: start with 'Add' for feature branches, 'Fix' for fix branches. "
    "Convert kebab-case branch names to human-readable form. "
    "acceptance_criteria: checkbox-ready strings (no '- [ ]' prefix, the caller adds it). "
    "labels: only add if clearly evidenced by commit messages or file paths."
)


def generate_story(
    branch_analysis: dict,
    model: str = "gpt-4o",
) -> StoryContent:
    """
    Generate a Jira story from git branch analysis data.

    Args:
        branch_analysis: Dict output from scripts/analyze_branch.py — contains
                         current_branch, branch_type, branch_name, commits,
                         files_changed, is_behind, behind_count.
        model:           BMW LLM API model name (default: gpt-4o).

    Returns:
        StoryContent — typed, Pydantic-validated. Access fields directly.
        Acceptance criteria are formatted for display as:
            - [ ] {criterion}
    """
    completion = _client().chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(branch_analysis, indent=2)},
        ],
        response_format=StoryContent,
    )
    return completion.choices[0].message.parsed
