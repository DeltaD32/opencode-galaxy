---
name: file-handoff
description: >-
  Moves large context or output safely through a workflow by writing payloads
  to disk, passing only file pointers to downstream agents or tools, and
  preferring file-based inputs over large inline parameters. Use when reviews,
  reports, prompts, comments, or generated artifacts are large enough to risk
  transport timeouts or oversized tool parameters.
license: Proprietary
compatibility: >-
  Requires local filesystem access and tools or agents that can read from files
  or accept file-based input flags such as --body-file, --input-file, or
  @file syntax.
metadata:
  author: Johannes Hermann <johannes.jh.hermann@bmw.de>
  version: "1.0.0"
  tags:
    - handoff
    - large-payload
    - timeout
    - orchestration
---

# file-handoff

## Steps

### 1. Decide whether file handoff is needed

Before composing a large prompt or tool call, ask:

- Is this content larger than roughly 200 lines or 8 KB?
- Will another step or tool need this content, and can it read from a file?

If the answer to any of these is yes, switch to file handoff immediately.

### 2. Choose a file location

Prefer a temporary but durable working location such as:

- Copilot session-state folder
- a temp directory for the current task
- a dedicated workspace scratch directory

Use absolute paths whenever the file will be referenced by another agent or tool.

Suggested file names:

- `context.md`
- `review-context.md`
- `review-result.md`
- `report.md`
- `payload.json`
- `request-body.md`

### 3. Write the content to disk

For small-to-medium content, a single write is fine.

For large content, write incrementally:

1. Initialize the file with the first section
2. Append one logical section at a time
3. Keep each append under 50 lines
4. Verify the file exists and is non-empty

Prefer this pattern:

```bash
cat > /abs/path/to/context.md <<'EOF'
## Summary
Brief description of the task or context.
EOF

cat >> /abs/path/to/context.md <<'EOF'
## Details
- First piece of information
- Second piece of information
EOF
```

Avoid the following patterns:

- one huge heredoc containing the entire file
- a giant string parameter passed through a model tool call
- repeatedly reconstructing the same large markdown body

### 4. Pass only a small pointer downstream

If invoking another agent, keep the prompt tiny and point to the file:

```text
Context File: /abs/path/to/context.md
```

Do not duplicate the file contents in the prompt.

If the downstream step needs an output destination too, include that pointer as well:

```text
Context File: /abs/path/to/context.md
Output File: /abs/path/to/result.md
```

### 5. Prefer file-based tool interfaces

When available, prefer interfaces such as:

- `gh pr comment --body-file /abs/path/to/review-result.md`
- `curl --data-binary @payload.json ...`
- `tool --input-file /abs/path/to/context.md`
- `command < /abs/path/to/input.txt`

If a tool only supports inline parameters:

- use it only for small payloads
- otherwise look for an alternative CLI, script, or workflow that accepts files

### 6. Keep outputs on disk too

If the downstream agent or tool generates a large result:

- instruct it to write directly to an output file
- confirm the file was created successfully
- summarize the result briefly instead of reprinting the whole artifact

Example verification:

```bash
test -s /abs/path/to/result.md && echo "OK" || echo "MISSING"
```

### 7. Reuse the file, do not paste its content back inline

Once the file exists on disk:

- link to it
- summarize it
- post it using file-based commands
- archive or clean it up when the workflow is done

Do not read the full file back into a model parameter unless you need a short, targeted excerpt.

## Guardrails

- Do **not** embed a large file into a downstream prompt after writing it to disk
- Do **not** re-output a large generated artifact just to show it again
- Do **not** claim a file-based workflow is complete until the file exists and is non-empty
- Do **not** use large inline body parameters when a `--body-file` or equivalent exists
- Do **not** build very large files as a single giant heredoc if incremental writes are practical
- Do **not** leave the next step guessing where the file is; always print or
  pass the full absolute path

## Examples

### Example 1: Delegate a large review brief to another agent

**Bad approach**

- Build a huge prompt containing ticket summary, comments, attachments, and review checklist
- Send the entire prompt inline to the specialist review agent

**Good approach**

1. Write `review-context.md` to disk
2. Append sections incrementally
3. Invoke the reviewer with only:

```text
Context File: /abs/path/to/review-context.md
```

4. Ask the reviewer to write to:

```text
Output File: /abs/path/to/review-result.md
```

### Example 2: Post a long PR review without passing it as a giant parameter

Instead of sending the full review body through a tool parameter, write it to disk and use:

```bash
gh pr comment 123 \
  --repo owner/repo \
  --body-file /abs/path/to/review-result.md
```

This keeps the model from re-emitting the full markdown body and avoids transport timeouts.

## Troubleshooting

### The workflow still times out

- Check whether you are still embedding the file contents in a later prompt
- Check whether you are passing the full body as a tool parameter anyway
- Split file creation into smaller append operations
- Switch to a CLI or script that reads from a file directly

### The downstream agent ignores the file

- Make the prompt explicit and minimal
- Use a clear pointer such as `Context File: /abs/path/to/context.md`
- Ensure the path is absolute and readable
- If needed, include both input and output file paths

### The output file was not created

- Verify the destination directory exists
- Verify write permissions
- Add an explicit post-step file existence check
- Stop and report the failure instead of silently continuing
