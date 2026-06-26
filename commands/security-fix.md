---
description: "AAA — Autonomously fix GHAS or Wiz Code security findings. Pass target=ghas or target=wiz as argument."
agent: aaa-security-fixer
---

Fix security findings using the AAA (AST Agentic Approach).

Usage: `/security-fix $ARGUMENTS`

Where `$ARGUMENTS` is `target=ghas`, `target=wiz`, a specific CodeQL rule ID, or a Wiz Issue ID.

Delegate to the `aaa-security-fixer` agent to:
1. Retrieve all open findings for the specified platform (GHAS or Wiz Code).
2. For each finding: fetch full context, understand the vulnerability, implement the minimal correct fix.
3. Run CodeQL or Wiz CLI to verify zero findings remain after each fix.
4. Commit fixes with messages referencing the finding ID.
5. Report a summary of all findings resolved.
