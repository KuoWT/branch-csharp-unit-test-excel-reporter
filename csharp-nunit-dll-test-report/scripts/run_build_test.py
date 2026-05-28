#!/usr/bin/env python3
"""Run dotnet restore/build/test and write a compact JSON result."""

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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--solution", default="")
    parser.add_argument("--output", default="build-test-result.json")
    parser.add_argument("--no-restore", action="store_true")
    args = parser.parse_args()

    cwd = Path(args.repo).resolve()
    target = [args.solution] if args.solution else []
    steps = []
    if not args.no_restore:
        steps.append(run(["dotnet", "restore", *target], cwd))
    steps.append(run(["dotnet", "build", *target, "--no-restore"], cwd))
    steps.append(run(["dotnet", "test", *target, "--no-build"], cwd))

    result = {
        "restore": steps[0] if not args.no_restore else {"result": "Skipped"},
        "build": steps[1 if not args.no_restore else 0],
        "test": steps[2 if not args.no_restore else 1],
        "overall": "Pass" if all(s["result"] in {"Pass", "Skipped"} for s in steps) else "Fail",
    }
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["overall"] == "Pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
