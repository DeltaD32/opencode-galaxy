---
description: "AAA — Explain GHAS or Wiz security findings in detail. Read-only, no code changes."
agent: aaa-security-fixer
---

Explain security findings using the AAA (AST Agentic Approach). Read-only — no code changes made.

Usage: `/security-explain $ARGUMENTS`

Where `$ARGUMENTS` is `target=ghas`, `target=wiz`, a specific finding ID, or leave blank for an overview of all open findings.

Delegate to the `aaa-security-fixer` agent to:
1. Retrieve the specified finding(s).
2. For each: explain the vulnerability type, severity, attack path, and affected code.
3. Describe remediation options with examples — but do NOT apply any changes.
4. Summarise the overall security posture.
