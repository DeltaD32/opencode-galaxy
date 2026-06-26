"""
generate_dor_fields.py — BMW LLM API structured output for DoR field generation.

Calls the BMW LLM API with client.chat.completions.parse() to fill missing
Definition-of-Ready Jira fields for a single story. Returns a typed
DoRFieldValues object — no JSON parsing or string extraction required.

Usage:
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path.home() / ".opencode/skills/dor-jira-updater/scripts"))
    from generate_dor_fields import generate_dor_fields, DoRFieldValues

    result = generate_dor_fields(
        issue_key="DX-123",
        current_fields={"summary": "Add PDF rotation"},
        dor_requirements=[{"field": "story_points", "required": True}],
    )
    # result is a typed DoRFieldValues object
    for f in result.fields:
        print(f.logical_name, "->", f.example_value)

    # Pass directly to build_jira_payload.build_payload():
    payload = build_payload(
        issue_key=result.issue_key,
        dor_fields=[f.model_dump() for f in result.fields],
        description_template=description,
        acceptance_criteria=ac,
    )
"""

import json
import os
from pydantic import BaseModel, Field
from typing import List, Optional
import openai


class DoRField(BaseModel):
    logical_name: str = Field(
        description=(
            "Logical field name matching the DEFAULT_FIELD_MAP key in "
            "build_jira_payload.py (e.g. 'summary', 'description', "
            "'story_points', 'labels', 'priority', 'components')."
        )
    )
    example_value: str | list = Field(
        description=(
            "Concrete value to write. Strings for scalar fields; "
            "list of strings for array fields (components, labels, fixVersions)."
        )
    )
    reason: str = Field(
        description="One-sentence justification for the generated value."
    )


class DoRFieldValues(BaseModel):
    issue_key: str = Field(
        description="Jira issue key, e.g. 'DX-123'."
    )
    fields: List[DoRField] = Field(
        description=(
            "Only fields that are currently missing or non-compliant. "
            "Do not include fields that already satisfy the DoR."
        )
    )
    compliance_notes: Optional[str] = Field(
        default=None,
        description=(
            "Optional overall assessment of this story's DoR compliance "
            "after the proposed updates."
        ),
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
    "You are a Jira DoR compliance assistant. Given the current Jira issue fields "
    "and the Definition-of-Ready requirements, identify which fields are missing or "
    "non-compliant and generate concrete values for them. "
    "Only output fields that need updating — skip fields that already satisfy the DoR. "
    "story_points must be a numeric string ('3', '5', '8'). "
    "priority must be one of: Highest, High, Medium, Low, Lowest. "
    "labels and components must be lists of strings."
)


def generate_dor_fields(
    issue_key: str,
    current_fields: dict,
    dor_requirements: list,
    model: str = "gpt-4o",
) -> DoRFieldValues:
    """
    Call BMW LLM API with structured output to fill missing DoR fields for one story.

    Args:
        issue_key:        Jira issue key, e.g. "DX-123".
        current_fields:   Dict of the story's current Jira fields.
        dor_requirements: List of DoR rule dicts (from dor-confluence-reader).
        model:            BMW LLM API model name (default: gpt-4o).

    Returns:
        DoRFieldValues — typed, Pydantic-validated. Access .fields directly.
    """
    prompt = {
        "issue_key": issue_key,
        "current_fields": current_fields,
        "dor_requirements": dor_requirements,
    }
    completion = _client().chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(prompt, indent=2)},
        ],
        response_format=DoRFieldValues,
    )
    return completion.choices[0].message.parsed
