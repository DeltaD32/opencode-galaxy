"""Importer: v1 `memory.jsonl` → the sqlite-vec memory store (CO-004 M4.1).

JSONL line shapes (from the v1 agent-memory skill):
  {"type":"entity","name":..,"entityType":..,"observations":[str,..]}
  {"type":"relation","from":..,"to":..,"relationType":..}
AgentLearnings observations look like  "[TAG] domain | note | YYYY-MM-DD".

Deterministic placement + canonical dedup-merge: known duplicate project names
collapse to ONE canonical entity (the others kept as aliases); observations and
relations union onto the canonical; dangling relations are logged, not dropped.
Every entity is embedded by the store on upsert, so the vector index is rebuilt
in-DB (no hnswlib drift).
"""
from __future__ import annotations
import json, re, sqlite3, pathlib, argparse
from .store import MemoryStore, _norm, _now, _new_id

# Known v1 duplicates → canonical (CO-004 M4.1). Override via import_jsonl(canonical_merges=...).
DEFAULT_MERGES = {
    "JARVIS Project": "JARVIS Galaxy",
    "JARVIS Frontend Project": "JARVIS Galaxy",
    "JARVIS Web Frontend": "JARVIS Galaxy",
}

_TAG_RE = re.compile(r"^\[(?P<tag>[^\]]+)\]\s*(?P<body>.*)$")
_DATE_TAIL = re.compile(r"\s*(\d{4}-\d{2}-\d{2})\s*$")
_DATE_ONLY = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_learning_obs(s: str):
    """'[TAG] domain | note | YYYY-MM-DD' → (tag, domain, note, date|None)."""
    s = s.strip()
    tag = "NOTE"
    m = _TAG_RE.match(s)
    rest = s
    if m:
        tag = m.group("tag").strip()
        rest = m.group("body")
    parts = [p.strip() for p in rest.split("|")]
    domain = parts[0] if parts else ""
    date = None
    if len(parts) >= 2 and _DATE_ONLY.match(parts[-1]):
        date = parts[-1]
        note = " | ".join(parts[1:-1])
    else:
        note = " | ".join(parts[1:]) if len(parts) > 1 else ""
    return tag, domain, note, date


def infer_project(name: str):
    """Project a non-learnings entity belongs to (CO-004 mapping), or None."""
    n = name.strip()
    if n.lower().startswith("jarvis"):
        return "jarvis-galaxy"
    if n.endswith(" Project"):
        return _norm(n[: -len(" Project")]) or None
    return None


def _parse_general_obs(s: str):
    """A non-learnings observation → (body, tag, singleton_key, observed_at)."""
    body = s.strip()
    tag = ""
    observed_at = None
    m = _TAG_RE.match(body)
    if m:
        tag = m.group("tag").strip()
        body = m.group("body").strip()
    d = _DATE_TAIL.search(body)
    if d:
        observed_at = d.group(1)
        body = body[: d.start()].strip()
    singleton = "status" if body.lower().startswith("status:") else None
    return body, tag, singleton, observed_at


def _insert_obs(store, eid, body, tag="", domain="", singleton_key=None, observed_at=None):
    """Insert one observation preserving its original date; mirrors store dedup."""
    if singleton_key:
        store.conn.execute("DELETE FROM observations WHERE entity_id=? AND singleton_key=?",
                           (eid, singleton_key))
    try:
        store.conn.execute(
            "INSERT INTO observations (id,entity_id,tag,domain,body,singleton_key,observed_at)"
            " VALUES (?,?,?,?,?,?,?)",
            (_new_id("obs_"), eid, tag, domain, body, singleton_key, observed_at or _now()))
    except sqlite3.IntegrityError:
        pass  # identical (tag,domain,body) already present → dedup


def import_jsonl(store: MemoryStore, path, *, canonical_merges=None) -> dict:
    """Import a memory.jsonl into `store`. Returns import statistics."""
    merges = dict(DEFAULT_MERGES if canonical_merges is None else canonical_merges)
    stats = {"entities": 0, "observations": 0, "relations": 0,
             "merged": 0, "learnings": 0, "dangling": []}
    text = pathlib.Path(path).read_text(encoding="utf-8")
    relations = []
    for line in (l for l in text.splitlines() if l.strip()):
        rec = json.loads(line)
        kind = rec.get("type")
        if kind == "relation":
            relations.append(rec)
            continue
        if kind != "entity":
            continue
        name = rec["name"]
        etype = rec.get("entityType", "Entity")
        obs = rec.get("observations", []) or []
        if name.endswith("::learnings"):
            agent = name[: -len("::learnings")]
            for o in obs:
                tag, domain, note, _date = parse_learning_obs(o)
                store.learn(agent, tag, domain, note)
                stats["learnings"] += 1
            stats["entities"] += 1
            continue
        canonical = merges.get(name, name)
        if canonical != name:
            stats["merged"] += 1
        eid = store._upsert_entity(canonical, etype, project=infer_project(canonical))
        if canonical != name:
            store.add_alias(canonical, name)  # variant resolves to the canonical
        for o in obs:
            body, tag, singleton, observed_at = _parse_general_obs(o)
            _insert_obs(store, eid, body, tag=tag, singleton_key=singleton, observed_at=observed_at)
            stats["observations"] += 1
        store._reembed(eid)  # make observation content semantically searchable
        stats["entities"] += 1
    store.conn.commit()

    for rec in relations:
        fid = store._resolve(rec.get("from", ""))
        tid = store._resolve(rec.get("to", ""))
        if not fid or not tid:
            stats["dangling"].append((rec.get("from"), rec.get("to"), rec.get("relationType")))
            continue
        store.conn.execute(
            "INSERT OR IGNORE INTO relations (id,from_id,to_id,rel_type,created_at) VALUES (?,?,?,?,?)",
            (_new_id("rel_"), fid, tid, rec.get("relationType", "related"), _now()))
        stats["relations"] += 1
    store.conn.commit()
    return stats


def verify(store: MemoryStore) -> dict:
    """Reconciliation report: counts, orphan relations, duplicate names, vector coverage."""
    c = store.conn
    n_ent = c.execute("SELECT COUNT(*) n FROM entities").fetchone()["n"]
    n_obs = c.execute("SELECT COUNT(*) n FROM observations").fetchone()["n"]
    n_rel = c.execute("SELECT COUNT(*) n FROM relations").fetchone()["n"]
    orphans = c.execute(
        "SELECT COUNT(*) n FROM relations WHERE from_id NOT IN (SELECT id FROM entities)"
        " OR to_id NOT IN (SELECT id FROM entities)").fetchone()["n"]
    dups = [r["name"] for r in c.execute(
        "SELECT name, COUNT(*) c FROM entities GROUP BY name HAVING c > 1").fetchall()]
    n_vec = c.execute("SELECT COUNT(*) n FROM entity_vectors").fetchone()["n"]
    return {
        "entities": n_ent, "observations": n_obs, "relations": n_rel,
        "orphan_relations": orphans, "duplicate_names": dups,
        "vector_coverage": n_vec, "vectors_complete": n_vec >= n_ent,
        "ok": orphans == 0 and not dups and n_vec >= n_ent,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Import v1 memory.jsonl into the sqlite memory store.")
    ap.add_argument("jsonl", help="path to memory.jsonl")
    ap.add_argument("--db", default=None, help="memory.db path (default: $JARVIS_MEMORY_PATH or ~/.jarvis)")
    args = ap.parse_args(argv)
    store = MemoryStore.open(args.db)
    try:
        stats = import_jsonl(store, args.jsonl)
        report = verify(store)
    finally:
        store.close()
    print("import:", json.dumps(stats, indent=2))
    print("verify:", json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
