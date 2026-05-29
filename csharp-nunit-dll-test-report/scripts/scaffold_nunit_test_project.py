#!/usr/bin/env python3
"""Create a NUnit test project for a C# DLL project when one does not exist."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> dict[str, object]:
    proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    output = (proc.stdout + "\n" + proc.stderr).strip()
    return {
        "command": " ".join(cmd),
        "exit_code": proc.returncode,
        "result": "Pass" if proc.returncode == 0 else "Fail",
        "output_tail": "\n".join(output.splitlines()[-80:]),
    }


def discover_solution(repo: Path) -> Path | None:
    solutions = sorted(repo.glob("*.sln"))
    return solutions[0] if solutions else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--dll-project", required=True, help="Path to the changed DLL .csproj, relative to repo or absolute.")
    parser.add_argument("--solution", default="", help="Optional .sln path. If omitted, the first repo-root .sln is used when present.")
    parser.add_argument("--test-project-name", default="", help="Defaults to <DllProjectName>.Tests.")
    parser.add_argument("--tests-root", default="tests")
    parser.add_argument("--output", default="scaffold-test-project-result.json")
    parser.add_argument("--fail-on-error", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    dll_project = Path(args.dll_project)
    if not dll_project.is_absolute():
        dll_project = repo / dll_project
    dll_project = dll_project.resolve()
    if not dll_project.exists():
        raise SystemExit(f"DLL project not found: {dll_project}")

    test_project_name = args.test_project_name or f"{dll_project.stem}.Tests"
    test_project_dir = repo / args.tests_root / test_project_name
    test_project = test_project_dir / f"{test_project_name}.csproj"

    steps = []
    created = False
    if test_project.exists():
        steps.append(
            {
                "command": "detect existing test project",
                "exit_code": 0,
                "result": "Pass",
                "output_tail": f"Using existing test project: {test_project}",
            }
        )
    else:
        test_project_dir.mkdir(parents=True, exist_ok=True)
        steps.append(run(["dotnet", "new", "nunit", "--name", test_project_name, "--output", str(test_project_dir)], repo))
        created = steps[-1]["result"] == "Pass"

    if test_project.exists():
        steps.append(run(["dotnet", "add", str(test_project), "reference", str(dll_project)], repo))

    solution = Path(args.solution).resolve() if args.solution else discover_solution(repo)
    if solution and solution.exists() and test_project.exists():
        steps.append(run(["dotnet", "sln", str(solution), "add", str(test_project)], repo))

    result = {
        "repo": str(repo),
        "dll_project": str(dll_project),
        "test_project": str(test_project),
        "test_project_dir": str(test_project_dir),
        "created": created,
        "solution": str(solution) if solution else "",
        "steps": steps,
        "overall": "Pass" if steps and all(step["result"] == "Pass" for step in steps) else "Fail",
    }

    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.fail_on_error and result["overall"] != "Pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
