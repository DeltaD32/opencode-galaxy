---
name: bmw-wisdom
description: Append one BMW-style management wisdom quote to the end of substantial completion messages by selecting it from a locally synced snapshot of the bmw_sprueche repository.
license: Proprietary
compatibility: Python 3.11+ and uv are optional (enhanced context-aware mode only). Refreshing the local sayings snapshot also requires gh CLI access to cc-github.bmwgroup.net.
metadata:
  author: Johannes Hermann <johannes.jh.hermann@bmw.de>
  version: "1.0.1"
  tags:
    - bmw
    - sayings
    - humor
    - completions
    - prompt-finishing
---

# bmw-wisdom

## Goal

Append exactly one BMW-style saying to the end of a substantial completion message without getting in the way of the actual answer.

## When to Use

- The user explicitly asks for BMW sayings, BMW-style wrap-ups, or playful closing lines
- The `<prompt>bmw-wisdom</prompt>` prompt is active
- You are finishing a substantial task, code review, implementation summary, or agent completion summary

## When **Not** to Use

- You are only asking a clarifying question
- The reply is just a short acknowledgement or status ping
- The message is purely about an error/failure and playful tone would distract from it
- The user asked for a strict or formal tone

## Source of Truth

- Use the local snapshot in `references/quotes.json`
- Do **not** invent or paraphrase sayings unless the user asks for that
- The snapshot is sourced from:
  - `https://cc-github.bmwgroup.net/markusfidorra/bmw_sprueche`
  - `README.md`
  - `bmw_schulungen.md`

If the user asks to refresh the sayings from upstream, run the bundled sync helper from the skill directory:

- **macOS / Linux / bash**
  ```bash
  cd "<SKILL_DIR>" && uv run scripts/sync_sayings.py
  ```
- **Windows / PowerShell**
  ```powershell
  Set-Location "<SKILL_DIR>"; uv run scripts/sync_sayings.py
  ```

Review the resulting diff before committing because upstream sayings may change.

## Selecting a Saying

There are two selection modes. Use **simple mode** by default; use **enhanced mode** only when shell commands are known to run without user confirmation (e.g. the tool is already approved for the session or the user is in auto-approve / yolo mode).

### Simple Mode (default — no shell required)

1. Read `references/quotes.json` directly using file-reading tools (view / read)
2. Pick one quote **at random** from the `quotes` array
3. Do **not** run any shell command — this avoids the confirmation prompt

This mode has no context-awareness or repeat tracking, but it is frictionless.

### Enhanced Mode (context-aware — requires shell permission)

Use this mode **only** when you are confident that `uv` / Python commands will execute without prompting the user for confirmation. Indicators that this is the case:

- You have already successfully run `uv` or `python` shell commands in the current session without being blocked or prompted
- The user has explicitly enabled auto-approve / yolo mode

Run the bundled selector helper from the skill directory:

- **macOS / Linux / bash**
  ```bash
  cd "<SKILL_DIR>" && uv run scripts/select_saying.py --context "<one-line task summary>"
  ```
- **Windows / PowerShell**
  ```powershell
  Set-Location "<SKILL_DIR>"; uv run scripts/select_saying.py --context "<one-line task summary>"
  ```

Guidance for the `--context` text:

- Keep it short, e.g. `finished pull request cleanup for skill repo`
- Prefer a short summary of what just completed
- The helper uses the context only as a soft preference, not as a strict match
- It remembers the last 40 used quotes in local Copilot state and avoids repeating them when possible
- Even for coding- and PR-heavy workflows, the full sayings set can still surface over time

### When in doubt

Prefer **simple mode**. A random quote is better than a confirmation prompt that interrupts the user's flow.

## Output Format

After the main completion message, append exactly one final line in this format:

```text
BMW wisdom quote: <selected saying>
```

Rules:

- Add one blank line before the saying
- Append only one saying
- Put the saying at the very end of the response
- Keep the selector output quoted so it is visibly a quoted BMW wisdom line
- Keep the main answer useful even if the saying is removed

## References

- `references/quotes.json` — locally synced quotes snapshot
- `scripts/sync_sayings.py` — refresh the snapshot from upstream
- `scripts/select_saying.py` — choose one saying for the current context
