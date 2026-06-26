# Review Context Contract

When an orchestrator (e.g., a review-orchestrator agent) prepares context
for the embedded-review skill, it should write a **context file** with
the following structure. The reviewer reads this file as its primary input.

## How to Pass the Context File

Include this line in the prompt to the reviewer:

```
Context File: /abs/path/to/review-context.md
```

The reviewer will read that file first and treat it as the authoritative
source of requirements and PR coordinates.

## Optional Output Pointers

The context file may also include these lines to control where the reviewer
writes its output:

```
Review Output File: /abs/path/to/review-result.md
Review Comments File: /abs/path/to/review-comments.json
```

- **Review Output File**: The reviewer writes the full markdown review here
  (using incremental appends — see `review-format.md`).
- **Review Comments File**: The reviewer writes a JSON file for inline PR
  comments (compatible with `pr-review`'s `add_pr_comment.py`).

If these lines are absent, the reviewer returns the review in the chat response.

## Required Sections

### Ticket

```markdown
## Ticket

- **ID**: IPBD-12345
- **Summary**: Short description of the ticket
- **Description**: Full ticket description (or relevant excerpt)
```

### Derived Requirements

```markdown
## Derived Requirements

- Functional: What the code must do
- Implementation: How it should be done (constraints, patterns)
```

### Review Checklist

```markdown
## Review Checklist

- [ ] Requirement A is implemented correctly
- [ ] Requirement B handles edge case X
- [ ] No regressions in module Y
```

The reviewer must explicitly address each checklist item with concrete code
evidence (file paths and verified line references).

### PR

```markdown
## PR

- **Number**: 1234
- **Link**: https://github.example.com/org/repo/pull/1234
- **Base branch**: master
- **Fetch command**: `git fetch origin pull/1234/head`
- **Diff command**: `git --no-pager diff origin/master...FETCH_HEAD`
```

## Optional Sections

### Key Comments

```markdown
## Key Comments

- Implementation hints from ticket comments
- Clarifications from discussions
```

### Attachments

```markdown
## Attachments

- `diagram.png` — Architecture diagram (parsed / not parsed)
- `spec.pdf` — Requirements specification (summary: ...)
```

### Assumptions / Risks

```markdown
## Assumptions / Risks

- Embedded constraints apply (no dynamic allocation)
- Context gap: requirement X is ambiguous
- PR is N commits behind master
```

### Domain-Specific Overrides

```markdown
## Domain Overrides

- **C++ Standard**: C++14
- **Source directory for style reference**: apps/climate/
- **Additional constraints**: (any domain-specific rules)
```

This section allows domain-specific agents to inject their overrides without
modifying the skill itself.
