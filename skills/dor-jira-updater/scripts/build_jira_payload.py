# /// script
# requires-python = ">=3.10"
# ///
"""
build_jira_payload.py — Build Jira update payloads from DoR spec and story data.

Takes a DoR specification (from step 2) and a list of stories (from step 1)
and produces correctly formatted jira_update_issue payloads for each story.

Usage:
    uv run scripts/build_jira_payload.py --dor-spec dor.json --stories backlog.json

Output:
    JSON array of {issue_key, fields} payloads to stdout.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Default field map (same as in SKILL.md and DoR_skill.md)
DEFAULT_FIELD_MAP: dict[str, str] = {
    "summary": "summary",
    "description": "description",
    "acceptance_criteria": "customfield_11100",
    "story_points": "story_points",
    "labels": "labels",
    "priority": "priority",
    "components": "components",
    "assignee": "assignee",
    "fix_versions": "fixVersions",
    "due_date": "duedate",
    "environment": "environment",
    "feature_team": "customfield_11400",
    "original_estimate": "timetracking",
}

SKIP_FIELDS: set[str] = {"customfield_10001", "customfield_10000"}

ARRAY_FIELDS: set[str] = {"components", "fixVersions", "customfield_11400"}

DEFAULT_LABELS: list[str] = ["auto-generated", "copilot-sdk"]
DEFAULT_PRIORITY: str = "Medium"

# Generic fallback description template following the BMW ATC DoR standard structure.
# Used only when parse_dor_page.py returns 0 sections from the live Confluence DoR page.
# The live page (CONFLUENCE_DOR_PAGE_ID) is always preferred — this is a safe default.
DOR_DESCRIPTION_TEMPLATE: str = """\
*DESCRIPTION:*

*Overview*
A brief summary (2-3 sentences) explaining the purpose of the story and its significance to the project or product.
Format: As a [insert title] I want to [objective] in order to [benefit/outcome]

*Objective*
Clearly outline the goals of the story.
Format: "What do I want to achieve?" + "Why do I want to achieve this respectively, what is the targeted benefit?"

*Key Features*
List the main features or functionalities that will be developed as part of this story. Use bullet points for clarity.

*Scope of work*
Summarise scope of work.

*KPIs*
"How do I know that the objective is achieved?"
Format: Provide in numbered list

*Expected user stories/topics + est US estimation each*
Tip: Number and place in order of completion.

*Dependencies*
Identify any dependencies on other stories, or external factors that could impact the completion of this story.

*Stakeholders*
List the key stakeholders involved, including team members, co-creators (if applicable), and any other relevant parties.

*Risks and Mitigations*
Highlight any potential risks and suggest mitigation strategies.\
"""


def _build_description_from_sections(sections: list[dict]) -> str:
    """Build a Jira wiki-markup description string from parsed DoR sections."""
    parts = ["*DESCRIPTION:*", ""]
    for section in sections:
        heading = section.get("heading", "")
        instructions = section.get("instructions", "")
        parts.append(f"*{heading}*")
        if instructions:
            parts.append(instructions)
        parts.append("")
    return "\n".join(parts).strip()


def format_field_value(field_id: str, value: str | list | dict) -> object:
    """Format a field value according to Jira's expected format."""
    if field_id in ARRAY_FIELDS:
        if isinstance(value, str):
            return [{"name": value}]
        if isinstance(value, list) and value and isinstance(value[0], str):
            return [{"name": v} for v in value]
        return value

    if field_id == "priority":
        if isinstance(value, str):
            return {"name": value}
        return value

    if field_id == "labels":
        if isinstance(value, str):
            return [value]
        return value

    if field_id == "timetracking":
        if isinstance(value, str):
            return {"originalEstimate": value}
        return value

    return value


def build_payload(
    issue_key: str,
    dor_fields: list[dict],
    description_template: str,
    acceptance_criteria: list[dict],
    field_map: dict[str, str] | None = None,
    existing_labels: list[str] | None = None,
) -> dict:
    """Build a jira_update_issue payload for a single story."""
    fmap = field_map or DEFAULT_FIELD_MAP
    fields: dict = {}

    # Set description
    fields["description"] = description_template

    # Note: customfield_11100 (Okapya checklist) uses a proprietary format
    # that cannot be set via standard REST API. It is intentionally excluded
    # from the REST payload — populate it manually or via the Okapya plugin API.
    # fields["customfield_11100"] = acceptance_criteria  # excluded

    # Set discovered fields
    for dor_field in dor_fields:
        logical = dor_field.get("logical_name", "")
        jira_id = fmap.get(logical)
        if not jira_id or jira_id in SKIP_FIELDS:
            continue
        if jira_id in ("description", "customfield_11100"):
            continue  # Already handled above
        value = dor_field.get("example_value", "")
        if value:
            fields[jira_id] = format_field_value(jira_id, value)

    # Apply defaults
    if "labels" not in fields:
        merged = list(set((existing_labels or []) + DEFAULT_LABELS))
        fields["labels"] = merged
    else:
        existing = existing_labels or []
        current = fields["labels"] if isinstance(fields["labels"], list) else [fields["labels"]]
        fields["labels"] = list(set(existing + current + DEFAULT_LABELS))

    if "priority" not in fields:
        fields["priority"] = {"name": DEFAULT_PRIORITY}

    return {"issue_key": issue_key, "fields": fields}


def main() -> None:
    ap = argparse.ArgumentParser(description="Build Jira update payloads")
    ap.add_argument("--dor-spec", required=True, help="DoR specification JSON file")
    ap.add_argument("--stories", required=True, help="Backlog stories JSON file")
    args = ap.parse_args()

    dor_path = Path(args.dor_spec)
    stories_path = Path(args.stories)

    if not dor_path.exists():
        print(f"ERROR: DoR spec not found: {dor_path}", file=sys.stderr)
        sys.exit(1)
    if not stories_path.exists():
        print(f"ERROR: stories file not found: {stories_path}", file=sys.stderr)
        sys.exit(1)

    dor = json.loads(dor_path.read_text(encoding="utf-8"))
    stories = json.loads(stories_path.read_text(encoding="utf-8"))

    dor_fields = dor.get("required_fields", [])

    # Build description template from parsed DoR sections, or use the canonical DoR template
    parsed_sections = dor.get("description_template", {}).get("sections", [])
    if parsed_sections:
        description = _build_description_from_sections(parsed_sections)
    else:
        description = DOR_DESCRIPTION_TEMPLATE

    ac = [{"name": "All required DoR fields populated", "checked": False, "mandatory": False}]

    payloads = []
    story_list = stories if isinstance(stories, list) else stories.get("stories", [])
    for story in story_list:
        key = story.get("issue_key", "")
        if key:
            payload = build_payload(key, dor_fields, description, ac)
            payloads.append(payload)

    print(json.dumps(payloads, indent=2))


if __name__ == "__main__":
    main()
