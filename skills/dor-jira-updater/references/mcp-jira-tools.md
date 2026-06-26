# MCP Jira Tool Reference

Quick reference for the Jira tools available via the **mcp-atlassian**
MCP server.

## `jira_get_issue`

Fetch a single Jira issue by key.

| Parameter   | Type   | Required | Description                  |
| ----------- | ------ | -------- | ---------------------------- |
| `issue_key` | string | yes      | Jira issue key (e.g. DX-123) |

**Returns**: Issue object with all fields including custom fields.

## `jira_update_issue`

Update fields on a Jira issue.

| Parameter   | Type   | Required | Description                      |
| ----------- | ------ | -------- | -------------------------------- |
| `issue_key` | string | yes      | Jira issue key                   |
| `fields`    | object | yes      | Object of field_id → value pairs |

**IMPORTANT**: Use `fields`, not `additional_fields`. All updates go inside
the `fields` object.

## `jira_search`

Search for issues using JQL.

| Parameter | Type   | Required | Description               |
| --------- | ------ | -------- | ------------------------- |
| `jql`     | string | yes      | JQL query string          |
| `limit`   | int    | no       | Max results (default: 50) |

**Example JQL queries:**

```
# All stories in a project
project = DX AND issuetype = Story

# Stories in current sprint
project = DX AND sprint in openSprints()

# Stories without fix version
project = DX AND fixVersion is EMPTY AND issuetype = Story
```

## Error Codes

| HTTP Status | Meaning                                     |
| ----------- | ------------------------------------------- |
| 404         | Issue not found                             |
| 400         | Invalid field value or field not on screen  |
| 401/403     | Authentication failed (check PAT token)     |
| 500         | Jira server error (retry once, then report) |
