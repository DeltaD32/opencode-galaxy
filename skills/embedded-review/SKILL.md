---
name: embedded-review
description: >-
  Perform detailed code reviews for embedded C/C++ systems. Provides review
  criteria, output format, and embedded constraints as reusable references.
  Language-agnostic on C++ standard (caller specifies C++14/17/20).
  Use when reviewing embedded code, auditing firmware, or checking C/C++ PRs
  against embedded best practices. Triggers on "review embedded code",
  "embedded C++ review", "firmware review", or requests to review code that
  runs on microcontrollers or ECUs.
license: Proprietary
compatibility: Requires git and access to the codebase being reviewed. Optionally requires uv and gh CLI for posting comments via pr-review.
metadata:
  authors:
    - Johannes Hermann <johannes.jh.hermann@bmw.de>
  version: "1.0.0"
  tags:
    - c++
    - embedded
    - code review
    - firmware
    - ECU
    - memory safety
    - real-time
    - static analysis
---

# Embedded C/C++ Code Review

Perform thorough code reviews for embedded C/C++ systems with a focus on
memory safety, real-time correctness, and hardware constraints.

## Goal

Provide a structured, reusable code review framework for embedded C/C++
projects. The skill supplies review criteria, output format conventions,
embedded constraints, and a context contract — but **no scripts**. For
posting review comments to GitHub, use the **pr-review** skill's
`add_pr_comment.py`. For large review outputs, use the **file-handoff** skill.

## When to Use

- Reviewing pull requests that touch embedded C/C++ code
- Auditing firmware or ECU software for quality and safety
- Performing code reviews against embedded best practices
- When an agent needs structured review criteria for embedded systems

## Prerequisites

Install required skills from [DX Skills](https://bmw.ghe.com/DX/skills):

| Skill                   | Required    | Purpose                                                                                       |
| ----------------------- | ----------- | --------------------------------------------------------------------------------------------- |
| **pr-review**           | Yes         | `add_pr_comment.py` for posting inline review comments, `review-guide.md` as base methodology |
| **file-handoff**        | Recommended | Use when review output is large — write to file, pass pointer                                 |
| **resolve-pr-comments** | Optional    | Use after review to address feedback and resolve threads                                      |

## Related Skills

| Skill                   | Relationship                                                                                               |
| ----------------------- | ---------------------------------------------------------------------------------------------------------- |
| **pr-review**           | Reuse `add_pr_comment.py` for posting inline review comments. Reuse `review-guide.md` as base methodology. |
| **file-handoff**        | Use when review output is large. Write to file, pass pointer.                                              |
| **resolve-pr-comments** | Use after review to address feedback and resolve threads.                                                  |

## Inputs

The caller (agent or user) should provide:

| Input              | Required | Description                                                             |
| ------------------ | -------- | ----------------------------------------------------------------------- |
| PR number or diff  | Yes      | The code to review                                                      |
| C++ standard       | No       | e.g., C++14, C++17, C++20. Defaults to C++17 if unspecified.            |
| Domain constraints | No       | Additional constraints beyond the defaults in `embedded-constraints.md` |
| Source directory   | No       | Directory to examine for coding style (e.g., `apps/climate/`)           |
| Context file       | No       | Path to a review-context file (see `review-context-contract.md`)        |

## Steps

### 1. Load References

Read the following reference docs from this skill before starting:

- `references/review-criteria.md` — What to look for
- `references/review-format.md` — How to format output
- `references/embedded-constraints.md` — Embedded-specific constraints

If a context file is provided, also read:

- `references/review-context-contract.md` — Expected structure of orchestrator input

### 2. Fetch the PR

```bash
git fetch origin pull/<PR_NUMBER>/head
git --no-pager diff origin/master...FETCH_HEAD
```

Do not rebase — review the diff as-is. If the PR is behind `origin/master`,
mention it as a risk.

### 3. Examine Coding Style

If a source directory is provided, examine the existing codebase in that
directory to understand the project's coding conventions. Apply those
conventions in your review.

### 4. Perform the Review

Apply the criteria from `review-criteria.md` with the constraints from
`embedded-constraints.md`. Use the caller-specified C++ standard.

Review strategy:

- Consider the broader codebase when reviewing (fetch referenced files for context)
- Trace each addition/removal to assess impact on other components
- Infer the requirements being implemented and assess architectural compliance
- Do not invent line numbers — verify via `git --no-pager show` or open the file

### 5. Format Output

Format per `references/review-format.md`. If a `Review Output File:` path is
provided, write output incrementally to that file (see format reference for
the file-writing protocol).

### 6. Post Comments (optional)

If a `Review Comments File:` path is provided, generate a JSON file for
inline PR comments (see format reference for JSON schema). Then use
**pr-review**'s `add_pr_comment.py` to post:

```bash
uv run /path/to/skills/pr-review/scripts/add_pr_comment.py <PR_NUMBER> \
  --review /path/to/review-comments.json --event PENDING
```

## Troubleshooting

| Issue                        | Solution                                                                     |
| ---------------------------- | ---------------------------------------------------------------------------- |
| PR cannot be fetched         | Verify remote URL and PR number. Check `git remote -v`.                      |
| Large review causes timeout  | Use `Review Output File:` with incremental appends (see `review-format.md`). |
| Line numbers don't match     | Always verify with `git --no-pager diff` — never guess line numbers.         |
| Missing coding style context | Ask the caller to specify a source directory to examine.                     |
