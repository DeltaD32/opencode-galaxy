"""MemoryStore: durable, self-binding semantic memory.

Two layers (CO-004):
  - knowledge graph: project-bound entities + observations + relations + vectors
  - agent learnings: a per-agent '<agent>::learnings' entity with WORKED/AVOID/PATTERN obs

Placement is deterministic: callers pass `project` (from the handoff), the store resolves
the canonical entity via the alias table — agents never choose where things go.
"""
from __future__ import annotations
import os, re, sqlite3, datetime, pathlib, json, math
import sqlite_vec
from . import embeddings

SCHEMA = pathlib.Path(__file__).resolve().parent.parent.parent / "schema" / "memory.sql"
DEFAULT_PATH = str(pathlib.Path.home() / ".jarvis" / "memory.db")


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def _new_id(p=""):
    import uuid; return f"{p}{uuid.uuid4().hex[:12]}"

def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()

def _decay(observed_at: str, half_life_days: float) -> float:
    try:
        age = (datetime.datetime.now(datetime.timezone.utc)
               - datetime.datetime.fromisoformat(observed_at)).total_seconds() / 86400.0
    except Exception:
        return 1.0
    return 0.5 ** (age / max(half_life_days, 0.001))


class MemoryStore:
    def __init__(self, conn: sqlite3.Connection, engine):
        self.conn = conn
        self.engine = engine

    # ---- lifecycle --------------------------------------------------------
    @classmethod
    def open(cls, path: str | None = None, engine=None):
        p = path or os.environ.get("JARVIS_MEMORY_PATH", DEFAULT_PATH)
        pathlib.Path(p).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(p)
        conn.row_factory = sqlite3.Row
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        store = cls(conn, engine or embeddings.from_env())
        try:
            store.init()
        except Exception:
            conn.close()  # don't leak the handle when init refuses (e.g. dim mismatch)
            raise
        return store

    def init(self):
        self.conn.executescript(SCHEMA.read_text())
        # vector table dim must match the engine; record + enforce.
        row = self.conn.execute("SELECT value FROM meta WHERE key='embed_dim'").fetchone()
        if row is None:
            self.conn.execute(
                f"CREATE VIRTUAL TABLE IF NOT EXISTS entity_vectors USING vec0("
                f"entity_id TEXT PRIMARY KEY, embedding float[{self.engine.dim}])")
            self.conn.execute("INSERT OR REPLACE INTO meta VALUES ('embed_dim', ?)", (str(self.engine.dim),))
            self.conn.execute("INSERT OR REPLACE INTO meta VALUES ('embed_engine', ?)", (self.engine.name,))
            self.conn.commit()
        elif int(row["value"]) != self.engine.dim:
            raise RuntimeError(
                f"embedding dim mismatch: db={row['value']} engine={self.engine.dim} "
                f"({self.engine.name}). Re-embed required — don't mix engines.")

    def close(self):
        """Close the underlying SQLite connection. On Windows an open handle
        blocks unlinking the DB file (e.g. temp-dir cleanup in tests)."""
        self.conn.close()

    # ---- internals --------------------------------------------------------
    def _resolve(self, name: str) -> str | None:
        r = self.conn.execute("SELECT entity_id FROM entity_aliases WHERE alias=?", (_norm(name),)).fetchone()
        return r["entity_id"] if r else None

    def _upsert_entity(self, name, entity_type, project=None, half_life_days=30.0, blackboard_id=None) -> str:
        eid = self._resolve(name)
        if eid:
            self.conn.execute("UPDATE entities SET updated_at=?, last_reinforced_at=?, decay_score=1.0 WHERE id=?",
                              (_now(), _now(), eid))
            self.conn.commit()
            return eid
        eid = _new_id("ent_")
        self.conn.execute(
            "INSERT INTO entities (id,name,entity_type,project,half_life_days,blackboard_id,created_at,updated_at,last_reinforced_at)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
            (eid, name, entity_type, project, half_life_days, blackboard_id, _now(), _now(), _now()))
        self.conn.execute("INSERT OR IGNORE INTO entity_aliases (alias, entity_id) VALUES (?,?)", (_norm(name), eid))
        self.conn.commit()
        self._embed(eid, name)
        return eid

    def add_alias(self, name: str, alias: str):
        eid = self._resolve(name)
        if eid:
            self.conn.execute("INSERT OR IGNORE INTO entity_aliases (alias, entity_id) VALUES (?,?)", (_norm(alias), eid))
            self.conn.commit()

    def _embed(self, entity_id: str, text: str):
        vec = self.engine.embed([text])[0]
        # vec0 virtual tables don't support INSERT OR REPLACE — delete then insert.
        self.conn.execute("DELETE FROM entity_vectors WHERE entity_id=?", (entity_id,))
        self.conn.execute("INSERT INTO entity_vectors (entity_id, embedding) VALUES (?,?)",
                          (entity_id, sqlite_vec.serialize_float32(vec)))
        self.conn.commit()

    def _reembed(self, entity_id: str):
        """Re-embed an entity from its name + recent observations (the searchable content)."""
        e = self.conn.execute("SELECT name FROM entities WHERE id=?", (entity_id,)).fetchone()
        if not e:
            return
        obs = [o["body"] for o in self.conn.execute(
            "SELECT body FROM observations WHERE entity_id=? ORDER BY observed_at DESC LIMIT 8",
            (entity_id,)).fetchall()]
        self._embed(entity_id, (e["name"] + " " + " ".join(obs)).strip())

    def _add_obs(self, entity_id, body, tag="", domain="", singleton_key=None):
        if singleton_key:  # replace prior same-key obs
            self.conn.execute("DELETE FROM observations WHERE entity_id=? AND singleton_key=?",
                              (entity_id, singleton_key))
        try:
            self.conn.execute(
                "INSERT INTO observations (id,entity_id,tag,domain,body,singleton_key,observed_at)"
                " VALUES (?,?,?,?,?,?,?)",
                (_new_id("obs_"), entity_id, tag, domain, body, singleton_key, _now()))
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass  # dedup: identical (tag,domain,body) already present

    # ---- public API: project resolution ----------------------------------
    def resolve_project_entity(self, project: str, blackboard_id=None) -> str:
        return self._upsert_entity(project, "Project", project=project, blackboard_id=blackboard_id)

    # ---- public API: WRITE ------------------------------------------------
    def remember(self, *, project, entity_name=None, entity_type="TechnicalFact",
                 observations=None, relations=None, blackboard_id=None):
        """Write knowledge bound to a project. observations: list of dicts
        {body, tag?, domain?, singleton_key?}. relations: list of (other_name, rel_type)."""
        proj_id = self.resolve_project_entity(project, blackboard_id)
        target_name = entity_name or project
        eid = (proj_id if target_name == project
               else self._upsert_entity(target_name, entity_type, project=project, blackboard_id=blackboard_id))
        for o in (observations or []):
            self._add_obs(eid, o["body"], o.get("tag", ""), o.get("domain", ""), o.get("singleton_key"))
        if observations:
            self._reembed(eid)   # make the observation content semantically searchable
        # ensure ≥1 relation to the project (anti-pattern guard)
        rels = list(relations or [])
        if eid != proj_id and not rels:
            rels.append((project, "part-of"))
        for other_name, rel_type in rels:
            oid = self._upsert_entity(other_name, "Project" if other_name == project else "Entity",
                                      project=project)
            self.conn.execute(
                "INSERT OR IGNORE INTO relations (id,from_id,to_id,rel_type,created_at) VALUES (?,?,?,?,?)",
                (_new_id("rel_"), eid, oid, rel_type, _now()))
        self.conn.commit()
        return eid

    def learn(self, agent: str, tag: str, domain: str, note: str):
        """Per-agent learning (WORKED/AVOID/PATTERN). Decays; PATTERN lives 2× longer."""
        name = f"{agent}::learnings"
        half = 60.0 if tag == "PATTERN" else 30.0
        eid = self._upsert_entity(name, "AgentLearnings", project=None, half_life_days=half)
        self._add_obs(eid, note, tag=tag, domain=domain)
        return eid

    # ---- public API: READ -------------------------------------------------
    def recall(self, *, project=None, query="", agent=None, k=5) -> dict:
        out = {"project_context": [], "agent_learnings": [], "semantic": []}
        # 1) project context pack: the project entity + 1-hop related entities
        if project:
            pid = self._resolve(project)
            if pid:
                out["project_context"] = self._entity_brief(pid)
                for r in self.conn.execute(
                        "SELECT to_id FROM relations WHERE from_id=? UNION SELECT from_id FROM relations WHERE to_id=?",
                        (pid, pid)).fetchall():
                    out["project_context"].extend(self._entity_brief(r["to_id"]))
        # 2) agent learnings, decay-ranked
        if agent:
            lid = self._resolve(f"{agent}::learnings")
            if lid:
                hl = self.conn.execute("SELECT half_life_days FROM entities WHERE id=?", (lid,)).fetchone()["half_life_days"]
                rows = self.conn.execute(
                    "SELECT tag,domain,body,observed_at FROM observations WHERE entity_id=?", (lid,)).fetchall()
                ranked = sorted(rows, key=lambda o: _decay(o["observed_at"], hl), reverse=True)
                out["agent_learnings"] = [f"[{o['tag']}] {o['domain']}: {o['body']}" for o in ranked[:k]]
        # 3) semantic KNN over all entities
        if query:
            qv = sqlite_vec.serialize_float32(self.engine.embed([query])[0])
            hits = self.conn.execute(
                "SELECT entity_id, distance FROM entity_vectors WHERE embedding MATCH ? ORDER BY distance LIMIT ?",
                (qv, k)).fetchall()
            for h in hits:
                e = self.conn.execute("SELECT name, entity_type FROM entities WHERE id=?", (h["entity_id"],)).fetchone()
                if e:
                    out["semantic"].append({"name": e["name"], "type": e["entity_type"],
                                            "distance": round(h["distance"], 4)})
        return out

    def _entity_brief(self, eid: str) -> list[dict]:
        e = self.conn.execute("SELECT name, entity_type FROM entities WHERE id=?", (eid,)).fetchone()
        if not e:
            return []
        obs = [o["body"] for o in self.conn.execute(
            "SELECT body FROM observations WHERE entity_id=? ORDER BY observed_at DESC LIMIT 5", (eid,)).fetchall()]
        return [{"name": e["name"], "type": e["entity_type"], "observations": obs}]

    def recall_text(self, **kw) -> str:
        """recall() formatted as a context block to inject into an agent prompt."""
        r = self.recall(**kw)
        lines = []
        if r["agent_learnings"]:
            lines.append("What you've learned before:")
            lines += [f"  - {x}" for x in r["agent_learnings"]]
        if r["project_context"]:
            lines.append("Project context:")
            for c in r["project_context"][:5]:
                lines.append(f"  - {c['name']} ({c['type']})" +
                             (f": {c['observations'][0]}" if c.get("observations") else ""))
        if r["semantic"]:
            lines.append("Related knowledge: " + ", ".join(h["name"] for h in r["semantic"]))
        return "\n".join(lines)
