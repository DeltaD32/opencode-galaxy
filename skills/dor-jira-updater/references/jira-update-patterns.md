# Jira Update Patterns

Reference for formatting Jira field values correctly when calling
`jira_update_issue` via the MCP tool.

## `jira_update_issue` Calling Convention

The `fields` parameter is **required** (not `additional_fields`).
Put ALL field updates inside `fields`.

```json
{
  "issue_key": "PROJ-123",
  "fields": {
    "field_id": "value",
    "another_field": "value"
  }
}
```

## Value Formatting Rules

### Array-of-Objects Fields

Fields: `components`, `fixVersions`, `customfield_11400` (Feature Team)

```json
"components": [{"name": "Backend"}],
"fixVersions": [{"name": "v24.3"}],
"customfield_11400": [{"name": "Core Platform"}]
```

Multiple values:

```json
"components": [{"name": "Backend"}, {"name": "API"}]
```

### Priority

Always an object with `name`:

```json
"priority": {"name": "Medium"}
```

### Labels

Array of strings (not objects):

```json
"labels": ["auto-generated", "copilot-sdk", "team-alpha"]
```

**Merging**: To preserve existing labels, fetch the issue first, then
combine existing labels with new ones (deduplicate).

### Okapya Checklist (Acceptance Criteria)

`customfield_11100` — JSON array of checklist items:

```json
"customfield_11100": [
  {"name": "All DoR fields populated", "checked": false, "mandatory": false},
  {"name": "Fix Version set correctly", "checked": false, "mandatory": false}
]
```

### Description

Markdown string. Do NOT put acceptance criteria here.

```json
"description": "## Description Format\n**Overview**: ..."
```

### Simple String Fields

```json
"environment": "Production",
"duedate": "2026-06-30"
```

### Timetracking

```json
"timetracking": {"originalEstimate": "2d"}
```

## Skip Fields

Never include in `jira_update_issue`:

- `customfield_10001` (epic_link) — requires a valid epic key
- `customfield_10000` (sprint) — requires numeric sprint ID

## Error Recovery

| Error                   | Recovery                                |
| ----------------------- | --------------------------------------- |
| Field not on screen     | Remove field from payload, retry        |
| Invalid value for field | Check format rules above, fix and retry |
| Issue not found         | Skip story, log warning                 |
| Permission denied       | Log error, skip story                   |
