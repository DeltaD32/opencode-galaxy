---
name: pr-creation
description: Creates well-structured pull requests using gh CLI, validates against PR templates, checks ticket alignment, and suggests branch splits for unrelated changes. Use when creating PRs, submitting changes, or when the user asks to open, create, or submit a pull request.
license: Proprietary
compatibility: Requires gh CLI (GitHub CLI) installed and authenticated. Requires git repository with remote configured.
metadata:
  author: Matthias Bilger <matthias.bilger@bmw.de>
  version: "1.0.1"
  tags:
    - git
    - github
    - pull-request
    - pr
    - workflow
    - code-review
  memory:
    read:
      - current-ticket.md
---

# pr-creation

## Goal

Create a well-structured, comprehensive pull request that fulfills PR template requirements, maintains clear descriptions, and ensures changes align with referenced tickets or issues.

## When to use

- User asks to "create a PR", "open a pull request", "submit changes", or similar
- User wants to push changes and create a PR in one workflow
- User mentions creating a PR with proper formatting or validation
- Changes are ready for review and need to be submitted

## Inputs

- Current git branch with committed changes
- Optional: ticket/issue number or reference
- Optional: Current ticket from memory file (`.ttt/memory/current-ticket.md`)
- Optional: PR template location (defaults to `.github/pull_request_template.md`)
- Optional: target branch (defaults to `main` or default branch)

## Outputs

- Pull request created on GitHub with:
  - Well-structured title and description
  - All PR template checklist items addressed
  - Clear summary of what changed and why
  - Testing instructions when applicable
  - Proper labels and metadata
- Validation report if changes don't align with referenced ticket
- Suggestion for branch split if unrelated changes detected

## Steps

1. **Validate prerequisites**

   - Check gh CLI is installed and authenticated
   - Verify we're in a git repository
   - Confirm current branch has commits ahead of base branch
   - Check if current branch is already pushed to remote
   - Check access to JIRA MCP server. If this has not been setup use <skill>mcp-setup</skill>.

2. **Check for current ticket in memory**

   - Look for `.ttt/memory/current-ticket.md` file
   - If exists, read the ticket information
   - Ask user to confirm: "I found ticket {ticket-id} in memory. Is this the right ticket for this PR?"
   - If ticket info is minimal (just ticket ID), attempt to fetch full details from the ticket system (typically JIRA) for better validation
   - If user confirms, use this ticket for validation
   - If user declines, ask for the correct ticket. If the user does not have a ticket offer to create one and suggest to do so.
   - If no ticket is found in memory:
     - Ask the user if they want to provide a ticket reference for validation.
     - If the user does not want to provide a ticket reference, proceed without ticket validation but include a note in the PR description that no ticket reference was provided.
     - If this is a non-interactive session:
       - Check whether the user provided a ticket reference as an argument.
       - If no ticket reference argument is provided, stop, unless the user explicitly stated to create a PR without a ticket reference.
       - If the user explicitly stated to create a PR without a ticket reference, proceed but include a note in the PR description that no ticket reference was provided.

3. **Analyze changes**

   - Get diff between current branch and target branch
   - Identify modified files and their purposes
   - Extract commit messages for context
   - Detect if changes span multiple concerns

4. **Check for PR template**

   - Look for `.github/pull_request_template.md` or `.github/PULL_REQUEST_TEMPLATE.md`
   - Parse template structure (summary, checklist items, sections)
   - Identify required fields and checklist tasks
   - If there is no template include the following sections: Summary (Purpose), Changes, Tests performed.

5. **Validate ticket alignment** (if ticket reference provided)

   - Extract ticket number from branch name or user input
   - Retrieve ticket details using available tools (Jira MCP, GitHub issues, etc.)
   - Compare ticket description/requirements with actual changes
   - Flag any mismatches or additional scope

6. **Detect scope creep**

   - Analyze if changes address multiple unrelated concerns
   - Group changes by purpose/domain
   - Identify potential split points if changes are unrelated

7. **Ask user about scope mismatches** (if detected)

   - Present findings: "The ticket mentions X, but changes also include Y"
   - Suggest: "Would you like me to split the Y changes into a separate branch and PR?"
   - Wait for user decision before proceeding

8. **Generate PR description**

   - Create concise, scannable summary (2-3 sentences)
   - Fill in "What changed" section with bullet points
   - Add "How to test" section with clear reproduction steps
   - Complete checklist items with accurate checkmarks
   - Add notes section for context, caveats, or follow-ups
   - Include ticket reference in description if available

9. **Structure description for readability**

   - Use clear headings and bullet points
   - Keep paragraphs short (2-3 sentences max)
   - Use code blocks for commands, file paths, or snippets
   - Add whitespace between sections
   - Highlight breaking changes or migration steps if applicable
   - Never state tests have been performed without the user confirming it.

10. **Push branch if needed**

    - Push current branch to remote if not already pushed
    - Handle authentication or permission errors gracefully

11. **Create pull request**

    - Use `gh pr create` with generated title and body
    - Set appropriate labels based on change type (feature, bugfix, docs, etc.)
    - Link to related issues/tickets
    - Add reviewers automatically if they are specified by the user or detected from CODEOWNERS
    - Handle any errors during PR creation and provide actionable feedback
    - If no reviewers were added automatically, ask the user whether they want to add reviewers manually; if they confirm, ask for the reviewers and add them to the PR.

12. **Confirm success**
    - Show PR URL to user
    - Display PR number for reference
    - Provide quick-access commands for common next steps (viewing, editing, etc.)
    - Provide command to open the PR in the browser using `gh pr view --web`
    - Provide command to watch the PRs checks using `gh pr checks --watch`

## Examples

### Example 1: Simple PR creation

**User request:**

```text
Create a PR for these changes
```

**Agent actions:**

1. Analyzes current branch: `feature/update-readme`
2. Finds 1 file changed: `README.md`
3. No ticket reference detected
4. Loads PR template from `.github/pull_request_template.md`
5. Generates description:

```markdown
## Summary

Updated README.md to include installation instructions and troubleshooting section for common setup issues.

## What changed

- Added "Installation" section with step-by-step setup guide
- Added "Troubleshooting" section with solutions for common errors
- Fixed broken links to documentation
- Updated contributing guidelines

## How to test

1. Clone the repository
2. Follow installation steps in README.md
3. Verify all links work correctly

## Checklist

- [x] I created this PR against `main`
- [x] My commits have clear, imperative messages
- [x] I kept code/spec formatting consistent with the repo
- [x] CI is green (or I've explained why it isn't)
```

1. Pushes branch and creates PR
2. Returns: "Created PR #123: Update README with installation and troubleshooting"

### Example 2: PR with ticket from memory

**User request:**

```text
Create a PR
```

**Agent actions:**

1. Checks `.ttt/memory/current-ticket.md` and finds: `PROJ-456`
2. Asks user: "I found ticket PROJ-456 in your memory. Is this the right ticket for this PR?"
3. User confirms: "Yes"
4. Fetches full ticket details: "Add structured logging to API endpoints"
5. Analyzes current branch: `feature/add-logging`
6. Validates changes match ticket scope
7. Generates PR with ticket reference in description
8. Creates PR #123 with link to PROJ-456

### Example 3: PR with ticket validation and scope mismatch

**User request:**

```text
Create a PR for ticket PROJ-456
```

**Agent actions:**

1. User explicitly provided ticket PROJ-456 (overrides memory)
2. Analyzes current branch: `feature/proj-456-add-logging`
3. Retrieves ticket PROJ-456: "Add structured logging to API endpoints"
4. Detects changes:
   - API logging added ✓
   - Also found: Refactored database connection pooling ⚠️
5. Asks user:

   ```
   The ticket PROJ-456 is about adding logging, but I also see database
   connection pooling changes. These seem unrelated.

   Would you like me to:
   A. Include everything in one PR (with explanation)
   B. Split the database changes into a separate branch/PR
   ```

6. User chooses B
7. Creates new branch `feature/improve-db-pooling`, moves those commits there
8. Creates PR for logging changes only
9. Reminds user about the separate database PR that needs to be created

### Example 4: PR with template validation

**User request:**

```text
Open a pull request
```

**Agent actions:**

1. Checks `.ttt/memory/current-ticket.md` - not found
2. Analyzes changes across multiple files
3. Loads PR template and identifies required sections
4. Detects missing "How to test" information
5. Generates comprehensive testing instructions based on changed files
6. Ensures all checklist items are addressed
7. Creates PR with complete, well-structured description
8. Returns: "Created PR #124: Implement user authentication flow"

## Programmatic Usage

When you need PR analysis data as structured objects (e.g. to generate a description
programmatically before calling `gh pr create`), import `pr_helper` directly:

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path.home() / ".opencode/skills/pr-creation/scripts"))
from pr_helper import (
    analyze_changes,       # → ChangeAnalysis dataclass
    find_pr_template,      # → PRTemplate | None
    generate_pr_body,      # → str (markdown PR body)
    detect_ticket_from_branch,  # → str | None
    check_prerequisites,   # → bool
    get_current_branch,    # → str | None
    get_default_branch,    # → str
)

# Example: generate a PR body from current branch
if check_prerequisites():
    base = get_default_branch()
    analysis = analyze_changes(base)
    template = find_pr_template()
    title = f"feat: {analysis.branch_name}"
    body = generate_pr_body(analysis, template, title)
    print(body)
```

Or run the full interactive flow from the terminal:

```bash
~/.opencode/plugins/clipjoint/.venv/bin/python3 \
  ~/.opencode/skills/pr-creation/scripts/pr_helper.py

# With ticket validation
~/.opencode/plugins/clipjoint/.venv/bin/python3 \
  ~/.opencode/skills/pr-creation/scripts/pr_helper.py --ticket PROJ-123

# Auto-generate and create PR without prompts
~/.opencode/plugins/clipjoint/.venv/bin/python3 \
  ~/.opencode/skills/pr-creation/scripts/pr_helper.py --auto
```

## References

- [GitHub CLI PR creation documentation](https://cli.github.com/manual/gh_pr_create)
- [Writing good PR descriptions](references/pr-best-practices.md)
- [Handling scope creep](references/scope-detection.md)
