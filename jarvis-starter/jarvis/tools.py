"""Tool framework: registry + sandboxed tools restricted to a task's file_scope.

Every tool is OpenAI function-calling shaped:
  {"type":"function","function":{"name","description","parameters":<jsonschema>}}
Handlers receive (args: dict, ctx: ToolContext) and return a string.
"""
from __future__ import annotations
import json, os, pathlib, subprocess
from dataclasses import dataclass, field


@dataclass
class ToolContext:
    """Capabilities a tool is allowed to use for THIS task."""
    repo_root: str
    file_scope: list[str] = field(default_factory=list)  # absolute paths allowed

    def _check(self, path: str) -> pathlib.Path:
        p = pathlib.Path(path)
        if not p.is_absolute():
            p = pathlib.Path(self.repo_root) / p
        p = p.resolve()
        # Cross-platform containment: compare path components, not string
        # prefixes. A `str(p).startswith(root + "/")` check is POSIX-only and
        # rejects valid in-scope paths on Windows (back-slash separators).
        allowed = any(p == s or p.is_relative_to(s)
                      for s in (pathlib.Path(s).resolve() for s in self.file_scope))
        if not allowed:
            raise PermissionError(f"path {p} is outside this task's file_scope")
        return p


_REGISTRY: dict[str, dict] = {}


def tool(name, description, parameters):
    """Decorator registering a tool handler."""
    def wrap(fn):
        _REGISTRY[name] = {
            "schema": {"type": "function", "function": {
                "name": name, "description": description, "parameters": parameters}},
            "handler": fn,
        }
        return fn
    return wrap


def schemas(allow: list[str] | None = None) -> list[dict]:
    return [t["schema"] for n, t in _REGISTRY.items() if allow is None or n in allow]


def dispatch(name: str, args: dict, ctx: ToolContext) -> str:
    if name not in _REGISTRY:
        return f"ERROR: unknown tool {name}"
    try:
        return _REGISTRY[name]["handler"](args, ctx)
    except Exception as e:  # tool errors are returned to the model, not raised
        return f"ERROR: {type(e).__name__}: {e}"


# ---- built-in tools -------------------------------------------------------

@tool("read_file", "Read a UTF-8 text file within the task's file scope.",
      {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]})
def _read_file(args, ctx: ToolContext):
    p = ctx._check(args["path"])
    return p.read_text()


@tool("write_file", "Write (create/overwrite) a text file within the task's file scope.",
      {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
       "required": ["path", "content"]})
def _write_file(args, ctx: ToolContext):
    p = ctx._check(args["path"])
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(args["content"])
    return f"wrote {len(args['content'])} bytes to {p}"


@tool("bash", "Run a shell command inside the repo root. No network. 30s timeout.",
      {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]})
def _bash(args, ctx: ToolContext):
    # In production: run inside a container/sandbox with no network + scoped mount.
    out = subprocess.run(args["command"], shell=True, cwd=ctx.repo_root,
                         capture_output=True, text=True, timeout=30)
    return (out.stdout + out.stderr)[:8000]
