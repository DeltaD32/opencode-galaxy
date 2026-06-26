---
name: deep-web-research
version: "1.1.0"
description: Run broad or high-stakes public web research through parallel research lanes, rerank merged findings with cohere/rerank-3-5, then return only a compact synthesis packet to the main agent. Use when the question is complex enough that raw search/fetch output would pollute the main context.
metadata:
  authors:
    - Kristaps Dreija <Kristaps.Dreija@bmw.de>
  tags:
    - research
    - web
    - brave-search
    - parallel
    - rerank
    - cohere
deps:
  internal: [bravesearch, web-research]
  external: []
---

# Deep Web Research

## Overview

Escalation path from `web-research` for broad, comparison-heavy, or
context-polluting topics. Split work into parallel research lanes and return
only a compact synthesis packet to the main agent.

## When to Use

- Topic needs multiple search angles or competing solution spaces
- Answer requires comparing products, frameworks, or architectures
- Source bias is likely and you want explicit corroboration / disconfirmation
- Reading many pages would pollute the main context

## When NOT to Use

- Simple `web-research` pass over 2–5 sources is enough
- User gave the exact URL to read
- Work is entirely in local repo or internal systems

## Workflow

```
Question → LaneDesign → ParallelLanes → EvidencePackets → Synthesis → CompactAnswer
```

## Step 1 — Design 3–5 parallel lanes

Common lane types: `primary-docs`, `implementation-examples`,
`comparison-alternatives`, `skepticism-disconfirmation`, `freshness-news`.

Use the template at: `references/research-lane-subagent.md`

## Step 2 — Run lanes in parallel as Task subagents

```text
Task(description="Primary docs lane",        subagent_type="general", prompt="<filled template>")
Task(description="Implementation evidence",  subagent_type="general", prompt="<filled template>")
Task(description="Alternatives lane",        subagent_type="general", prompt="<filled template>")
Task(description="Skeptic lane",             subagent_type="general", prompt="<filled template>")
```

Each lane: searches with `bravesearch`, opens top pages, returns compact JSON packet.
See result schema at: `references/research-lane-result-template.json`

## Step 3 — Rerank merged findings (Step 4b)

The `reranker.py` module is pre-installed — **no code generation needed**.

```python
import sys, pathlib, asyncio
sys.path.insert(0, str(pathlib.Path.home() / ".opencode/skills/deep-web-research"))
from reranker import rerank_findings

all_findings = lane1["key_findings"] + lane2["key_findings"] + lane3["key_findings"]

# Async (preferred — call from async context or wrap with asyncio.run):
top_findings = await rerank_findings(user_question, all_findings, top_n=8)
# or:
top_findings = asyncio.run(rerank_findings(user_question, all_findings, top_n=8))
```

**Skip reranking when:** total merged findings ≤ 8, or all lanes returned the same 2–3 facts.

## Step 4 — Synthesise

Use `top_findings` in the synthesis prompt:

```python
synthesis_context = "\n".join(f"- {f}" for f in top_findings)
synthesis_prompt  = f"""
You are synthesising parallel research lanes into a single compact answer.
User question: {user_question}
Top-ranked findings:
{synthesis_context}
Return: proposed_answer, key_findings (5–8), confidence (0–1), confidence_reason, open_questions.
"""
```

## Required output contract

The merged result back to the main agent must contain **only**:
`proposed_answer`, `key_findings` (5–10), `references`, `confidence`,
`confidence_reason`, `open_questions`, `follow_up_queries`.

Do not pass raw page dumps or full search logs to the main context.

## Bias check rules

- Dedicate at least one lane to disconfirmation
- Prefer primary docs over vendor blogs
- If sources are weak, lower confidence rather than forcing a strong answer

## Error handling

- Lane fails → keep result, lower confidence
- Multiple lanes → same weak source family → note circular sourcing risk
- Too narrow for parallelisation → fall back to `web-research`
