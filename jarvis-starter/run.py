#!/usr/bin/env python3
"""JARVIS CLI — the one-command hand-over entrypoint.

  python run.py "build a hello-world API"              # plan only (gate holds)
  python run.py --go "build a hello-world API"         # plan + run (auto-approve)
  python run.py --go --repo /path/to/project "..."     # target a repo

Needs live LLM creds (set in .env). Plan-only works to preview the DAG.
"""
import argparse, json, os, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from jarvis import orchestrator
from jarvis.llm import complete


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("request")
    ap.add_argument("--go", action="store_true", help="auto-approve and execute the DAG")
    ap.add_argument("--repo", default=os.getcwd(), help="repo root (default: cwd)")
    ap.add_argument("--concurrency", type=int, default=3)
    args = ap.parse_args()

    res = orchestrator.handle_request(
        args.request, str(pathlib.Path(args.repo).resolve()), complete,
        auto_approve=args.go, concurrency=args.concurrency)

    if res["status"] == "awaiting-approval":
        print(f"\nPlanned {len(res['tasks'])} tasks (gate is HOLDING — re-run with --go to execute):")
        for t in res["plan"].tasks:
            dep = f"  after {t.depends_on}" if t.depends_on else ""
            print(f"  [{t.id}] {t.agent}: {t.description}{dep}  scope={t.file_scope}")
    else:
        print(f"\nComplete. Tasks:")
        for t in res["tasks"]:
            print(f"  [{t['id']}] {t['agent']}: {t['status']}")


if __name__ == "__main__":
    main()
