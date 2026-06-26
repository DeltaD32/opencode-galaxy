#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "Pillow",
#   "python-pptx",
# ]
# ///

"""
fastmode_orchestrator.py - Route per-slide issues for delivery inner loops.

This script is intentionally lightweight:
- Runs structural + polish gates for selected slides
- Writes one issues_NN.json per slide
- Produces one issues_summary.json for orchestration/routing
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SLIDE_HEADER_RE = re.compile(r"^##\s*Slide\s+(\d+)\s*\[layout\s+(\d+)\]", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate and route issues_NN.json files.")
    p.add_argument("--storyline", required=True, help="Path to storyline markdown file")
    p.add_argument("--build-pptx", required=True, help="Path to build-stage PPTX")
    p.add_argument("--final-pptx", required=True, help="Path to polished/final PPTX")
    p.add_argument(
        "--issues-dir",
        default="",
        help="Output directory for issues_NN.json (default: <final-pptx-dir>/issues)",
    )
    p.add_argument(
        "--slides",
        default="",
        help="Optional comma-separated 1-based slides to process, e.g. 3,7",
    )
    p.add_argument(
        "--max-auto-iterations",
        type=int,
        default=2,
        help="Metadata only: suggested max automatic fix loops per slide.",
    )
    p.add_argument(
        "--allow-open-issues",
        action="store_true",
        help="Exit with code 0 even when open issues exist.",
    )
    return p.parse_args()


def parse_storyline_layouts(storyline_path: Path) -> dict[int, int]:
    layouts: dict[int, int] = {}
    for raw in storyline_path.read_text(encoding="utf-8").splitlines():
        m = SLIDE_HEADER_RE.match(raw.strip())
        if not m:
            continue
        slide_no = int(m.group(1))
        layout_no = int(m.group(2))
        layouts[slide_no] = layout_no
    return layouts


def parse_slides_arg(raw: str) -> list[int]:
    if not raw.strip():
        return []
    slides: set[int] = set()
    for part in raw.split(","):
        token = part.strip()
        if not token:
            continue
        slides.add(int(token))
    return sorted(slides)


def run_gate(cmd: list[str], json_path: Path) -> tuple[int, dict]:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    payload: dict
    if json_path.exists():
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    else:
        payload = {
            "check": "unknown",
            "passed": False,
            "errors": [f"Gate script did not write JSON: {' '.join(cmd)}"],
        }

    payload["exit_code"] = proc.returncode
    payload["stdout"] = (proc.stdout or "").strip()
    payload["stderr"] = (proc.stderr or "").strip()
    return proc.returncode, payload


def issue(owner: str, category: str, message: str) -> dict:
    return {
        "owner": owner,
        "category": category,
        "severity": "error",
        "message": message,
    }


def classify_slide(struct_payload: dict, polish_payload: dict) -> dict:
    issues: list[dict] = []

    for msg in struct_payload.get("errors", []):
        issues.append(issue(owner="build", category="structure", message=msg))

    for msg in polish_payload.get("errors", []):
        issues.append(issue(owner="polish", category="polish", message=msg))

    needs_build = any(i["owner"] == "build" for i in issues)
    needs_polish = any(i["owner"] == "polish" for i in issues)

    if needs_build and needs_polish:
        status = "needs_build_and_polish"
        next_worker = "build"
        recommended_order = ["build", "polish"]
    elif needs_build:
        status = "needs_build"
        next_worker = "build"
        recommended_order = ["build"]
    elif needs_polish:
        status = "needs_polish"
        next_worker = "polish"
        recommended_order = ["polish"]
    else:
        status = "clean"
        next_worker = "none"
        recommended_order = []

    return {
        "status": status,
        "next_worker": next_worker,
        "recommended_order": recommended_order,
        "issues": issues,
    }


def main() -> int:
    args = parse_args()
    storyline = Path(args.storyline).expanduser().resolve()
    build_pptx = Path(args.build_pptx).expanduser().resolve()
    final_pptx = Path(args.final_pptx).expanduser().resolve()
    issues_dir = (
        Path(args.issues_dir).expanduser().resolve()
        if args.issues_dir
        else final_pptx.parent / "issues"
    )
    raw_dir = issues_dir / "raw_gates"

    issues_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    layouts = parse_storyline_layouts(storyline)
    selected = parse_slides_arg(args.slides)
    slides = selected if selected else sorted(layouts.keys())
    if not slides:
        print("FAILED: No slides found. Check storyline headers: '## Slide N [layout X]'.")
        return 1

    script_dir = Path(__file__).resolve().parent
    structure_script = script_dir / "check_slide_structure.py"
    polish_script = script_dir / "check_slide_polish.py"

    summary = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "storyline": str(storyline),
        "build_pptx": str(build_pptx),
        "final_pptx": str(final_pptx),
        "max_auto_iterations": args.max_auto_iterations,
        "slides_checked": slides,
        "slides_clean": [],
        "slides_with_issues": [],
        "routing": {"build": [], "polish": [], "global": []},
        "issue_files": [],
    }

    for slide_no in slides:
        layout = layouts.get(slide_no)
        structure_json = raw_dir / f"slide_{slide_no:02d}_structure.json"
        polish_json = raw_dir / f"slide_{slide_no:02d}_polish.json"

        structure_cmd = [
            sys.executable,
            str(structure_script),
            "--pptx",
            str(build_pptx),
            "--slide",
            str(slide_no),
            "--json-out",
            str(structure_json),
        ]
        if layout is not None:
            structure_cmd.extend(["--layout", str(layout)])

        polish_cmd = [
            sys.executable,
            str(polish_script),
            "--pptx",
            str(final_pptx),
            "--slide",
            str(slide_no),
            "--json-out",
            str(polish_json),
        ]

        _, structure_payload = run_gate(structure_cmd, structure_json)
        _, polish_payload = run_gate(polish_cmd, polish_json)
        routed = classify_slide(structure_payload, polish_payload)

        slide_report = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "slide": slide_no,
            "layout": layout,
            "status": routed["status"],
            "next_worker": routed["next_worker"],
            "recommended_order": routed["recommended_order"],
            "issues": routed["issues"],
            "gates": {
                "structure": {
                    "passed": bool(structure_payload.get("passed")),
                    "exit_code": structure_payload.get("exit_code"),
                    "json_path": str(structure_json),
                },
                "polish": {
                    "passed": bool(polish_payload.get("passed")),
                    "exit_code": polish_payload.get("exit_code"),
                    "json_path": str(polish_json),
                },
            },
        }

        slide_file = issues_dir / f"issues_{slide_no:02d}.json"
        slide_file.write_text(
            json.dumps(slide_report, indent=2, ensure_ascii=True), encoding="utf-8"
        )
        summary["issue_files"].append(str(slide_file))

        if slide_report["status"] == "clean":
            summary["slides_clean"].append(slide_no)
        else:
            summary["slides_with_issues"].append(slide_no)

        if any(x["owner"] == "build" for x in slide_report["issues"]):
            summary["routing"]["build"].append(slide_no)
        if any(x["owner"] == "polish" for x in slide_report["issues"]):
            summary["routing"]["polish"].append(slide_no)
        if any(x["owner"] == "global" for x in slide_report["issues"]):
            summary["routing"]["global"].append(slide_no)

    summary_file = issues_dir / "issues_summary.json"
    summary_file.write_text(json.dumps(summary, indent=2, ensure_ascii=True), encoding="utf-8")

    print(f"Wrote per-slide issues to: {issues_dir}")
    print(f"Summary: {summary_file}")
    print(
        "Routing:"
        f" build={len(summary['routing']['build'])},"
        f" polish={len(summary['routing']['polish'])},"
        f" global={len(summary['routing']['global'])},"
        f" clean={len(summary['slides_clean'])}"
    )

    has_open = len(summary["slides_with_issues"]) > 0
    if has_open and not args.allow_open_issues:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
