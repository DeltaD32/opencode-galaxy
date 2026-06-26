# Jira Story Template Reference

This document provides guidance on creating well-structured Jira stories for ad-hoc work.

## Story Structure

### Summary

Brief, action-oriented title that describes what was done.

**Format patterns:**

- Feature work: "Add [feature/capability]"
- Bug fixes: "Fix [issue/problem]"
- Improvements: "Improve [aspect]"
- Documentation: "Update [documentation aspect]"

**Examples:**

- "Add Jira ticket creation skill"
- "Fix broken pytest configuration"
- "Improve README documentation"
- "Update pre-commit hooks"

### Description

A comprehensive explanation that includes:

1. **Context**: Why this work was needed
2. **Changes**: What was actually done
3. **Impact**: How this affects the project

**Template:**

```
## Context
[Why was this work needed? What problem does it solve?]

## Changes Made
[List the key changes implemented]
- Change 1
- Change 2
- Change 3

## Impact
[How does this affect users, the codebase, or the project?]
```

**Example:**

```
## Context
Team members frequently work on ad-hoc tasks that don't have pre-existing Jira tickets.
This makes it difficult to track work and maintain proper documentation.

## Changes Made
- Created new skill for generating Jira stories from branch analysis
- Implemented branch analysis script to extract commits and changes
- Added support for detecting if branch needs rebasing
- Integrated with Jira MCP server for ticket creation

## Impact
- Improves work tracking for ad-hoc tasks
- Ensures all work is properly documented in Jira
- Reduces manual effort in creating retrospective tickets
```

### Acceptance Criteria

Clear, testable conditions that define when the work is complete.

**Format:**

```
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
```

**Guidelines:**

- Use concrete, measurable statements
- Focus on outcomes, not implementation details
- Make them testable (can verify if done)
- Usually 3-5 criteria per story

**Example:**

```
- [ ] Script successfully analyzes current branch and identifies commits
- [ ] Jira story is created with summary derived from branch work
- [ ] Description includes context from commit messages
- [ ] User is notified if branch needs rebasing
- [ ] Story includes auto-generated acceptance criteria based on changes
```

## Deriving Story Content from Commits

### Analyzing Commit Messages

Look for patterns in commit messages to understand the work:

**Common commit prefixes:**

- `feat:` → Feature work
- `fix:` → Bug fixes
- `docs:` → Documentation updates
- `test:` → Test additions/fixes
- `refactor:` → Code restructuring
- `chore:` → Maintenance tasks

### Grouping Related Changes

Analyze file changes to identify themes:

**File patterns:**

- Multiple files in same directory → Feature/module work
- Test files + source files → Implementation with tests
- Documentation files only → Documentation work
- Configuration files → Setup/tooling work

### Generating Acceptance Criteria

Base criteria on what was actually implemented:

**From commits:**

- If tests were added → "Tests pass successfully"
- If docs updated → "Documentation is accurate and complete"
- If feature added → "Feature works as expected"
- If fix applied → "Issue no longer occurs"

**From file changes:**

- New files created → "New [component] is functional"
- Files deleted → "Deprecated [component] is removed"
- Files modified → "Changes to [component] are working"

## Quality Checklist

Before creating the story, ensure:

- [ ] Summary is concise (< 100 characters) and action-oriented
- [ ] Description provides sufficient context
- [ ] Description lists the actual changes made
- [ ] Acceptance criteria are measurable and testable
- [ ] Story type is set to "Story" (not Task or Bug)
- [ ] Project is correctly set
- [ ] Labels/components are added if mentioned in commits/files
