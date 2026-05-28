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
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Return a non-zero exit code when restore/build/test fails. By default the JSON result is written and the command exits 0 so report generation can continue.",
    )
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
    if args.fail_on_error and result["overall"] != "Pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
