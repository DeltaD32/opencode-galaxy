"""Eval harness (Module D / build-guide Phase 7).

A regression suite of representative requests with expected routing/plan shapes.
Any agent-prompt or routing change must pass evals before it's accepted — this is
what makes self-modification safe rather than drift-prone. `run_evals` decomposes
each request and checks the resulting plan against the case's expectations, then
enforces a configurable minimum pass rate (default 1.0).

Run offline with the bundled deterministic planner (`python -m jarvis.evals`), or
pass a live `llm_complete` to evaluate the real planner.
"""
from __future__ import annotations
import json, types, pathlib
from . import decomposer, agents as agentreg

CASES_PATH = pathlib.Path(__file__).resolve().parent.parent / "evals" / "cases.json"


def load_cases(path=None) -> list[dict]:
    return json.loads(pathlib.Path(path or CASES_PATH).read_text(encoding="utf-8"))


def make_mock_planner(cases):
    """A deterministic planner that returns each case's bundled plan — lets the
    harness run offline. Real evaluation passes the live planner instead."""
    by_request = {c["request"]: c["plan"] for c in cases}

    def planner(messages, tools=None, model=None):
        user = messages[-1]["content"]
        for request, plan in by_request.items():
            if request in user:
                return types.SimpleNamespace(content=json.dumps(plan), tool_calls=None)
        return types.SimpleNamespace(
            content=json.dumps({"project_name": "x", "task_description": "x", "tasks": []}),
            tool_calls=None)

    return planner


def check_plan(plan, expect: dict):
    """Return (ok, reasons) for a decomposed plan against a case's expectations."""
    reasons = []
    if "n_tasks" in expect and len(plan.tasks) != expect["n_tasks"]:
        reasons.append(f"n_tasks {len(plan.tasks)} != {expect['n_tasks']}")
    if "agents" in expect:
        got = {t.agent for t in plan.tasks}
        for a in expect["agents"]:
            if a not in got:
                reasons.append(f"missing agent '{a}'")
    if expect.get("has_dependency") and not any(t.depends_on for t in plan.tasks):
        reasons.append("expected at least one dependency")
    return (not reasons), reasons


def run_evals(llm_complete, cases=None, *, repo_root=".", agents=None, min_pass_rate: float = 1.0) -> dict:
    cases = load_cases() if cases is None else cases
    agents = agentreg.available() if agents is None else agents
    details, passed = [], 0
    for c in cases:
        try:
            plan = decomposer.decompose(c["request"], repo_root, llm_complete, agents)
            ok, reasons = check_plan(plan, c.get("expect", {}))
        except Exception as e:  # a broken plan is a failed eval, not a crash
            ok, reasons = False, [f"{type(e).__name__}: {e}"]
        passed += 1 if ok else 0
        details.append({"name": c["name"], "ok": ok, "reasons": reasons})
    total = len(cases) or 1
    rate = passed / total
    return {"passed": passed, "failed": total - passed, "pass_rate": round(rate, 4),
            "min_pass_rate": min_pass_rate, "ok": rate >= min_pass_rate, "details": details}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Run the JARVIS eval harness (regression gate).")
    ap.add_argument("--min", type=float, default=1.0, help="minimum pass rate to exit 0")
    args = ap.parse_args(argv)
    cases = load_cases()
    res = run_evals(make_mock_planner(cases), cases=cases, min_pass_rate=args.min)
    print(json.dumps(res, indent=2))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
