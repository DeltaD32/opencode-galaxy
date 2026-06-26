---
name: pdf-chat
description: >
  Chat with PDF documents using BMW LLM API and Anthropic Claude models.
  Encodes a local PDF as a base64 data URL and sends it alongside a question
  or instruction to Claude. Use when the user wants to summarise, query,
  extract data from, or ask questions about a PDF file.
  Trigger phrases: "summarise this PDF", "ask a question about a PDF",
  "extract data from PDF", "analyse document", "read this PDF", "chat with PDF",
  "what does this document say".
license: Proprietary
metadata:
  authors:
    - OpenCode Config
  version: "1.1.0"
  tags:
    - pdf
    - multimodal
    - document
    - claude
    - bmw-llm-api
---

# pdf-chat

Send a local PDF to Claude on the BMW LLM API and get a free-text or structured
answer. The module is pre-installed at `~/.opencode/skills/pdf-chat/pdf_chat.py`
— **no code generation needed**.

## Python path

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path.home() / ".opencode/skills/pdf-chat"))
from pdf_chat import ask_pdf, ask_pdf_stream
```

Use the clipjoint venv: `~/.opencode/plugins/clipjoint/.venv/bin/python3`

## API

```python
# Simple Q&A
answer = ask_pdf("report.pdf", "What are the three main conclusions?")
print(answer)

# Streaming (progressive output)
for chunk in ask_pdf_stream("report.pdf", "Summarise key findings."):
    print(chunk, end="", flush=True)
print()
```

Both functions share the same signature:

```python
ask_pdf(
    pdf_path: str,
    question: str,
    system:     str = "You are a helpful assistant...",  # optional
    model:      str = "anthropic/claude-haiku-4-5",      # optional
    max_tokens: int = 1024,                              # optional
) -> str
```

## Constraints

| Limit | Value |
|---|---|
| Max file size | **10 MB** per PDF |
| Supported models | `claude-haiku-4-5`, `claude-sonnet-4`, `claude-sonnet-4-5`, `claude-sonnet-4-6` |
| Multi-turn | Pass prior messages in `messages` array directly to `_client()` |

Only Claude models support PDF uploads — GPT and Gemini will return `400 Bad Request`.

## Steps for the agent

1. Confirm the PDF path — ask user if not already provided.
2. Check file size — `pdf_to_data_url()` raises `ValueError` if > 10 MB.
3. Choose model — default `claude-haiku-4-5` for speed; `claude-sonnet-4-6` for complex docs.
4. Call `ask_pdf()` — pass the user's question verbatim.
5. Return the answer directly.

## Structured output pattern

For typed extraction, use `_client()` with `client.chat.completions.parse()` and a
Pydantic `response_format`. See `pdf_chat.py` for the `_client()` helper signature.

## Error handling

| Symptom | Cause | Fix |
|---|---|---|
| `ValueError: PDF is X.X MB` | Exceeds 10 MB | Extract pages with `pypdf` first |
| `400 Bad Request` | Non-Claude model | Switch to `claude-haiku-4-5` |
| `SSL certificate verify failed` | CA bundle missing | Set `BMW_CA_BUNDLE` env var |
| Empty/garbled answer | Scanned/image PDF | Quality varies; consider OCR pre-processing |
