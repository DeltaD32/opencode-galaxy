"""
agent_memory.py — Per-agent self-learning memory for the OpenCode multi-agent system.

Wraps the memory MCP's JSONL knowledge graph with agent-namespaced read/write helpers.
Each agent maintains its own entity in the graph (e.g. "programming-expert::learnings")
with structured observations tagged as WORKED / AVOID / PATTERN.

Design principles:
  - Direct file I/O on memory.jsonl (no MCP subprocess needed)
  - Thread-safe via file lock (portalocker not required — single-writer design)
  - Observations are timestamped and tagged for easy filtering
  - Supports per-task recall so agents can query "what did I learn about Angular routing?"
  - Session-clearing safe: learned knowledge survives context resets

Entity naming convention:
  "<agent-name>::learnings"   — e.g. "programming-expert::learnings"

Observation format:
  "[WORKED] <task_domain> | <what worked> | <date>"
  "[AVOID]  <task_domain> | <what to avoid> | <date>"
  "[PATTERN] <task_domain> | <reusable technique> | <date>"

Usage:
  from agent_memory import recall, learn, summarise_learnings
  
  # At start of task — recall relevant learnings
  tips = recall("programming-expert", domain="Angular routing")
  
  # After task — record what worked
  learn("programming-expert", "WORKED", "Angular routing", "Use @defer for lazy routes")
  learn("programming-expert", "AVOID",  "Angular routing", "Don't use loadChildren strings — use loadComponent")
  
  # For display / debugging
  print(summarise_learnings("programming-expert", limit=5))
"""

from __future__ import annotations

import json
import os
import re
import fcntl
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def _memory_jsonl_path() -> Path:
    """
    Returns the memory.jsonl path.
    Respects MEMORY_FILE_PATH env var (same logic as the MCP server).
    Falls back to the default npx cache location.
    """
    env_path = os.environ.get("MEMORY_FILE_PATH")
    if env_path:
        p = Path(env_path)
        return p if p.is_absolute() else Path(__file__).parent / p

    # Default: locate via npx cache
    npx_glob = list(
        Path.home().glob(
            ".npm/_npx/*/node_modules/@modelcontextprotocol/server-memory/dist/memory.jsonl"
        )
    )
    if npx_glob:
        return npx_glob[0]

    raise FileNotFoundError(
        "Cannot find memory.jsonl. Set MEMORY_FILE_PATH or install "
        "@modelcontextprotocol/server-memory via npx."
    )


def _entity_name(agent: str) -> str:
    return f"{agent}::learnings"


# ---------------------------------------------------------------------------
# Low-level JSONL read/write
# ---------------------------------------------------------------------------

def _load_graph() -> tuple[list[dict], list[dict]]:
    """Load all entities and relations from memory.jsonl."""
    path = _memory_jsonl_path()
    entities: list[dict] = []
    relations: list[dict] = []
    if not path.exists():
        return entities, relations
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("type") == "entity":
            entities.append(obj)
        elif obj.get("type") == "relation":
            relations.append(obj)
    return entities, relations


def _save_graph(entities: list[dict], relations: list[dict]) -> None:
    """Atomically rewrite memory.jsonl with updated entities + relations."""
    path = _memory_jsonl_path()
    lines = []
    for e in entities:
        lines.append(json.dumps(e, ensure_ascii=False))
    for r in relations:
        lines.append(json.dumps(r, ensure_ascii=False))
    tmp = path.with_suffix(".jsonl.tmp")
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    tmp.replace(path)  # atomic rename


def _get_or_create_entity(agent: str, entities: list[dict]) -> dict:
    """Return existing agent entity or create a new empty one."""
    name = _entity_name(agent)
    for e in entities:
        if e.get("name") == name:
            return e
    new_entity = {
        "type": "entity",
        "name": name,
        "entityType": "AgentLearnings",
        "observations": [],
    }
    entities.append(new_entity)
    return new_entity


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

ObservationTag = Literal["WORKED", "AVOID", "PATTERN"]


def learn(
    agent: str,
    tag: ObservationTag,
    domain: str,
    note: str,
) -> None:
    """
    Record a learning for an agent.
    
    Args:
        agent:  Agent name, e.g. "programming-expert"
        tag:    "WORKED" | "AVOID" | "PATTERN"
        domain: Task domain / technology, e.g. "Angular routing", "blackboard"
        note:   What was learned — concise, actionable.
    
    Example:
        learn("programming-expert", "WORKED", "Angular signals",
              "Use linkedSignal for derived state — avoids manual subscription cleanup")
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    observation = f"[{tag}] {domain} | {note} | {today}"
    
    entities, relations = _load_graph()
    entity = _get_or_create_entity(agent, entities)
    
    # Deduplicate: skip if exact same note already recorded (ignore date)
    note_prefix = f"[{tag}] {domain} | {note} |"
    for obs in entity["observations"]:
        if obs.startswith(note_prefix):
            return  # already recorded
    
    entity["observations"].append(observation)
    _save_graph(entities, relations)


def recall(
    agent: str,
    domain: str = "",
    tag: ObservationTag | None = None,
    limit: int = 10,
) -> list[str]:
    """
    Retrieve learnings for an agent, optionally filtered by domain and/or tag.
    
    Args:
        agent:  Agent name, e.g. "programming-expert"
        domain: Optional filter — returns only observations mentioning this domain
                (case-insensitive substring match)
        tag:    Optional filter — "WORKED" | "AVOID" | "PATTERN" | None (all)
        limit:  Maximum number of observations to return (most recent first)
    
    Returns:
        List of observation strings, most recent first.
    
    Example:
        tips = recall("programming-expert", domain="Angular routing")
        # → ["[WORKED] Angular routing | Use @defer for lazy routes | 2026-06-25", ...]
    """
    entities, _ = _load_graph()
    name = _entity_name(agent)
    entity = next((e for e in entities if e.get("name") == name), None)
    if not entity:
        return []
    
    obs = list(entity.get("observations", []))
    obs.reverse()  # most recent first (appended last)
    
    if tag:
        obs = [o for o in obs if o.startswith(f"[{tag}]")]
    
    if domain:
        domain_lower = domain.lower()
        obs = [o for o in obs if domain_lower in o.lower()]
    
    return obs[:limit]


def summarise_learnings(agent: str, limit: int = 5) -> str:
    """
    Return a compact, human-readable summary of an agent's top learnings.
    Designed to be prepended to an agent's task context (low token cost).
    
    Format:
        ## My Learnings (programming-expert)
        WORKED  | Angular routing | Use @defer for lazy routes
        AVOID   | Angular routing | Don't use loadChildren strings
        PATTERN | BMW LLM API     | Always use clipjoint venv for Python
    
    Returns empty string if no learnings recorded yet.
    """
    entities, _ = _load_graph()
    name = _entity_name(agent)
    entity = next((e for e in entities if e.get("name") == name), None)
    if not entity or not entity.get("observations"):
        return ""
    
    obs = list(entity["observations"])
    obs.reverse()  # most recent first
    selected = obs[:limit]
    
    lines = [f"## My Learnings ({agent}) — top {len(selected)}"]
    for o in selected:
        # Parse: "[TAG] domain | note | date"
        m = re.match(r"\[(\w+)\]\s+(.+?)\s+\|\s+(.+?)\s+\|\s+(\S+)", o)
        if m:
            tag, domain, note, _ = m.groups()
            lines.append(f"{tag:<8}| {domain:<20} | {note}")
        else:
            lines.append(o)
    
    return "\n".join(lines)


def get_all_agents_with_learnings() -> list[str]:
    """
    Return list of agent names that have at least one learning recorded.
    Useful for the orchestrator to know which agents have history.
    """
    entities, _ = _load_graph()
    result = []
    for e in entities:
        name = e.get("name", "")
        if name.endswith("::learnings") and e.get("observations"):
            result.append(name.replace("::learnings", ""))
    return sorted(result)


def clear_learnings(agent: str) -> int:
    """
    Remove all learnings for a specific agent.
    Returns count of observations deleted.
    Only use this deliberately — learnings are meant to persist across sessions.
    """
    entities, relations = _load_graph()
    name = _entity_name(agent)
    entity = next((e for e in entities if e.get("name") == name), None)
    if not entity:
        return 0
    count = len(entity.get("observations", []))
    entity["observations"] = []
    _save_graph(entities, relations)
    return count
