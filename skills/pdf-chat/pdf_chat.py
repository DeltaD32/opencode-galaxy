"""
pdf_chat.py
===========
Chat with PDF documents using the BMW LLM API and Anthropic Claude models.

Extracted from ~/.opencode/skills/pdf-chat/SKILL.md — single source of truth.
Import this module directly; do not regenerate this code inline.

Usage:
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path.home() / ".opencode/skills/pdf-chat"))
    from pdf_chat import ask_pdf, ask_pdf_stream

    answer = ask_pdf("report.pdf", "What are the three main conclusions?")
    for chunk in ask_pdf_stream("report.pdf", "Summarise key findings."):
        print(chunk, end="", flush=True)

Constraints:
    - Max file size: 10 MB per PDF
    - Only Claude models support PDF uploads (not GPT/Gemini)
    - Requires: LLM_API_BASE_URL, LLM_API_BEARER_TOKEN, LLM_API_KEY env vars
"""

from __future__ import annotations

import base64
import os
import pathlib

# openai + httpx are installed in the clipjoint venv
try:
    import httpx
    from openai import OpenAI
except ImportError as exc:
    raise ImportError(
        "pdf_chat requires 'openai' and 'httpx'. "
        "Use the clipjoint venv: ~/.opencode/plugins/clipjoint/.venv/bin/python3"
    ) from exc

_DEFAULT_CA = str(
    pathlib.Path.home() / ".opencode/plugins/clipjoint/BMW_Trusted_Certificates_Latest.pem"
)
_DEFAULT_MODEL  = "anthropic/claude-haiku-4-5"
_DEFAULT_SYSTEM = "You are a helpful assistant that answers questions about documents."
_MAX_MB         = 10


def _client() -> OpenAI:
    """Build a configured OpenAI client for BMW LLM API."""
    ca = os.environ.get("BMW_CA_BUNDLE") or _DEFAULT_CA
    return OpenAI(
        base_url=os.environ.get("LLM_API_BASE_URL",
                                "https://api.gcp.cloud.bmw/llmapi/v1"),
        api_key=os.environ.get("LLM_API_KEY", "unused"),
        http_client=httpx.Client(
            headers={"x-apikey": os.environ["LLM_API_KEY"]},
            verify=ca if pathlib.Path(ca).exists() else True,
        ),
        default_headers={"Authorization": f"Bearer {os.environ['LLM_API_BEARER_TOKEN']}"},
    )


def pdf_to_data_url(path: str) -> str:
    """
    Read a local PDF and return a base64 data URL.

    Raises ValueError if the file exceeds 10 MB.
    """
    data = pathlib.Path(path).read_bytes()
    mb = len(data) / 1_048_576
    if mb > _MAX_MB:
        raise ValueError(f"PDF is {mb:.1f} MB — BMW LLM API limit is {_MAX_MB} MB")
    return f"data:application/pdf;base64,{base64.b64encode(data).decode()}"


def ask_pdf(
    pdf_path: str,
    question: str,
    system: str = _DEFAULT_SYSTEM,
    model: str = _DEFAULT_MODEL,
    max_tokens: int = 1024,
) -> str:
    """
    Send a PDF + question to Claude and return the answer as a string.

    Args:
        pdf_path  : Path to the local PDF file (≤ 10 MB).
        question  : The question or instruction to send.
        system    : System prompt (default: document Q&A assistant).
        model     : Claude model to use. Only Claude models support PDFs.
        max_tokens: Maximum tokens in the response.

    Returns:
        The model's text response.

    Raises:
        ValueError  : If PDF exceeds 10 MB.
        KeyError    : If BMW LLM API env vars are not set.
    """
    completion = _client().chat.completions.create(
        model=model,
        max_completion_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": [
                    {
                        "type": "file",
                        "file": {
                            "filename": pathlib.Path(pdf_path).name,
                            "file_data": pdf_to_data_url(pdf_path),
                        },
                    },
                    {"type": "text", "text": question},
                ],
            },
        ],
    )
    return completion.choices[0].message.content


def ask_pdf_stream(
    pdf_path: str,
    question: str,
    system: str = _DEFAULT_SYSTEM,
    model: str = _DEFAULT_MODEL,
    max_tokens: int = 1024,
):
    """
    Stream a PDF Q&A response. Yields text delta strings as they arrive.

    Use when the document is long or you want the user to see output progressively.

    Example:
        for chunk in ask_pdf_stream("report.pdf", "Summarise the key findings."):
            print(chunk, end="", flush=True)
        print()

    Args: same as ask_pdf().
    Yields: str — text delta chunks from the model.
    """
    stream = _client().chat.completions.create(
        model=model,
        max_completion_tokens=max_tokens,
        stream=True,
        messages=[
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": [
                    {
                        "type": "file",
                        "file": {
                            "filename": pathlib.Path(pdf_path).name,
                            "file_data": pdf_to_data_url(pdf_path),
                        },
                    },
                    {"type": "text", "text": question},
                ],
            },
        ],
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
