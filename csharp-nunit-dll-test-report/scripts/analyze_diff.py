#!/usr/bin/env python3
"""Summarize C# changes between the latest tag and a local branch."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


METHOD_RE = re.compile(
    r"^\s*(?:public|protected|internal|private)\s+"
    r"(?:static\s+|virtual\s+|override\s+|async\s+|sealed\s+|new\s+)*"
    r"[\w<>\[\],\s.?]+\s+"
    r"(?P<name>[A-Za-z_]\w*)\s*\(",
    re.MULTILINE,
)

CLASS_RE = re.compile(r"\b(?:class|record|struct|interface)\s+(?P<name>[A-Za-z_]\w*)")


def git(args: list[str], cwd: Path) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True, stderr=subprocess.STDOUT).strip()


def try_git(args: list[str], cwd: Path) -> str | None:
    try:
        return git(args, cwd)
    except subprocess.CalledProcessError:
        return None


def resolve_base_tag(branch: str, cwd: Path) -> str:
    return (
        try_git(["describe", "--tags", "--abbrev=0", f"{branch}^"], cwd)
        or try_git(["describe", "--tags", "--abbrev=0", branch], cwd)
        or ""
    )


def changed_methods_for_file(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.suffix.lower() != ".cs":
        return []
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    class_match = CLASS_RE.search(text)
    class_name = class_match.group("name") if class_match else ""
    methods = []
    for match in METHOD_RE.finditer(text):
        name = match.group("name")
        if name in {"if", "for", "foreach", "while", "switch", "catch", "using", "lock"}:
            continue
        methods.append({"class": class_name, "function": name})
    return methods


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("branch")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--base-tag", default="")
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    cwd = Path(args.repo).resolve()
    branch = args.branch
    base_tag = args.base_tag or resolve_base_tag(branch, cwd)
    if not base_tag:
        raise SystemExit("No Git tag found. Provide --base-tag.")

    git(["rev-parse", "--verify", branch], cwd)
    commit = git(["rev-parse", branch], cwd)
    status = git(["status", "--short"], cwd)
    diff_range = f"{base_tag}..{branch}"
    changed = git(["diff", "--name-status", diff_range], cwd)

    files = []
    ignored_files = []
    for line in changed.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status_code = parts[0]
        file_path = parts[-1]
        if Path(file_path).suffix.lower() != ".cs":
            ignored_files.append(
                {
                    "file": file_path,
                    "change_type": {
                        "A": "Added",
                        "M": "Modified",
                        "D": "Deleted",
                        "R": "Renamed",
                    }.get(status_code[:1], "Unknown"),
                    "reason": "Ignored because extension is not .cs",
                }
            )
            continue
        methods = changed_methods_for_file(cwd / file_path)
        files.append(
            {
                "file": file_path,
                "change_type": {
                    "A": "Added",
                    "M": "Modified",
                    "D": "Deleted",
                    "R": "Renamed",
                }.get(status_code[:1], "Unknown"),
                "methods": methods,
            }
        )

    result = {
        "branch": branch,
        "base_tag": base_tag,
        "commit": commit,
        "working_tree_dirty": bool(status),
        "diff_range": diff_range,
        "files": files,
        "ignored_files": ignored_files,
    }

    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
