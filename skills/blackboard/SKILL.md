---
name: blackboard
description: >
  Shared working file coordination for multi-agent tasks. Creates and manages
  blackboard files where specialists write analysis and proposed changes, and
  the worker agent executes the resulting plan. Use when 2+ specialist domains
  are involved, the task is high-stakes/multi-file, or the user requests a
  plan before execution.
tags: [coordination, multi-agent, blackboard, planning]
license: Proprietary
metadata:
  authors:
    - OpenCode Config
  version: "1.0.0"
---

# blackboard

Coordinate multi-agent tasks through a shared working file. Specialists write
analysis and diffs; the orchestrator assembles an Execution Plan; the worker
executes it and writes the result. Named after the classical Blackboard
Architecture from 1970s AI research.

## Python path

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path.home() / ".opencode/skills/blackboard"))
from blackboard import (
    create, append_section, read, get_section,
    mark_status, list_sections, is_ready_for_execution,
    archive, get_active_blackboards,
)
```

Use the clipjoint venv: `~/.opencode/plugins/clipjoint/.venv/bin/python3`

## Function reference

| Function | Returns | Description |
|---|---|---|
| `create(task_description, context, project_id=None)` | `str` | Create new blackboard file. Returns absolute file path. |
| `append_section(file_path, agent, section_name, content)` | `None` | Append a section. Replaces if section already exists (idempotent). |
| `read(file_path)` | `str` | Read full blackboard content. |
| `get_section(file_path, section_name)` | `str \| None` | Extract one section's body text. Returns `None` if absent. |
| `mark_status(file_path, status)` | `None` | Update the Status line. Valid values: see Status Values below. |
| `list_sections(file_path)` | `list[str]` | Section names in document order. |
| `is_ready_for_execution(file_path)` | `bool` | True if `## Proposed Changes` exists and is non-empty. |
| `archive(file_path)` | `str` | Move file to archive dir. Returns new absolute path. |
| `get_active_blackboards()` | `list[dict]` | List all active blackboards. Each dict: `{path, task, status, created, project}`. |

## Status values

| Status | Meaning |
|---|---|
| `deliberating` | Specialists are writing their sections (default on create) |
| `awaiting-approval` | Execution Plan written; waiting for user sign-off |
| `executing` | Worker agent is applying the plan |
| `done` | Worker completed successfully |
| `blocked` | A step failed; worker stopped; see `## Execution Result` |

## Blackboard file format

Files live in `/tmp/opencode/task-YYYYMMDD-NNN.md`.
IDs are sequential per day: `task-20260625-001`, `task-20260625-002`, etc.

**Header (written by `create()`):**
```markdown
# Task: <task_description>
**ID:** task-YYYYMMDD-NNN
**Status:** deliberating
**Created:** <ISO 8601 timestamp>
**Project:** <project_id or "standalone">

## Context
<context>
```

**Sections (written by `append_section()`):**
```markdown

## <section_name>
**Author:** <agent>
**Written:** <ISO timestamp>

<content>
```

**Archive directory:** `~/.local/share/opencode/blackboards/archive/`

## Coordination flow

```
1. Orchestrator creates blackboard
   path = create(task_description, context, project_id)

2. Delegate to each specialist with the blackboard path
   "Write your analysis to the blackboard at <path>"

3. Specialists write their sections
   append_section(path, "programming-expert", "Programming Analysis", "...")
   append_section(path, "programming-expert", "Proposed Changes", "```diff\n...")
   append_section(path, "design-expert", "Design Constraints", "...")

4. Orchestrator reviews all sections
   full_content = read(path)
   sections = list_sections(path)
   ready = is_ready_for_execution(path)

5. Orchestrator writes the execution plan
   append_section(path, "request-orchestrator", "Execution Plan", "...")

6. [Optional] Gate on approval
   mark_status(path, "awaiting-approval")
   # Wait for user to confirm, then:

7. Delegate to worker
   mark_status(path, "executing")
   task(subagent_type="worker", prompt=f"Execute the plan in blackboard at {path}")

8. Worker writes result and updates status
   append_section(path, "worker", "Execution Result", "Pass/fail + test output")
   mark_status(path, "done")  # or "blocked" if a step failed

9. [Phase 3] Secretary records to opencode.db project tables
   archive(path)  # after DB record is written
```

## Hard rules for specialists

1. **`## Proposed Changes` MUST contain exact unified diffs or complete code blocks.**
   Prose descriptions are a protocol violation — the worker cannot execute them.
   - ✅ `\`\`\`diff\n-old line\n+new line\n\`\`\``
   - ✅ Complete replacement file content in a fenced code block
   - ❌ "Change the button to use touch-action: none" (prose — rejected)

2. **Never write to another specialist's section.** Each agent owns its own sections.

3. **`append_section()` is idempotent.** Safe to re-run — it replaces the existing
   section rather than duplicating it.

4. **`## Execution Plan` is written by the orchestrator only**, after reviewing
   all specialist sections and resolving conflicts via the secretary if needed.

5. **`## Execution Result` is written by the worker only**, after execution.

## Activation conditions (when to use blackboard)

| Condition | Use blackboard? |
|---|---|
| 2+ specialist domains involved | ✅ Yes |
| High-stakes / multi-file change | ✅ Yes |
| User requests "plan first" / "dry run" / "show me the plan" | ✅ Yes |
| Keywords: delete, migrate, breaking change, production | ✅ Yes |
| Single clear specialist, simple task | ❌ No — fast path |
| User says "just do it" or `/beast-mode` | ❌ No — skip blackboard |

## Phase 3 note (future)

`blackboard.py` is designed to feed `opencode.db` project tables in Phase 3.
The `project_id` parameter on `create()` maps to `blackboards.project_id`.
Section writes via `append_section()` map to the `sections` table.
See `~/.config/opencode/docs/PROJECTS-DB.md` for the full schema.
