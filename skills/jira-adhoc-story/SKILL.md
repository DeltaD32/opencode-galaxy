---
name: jira-adhoc-story
description: Creates Jira story tickets for ad-hoc work based on current branch analysis. Analyzes commits, generates summary/description/acceptance criteria, and checks if rebase is needed. Use when documenting completed work that lacks a pre-existing ticket, creating retrospective documentation, or when user mentions creating a ticket for current branch work.
license: Proprietary
compatibility: Requires git, jq, and Jira MCP server configured. Works with feature/* and fix/* branch naming conventions.
metadata:
  author: Matthias Bilger <matthias.bilger@bmw.de>
  version: "1.0.1"
  tags:
    - jira
    - git
    - documentation
    - workflow
    - story
  memory:
    read:
      - workspace.md
    write:
      - workspace.md
---

# jira-adhoc-story

## Goal

Create a comprehensive Jira story ticket that documents ad-hoc work by analyzing the current branch's commits, generating appropriate summary, description, and acceptance criteria automatically.

## When to use

- User wants to create a ticket for work already completed on current branch
- User mentions "document my work", "create a ticket for this branch", or "I need a Jira story"
- Ad-hoc work was done without a pre-existing ticket
- Retrospective documentation is needed for tracking purposes

## Inputs

- Current git branch with commits (preferably `feature/*` or `fix/*` naming)
- Commits that diverge from the default branch (main)
- Optional: Jira project key from `.ttt/memory/workspace.md`

## Outputs

- Jira story ticket created with:
  - Auto-generated summary based on branch name and commits
  - Comprehensive description with context, changes, and impact
  - Acceptance criteria derived from actual changes
  - Proper labels/components if mentioned in commits
- Notification if branch needs rebasing (is behind main)
- Ticket key (e.g., DX-1234) returned to user

## State Management

**IMPORTANT**: This skill reads Jira project information from `.ttt/memory/workspace.md`.

- **Read first**: Check if `.ttt/memory/workspace.md` exists and contains Jira project key
- **If missing**: Ask user for Jira project key and update the workspace.md file
- **Respect existing data**: Use the project key from workspace.md as the default
- **Update when needed**: If user provides a different project key, confirm before updating workspace.md

Example workspace.md structure:

```markdown
# Workspace

## Infrastructure Tools

- **Issue Tracking**: jira - https://atc.bmwgroup.net/jira (Project: DX)
```

## Steps

1. **Validate prerequisites**

   - Check git repository is available
   - Verify current branch is appropriate for ticket creation
   - Ensure Jira MCP server is configured (use <skill>mcp-setup</skill> if needed)
   - Confirm jq is installed for JSON processing

2. **Check Jira project configuration**

   - Read `.ttt/memory/workspace.md` to find Jira project key
   - Look for "Issue Tracking: jira" section with "(Project: XXX)"
   - If not found, ask user: "What is your Jira project key?"
   - Update workspace.md with the project information for future use

3. **Analyze current branch**

   - Run `scripts/analyze_branch.py` to extract branch information:
     ```bash
     python skills/jira-adhoc-story/scripts/analyze_branch.py
     ```
   - The script outputs JSON with:
     - `current_branch`: Branch name
     - `branch_type`: "feature", "fix", or "other"
     - `branch_name`: Extracted name without prefix
     - `commits`: Array of commits with hash, author, date, message
     - `files_changed`: Array of changed files with status (A/M/D)
     - `is_behind`: Boolean indicating if branch is behind default
     - `behind_count`: Number of commits behind

4. **Validate branch and commits**

   - Ensure branch has commits that diverge from main
   - If no commits found, inform user: "This branch has no new commits to document"
   - If branch type is "other" (not feature/fix), warn user but proceed if confirmed
   - If branch is behind main (`is_behind: true`), note this for later notification

5. **Generate story content**

   Read [references/story-template.md](references/story-template.md) for guidance on structure.

   Use `generate_story()` from the co-located module. Returns a typed `StoryContent`
   object — no free-text parsing needed.

   ```python
   import sys, pathlib, json, subprocess
   sys.path.insert(0, str(pathlib.Path.home() / ".opencode/skills/jira-adhoc-story/scripts"))
   from generate_story import generate_story, StoryContent

   branch_analysis = json.loads(
       subprocess.check_output(["python3", "skills/jira-adhoc-story/scripts/analyze_branch.py"])
   )
   story = generate_story(branch_analysis)
   # story.summary, story.context, story.changes_made, story.impact,
   # story.acceptance_criteria (List[str]), story.labels (List[str])
   ```

   Module: `scripts/generate_story.py`
   Function: `generate_story(branch_analysis, model="gpt-4o")`
   Returns: `StoryContent` — typed Pydantic model. Acceptance criteria are checkbox-ready
   strings; format for display as `- [ ] {criterion}`.

   **Identify Labels/Components:**

   - Use the `labels` field from `StoryContent` directly
   - Common patterns auto-detected: "documentation", "testing", "ci", "frontend", "backend"
   - Only populated when clearly evidenced in commits or changed file paths

6. **Present story draft to user**

   Before creating the ticket, show the user:

   - Proposed summary
   - Generated description
   - Acceptance criteria
   - Any labels/components to add
   - Project and story type

   Ask: "Does this story accurately represent your work? Any changes needed?"

   If user requests changes, iterate on the content before creating the ticket.

7. **Create Jira story**

   Use Jira MCP tools to create the story:

   - Load the Jira MCP tools using `tool_search_tool_regex` with pattern `mcp_jira.*create_issue`
   - Call `mcp_jira_jira_create_issue` with:
     - `project`: Project key from workspace.md
     - `summary`: Generated summary
     - `description`: Generated description with sections
     - `issuetype`: "Story"
     - `labels`: Array of identified labels (if any)
     - `components`: Array of identified components (if any)

   Note: Acceptance criteria may need to be added in a separate field or as part of the description, depending on Jira configuration.

8. **Report results**

   After successful creation:

   - Display the ticket key (e.g., "Created story DX-1234")
   - Provide a link to the ticket
   - If branch was behind main, suggest:
     "Note: Your branch is {behind_count} commits behind main. Consider rebasing with: `git rebase origin/main`"

## Examples

### Example 1: Feature branch with multiple commits

**Input:**

- Branch: `feature/add-pdf-rotation`
- Commits:
  - "Add PDF rotation script"
  - "Update documentation"
  - "Add tests for rotation"

**Output:**

```
Created Jira story DX-1234: Add PDF rotation

Summary: Add PDF rotation
Description:
## Context
Added capability to rotate PDF files to support document processing workflows.

## Changes Made
- Implemented PDF rotation script with rotation angle support
- Updated documentation with usage examples
- Added comprehensive test suite for rotation functionality

## Impact
Users can now rotate PDF documents programmatically, improving document processing capabilities.

Acceptance Criteria:
- [ ] PDF rotation script successfully rotates documents
- [ ] Documentation includes clear usage examples
- [ ] Tests cover various rotation angles and edge cases
- [ ] Script handles errors gracefully
```

### Example 2: Fix branch behind main

**Input:**

- Branch: `fix/broken-tests`
- Commits: "Fix pytest configuration"
- Behind main by 3 commits

**Output:**

```
Created Jira story DX-1235: Fix broken tests

Note: Your branch is 3 commits behind main. Consider rebasing with: `git rebase origin/main`
```

## References

- [Story Template Guide](references/story-template.md) - Detailed guidance on story structure and content generation

## Troubleshooting

**"No commits found":**

- Ensure you have commits on your branch that aren't on main
- Check if you're on the correct branch: `git branch --show-current`

**"Jira MCP server not configured":**

- Use <skill>mcp-setup</skill> to configure Jira MCP server
- Ensure you have proper Jira credentials

**"Branch naming doesn't match pattern":**

- Skill works best with `feature/*` or `fix/*` branches
- Other branch names will work but may need manual summary adjustment

**"jq command not found":**

- Install jq: `sudo apt-get install jq` (Linux) or `brew install jq` (Mac)
