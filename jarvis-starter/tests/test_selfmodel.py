"""Self-model tests (Module F.1) — manifest reflects the live registries + invariants."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from jarvis import selfmodel
from jarvis import agents as agentreg


def test_manifest_reflects_registries():
    m = selfmodel.build_manifest()
    # built-in agents are present (registry is the source of truth)
    for a in ("programming-expert", "design-expert", "data-analyst"):
        assert a in m["agents"], m["agents"].keys()
    assert set(m["agents"]) >= set(agentreg.available())

    # tools come from the live tool registry
    assert {"read_file", "write_file", "bash"} <= set(m["tools"]), m["tools"]

    # DB schema tables are extracted from the DDL
    assert "tasks" in m["schemas"]["state.sql"], m["schemas"]
    assert "entities" in m["schemas"]["memory.sql"], m["schemas"]

    # five planes
    assert len(m["planes"]) == 5
    print("  ✓ manifest reflects agents, tools, and schema DDL from the live registries")


def test_invariants_floor_present():
    inv = " ".join(selfmodel.list_invariants()).lower()
    assert "egress" in inv and "sandbox" in inv and ("eval" in inv or "verification" in inv)
    assert len(selfmodel.list_invariants()) >= 4
    print("  ✓ immutable-floor invariants present (egress / sandbox / eval gate)")


def test_describe_agent():
    d = selfmodel.describe_agent("programming-expert")
    assert "bash" in d["tools"] and d["prompt"]
    print("  ✓ describe_agent returns a known built-in agent")


if __name__ == "__main__":
    test_manifest_reflects_registries()
    test_invariants_floor_present()
    test_describe_agent()
    print("\nSELF-MODEL (Module F.1) TESTS PASSED ✅")
