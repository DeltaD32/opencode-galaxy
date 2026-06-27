"""Agent runtime: the OpenAI function-calling tool-use loop.

run_task(spec, llm_complete) runs ONE agent task to completion and returns a
TaskResult. The control plane calls this; the runtime is pluggable (this is the
'api' runtime). No streaming inside the loop (gateway constraint).
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Callable
from . import tools as toolmod


@dataclass
class TaskSpec:
    task_id: str
    agent: str
    system_prompt: str
    user_prompt: str
    repo_root: str
    file_scope: list[str] = field(default_factory=list)
    allowed_tools: list[str] | None = None
    model: str | None = None
    max_steps: int = 10


@dataclass
class TaskResult:
    task_id: str
    status: str            # done | failed
    final_text: str
    steps: int
    error: str | None = None
    transcript: list = field(default_factory=list)


def run_task(spec: TaskSpec, llm_complete: Callable) -> TaskResult:
    ctx = toolmod.ToolContext(repo_root=spec.repo_root, file_scope=spec.file_scope)
    tools = toolmod.schemas(spec.allowed_tools)
    messages = [
        {"role": "system", "content": spec.system_prompt},   # ONE system prompt (gateway constraint)
        {"role": "user", "content": spec.user_prompt},
    ]
    transcript = []
    try:
        for step in range(spec.max_steps):
            msg = llm_complete(messages, tools=tools, model=spec.model)
            # Normalise the assistant message back into the messages array
            assistant_entry = {"role": "assistant", "content": msg.content or ""}
            tool_calls = getattr(msg, "tool_calls", None)
            if tool_calls:
                assistant_entry["tool_calls"] = [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in tool_calls
                ]
            messages.append(assistant_entry)

            if not tool_calls:
                return TaskResult(spec.task_id, "done", msg.content or "", step + 1,
                                  transcript=transcript)

            # Execute ALL tool calls in this step (parallel tool calls allowed), then continue.
            for tc in tool_calls:
                name = tc.function.name
                args = json.loads(tc.function.arguments or "{}")
                result = toolmod.dispatch(name, args, ctx)
                transcript.append({"tool": name, "args": args, "result": result[:500]})
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

        return TaskResult(spec.task_id, "failed", "", spec.max_steps,
                          error="max_steps exhausted", transcript=transcript)
    except Exception as e:  # noqa: BLE001
        return TaskResult(spec.task_id, "failed", "", 0, error=f"{type(e).__name__}: {e}",
                          transcript=transcript)
