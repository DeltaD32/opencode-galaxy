# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""Analyzes the current git branch to extract information for Jira story creation.

Outputs JSON with branch info, commits, and status.
"""

import json
import re
import subprocess
import sys


def run(cmd: list[str], *, check: bool = True) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, check=check)
    return result.stdout.strip()


def get_default_branch() -> str:
    try:
        ref = run(["git", "symbolic-ref", "refs/remotes/origin/HEAD"])
        return re.sub(r"^refs/remotes/origin/", "", ref)
    except subprocess.CalledProcessError:
        return "main"


def get_merge_base(default_branch: str) -> str | None:
    for ref in [f"origin/{default_branch}", default_branch]:
        try:
            return run(["git", "merge-base", "HEAD", ref])
        except subprocess.CalledProcessError:
            continue
    return None


def get_commits(merge_base: str) -> list[dict]:
    log_format = "%H%n%an%n%ai%n%s%n---"
    raw = run(["git", "log", f"{merge_base}..HEAD", f"--pretty=format:{log_format}"])
    if not raw:
        return []

    commits = []
    for entry in raw.split("---"):
        lines = [line for line in entry.strip().splitlines() if line]
        if len(lines) >= 4:
            commits.append(
                {
                    "hash": lines[0],
                    "author": lines[1],
                    "date": lines[2],
                    "message": lines[3],
                }
            )
    return commits


def get_files_changed(merge_base: str) -> list[dict]:
    raw = run(["git", "diff", "--name-status", f"{merge_base}..HEAD"])
    if not raw:
        return []

    files = []
    for line in raw.splitlines():
        parts = line.split("\t", 1)
        if len(parts) == 2:
            files.append({"status": parts[0], "file": parts[1]})
    return files


def get_behind_count(default_branch: str) -> int:
    run(["git", "fetch", "origin", default_branch, "--quiet"], check=False)
    try:
        count = run(["git", "rev-list", "--count", f"HEAD..origin/{default_branch}"])
        return int(count)
    except (subprocess.CalledProcessError, ValueError):
        return 0


def main() -> None:
    current_branch = run(["git", "branch", "--show-current"])
    default_branch = get_default_branch()

    match = re.match(r"^(feature|fix)/(.+)$", current_branch)
    if match:
        branch_type = match.group(1)
        branch_name = match.group(2)
    else:
        branch_type = "other"
        branch_name = current_branch

    merge_base = get_merge_base(default_branch)

    if merge_base:
        commits = get_commits(merge_base)
        files_changed = get_files_changed(merge_base)
    else:
        commits = []
        files_changed = []

    behind_count = get_behind_count(default_branch)

    output = {
        "current_branch": current_branch,
        "branch_type": branch_type,
        "branch_name": branch_name,
        "default_branch": default_branch,
        "commits": commits,
        "files_changed": files_changed,
        "is_behind": behind_count > 0,
        "behind_count": behind_count,
    }

    json.dump(output, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
