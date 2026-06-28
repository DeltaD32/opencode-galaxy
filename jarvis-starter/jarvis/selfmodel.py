"""Self-model (Module F.1).

An always-current, machine-readable picture of the system, generated from the
LIVE registries — never hand-maintained, so it can't go stale. The Architect
(Module F) reads this to understand its own architecture before changing it, and
the introspection functions are the tools it calls. The INVARIANTS are the
immutable floor (F.4): enforced in code, not editable by the system.
"""
from __future__ import annotations
import json, re, pathlib
from . import agents as agentreg
from . import tools as toolmod

_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA_DIR = _ROOT / "schema"
MANIFEST_PATH = _ROOT / "manifest.json"

# The five planes (build-guide §1).
PLANES = ["llm", "state", "control", "memory", "interface"]

# The immutable floor (Module F.4) — enforced in code; the system may not relax these.
INVARIANTS = [
    "may NOT widen its own egress allowlist",
    "may NOT remove or weaken the sandbox / file-scope enforcement",
    "may NOT disable the verification / eval gate or the auto-rollback",
    "may NOT grant an agent broader file-scope than policy allows",
    "gate-locked change classes cannot be promoted to 'auto' by the system",
]


def _table_names(sql_text: str) -> list[str]:
    return re.findall(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\"']?(\w+)", sql_text, re.IGNORECASE)


def build_manifest(write: bool = False) -> dict:
    """Regenerate the manifest from the live agent registry, tool registry, and DDL."""
    agents = {}
    for name in agentreg.available():
        a = agentreg.get(name)
        agents[name] = {"tools": a.get("tools", []), "model": a.get("model")}  # prompt omitted (large)
    tools = [s["function"]["name"] for s in toolmod.schemas()]
    schemas = {sql.name: _table_names(sql.read_text()) for sql in sorted(SCHEMA_DIR.glob("*.sql"))}
    manifest = {
        "planes": PLANES,
        "agents": agents,
        "tools": tools,
        "schemas": schemas,
        "invariants": INVARIANTS,
    }
    if write:
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


# ── Introspection tools the Architect can call ──────────────────────────────
def describe_architecture() -> dict:
    return build_manifest()


def describe_agent(name: str) -> dict:
    a = agentreg.get(name)
    return {"name": name, "tools": a.get("tools", []), "model": a.get("model"),
            "prompt": a.get("prompt", "")}


def describe_skill(name: str) -> dict:
    for s in toolmod.schemas():
        if s["function"]["name"] == name:
            return s["function"]
    return {"name": name, "status": "not-found"}


def list_invariants() -> list[str]:
    return list(INVARIANTS)


def main(argv=None):
    manifest = build_manifest(write=True)
    print(f"wrote {MANIFEST_PATH}")
    print(f"  planes={len(manifest['planes'])} agents={len(manifest['agents'])} "
          f"tools={len(manifest['tools'])} schemas={list(manifest['schemas'])} "
          f"invariants={len(manifest['invariants'])}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
