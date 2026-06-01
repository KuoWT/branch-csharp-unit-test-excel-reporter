#!/usr/bin/env python3
"""Generate the department-style C# NUnit DLL test report as standalone HTML."""

from __future__ import annotations

import argparse
import html
import json
from datetime import datetime
from pathlib import Path


def load_json(path: str) -> dict:
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def esc(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False)
    return html.escape(str(value), quote=True)


def status_class(value) -> str:
    text = str(value or "").strip().lower()
    if text in {"pass", "yes", "可 push"}:
        return "pass"
    if text in {"fail", "no", "missing", "inconclusive", "不可 push", "unknown"}:
        return "fail"
    if text in {"skipped", "not run"}:
        return "warn"
    return "neutral"


def badge(value) -> str:
    return f'<span class="badge {status_class(value)}">{esc(value)}</span>'


def scenario_key(row: dict) -> tuple[str, str, str]:
    return (
        str(row.get("file", "")),
        str(row.get("class", "")),
        str(row.get("function", "")),
    )


def diff_scope_rows(diff: dict) -> list[dict]:
    rows = []
    for item in diff.get("files", []):
        methods = item.get("methods") or []
        for method in methods:
            rows.append(
                {
                    "file": item.get("file", ""),
                    "class": method.get("class", ""),
                    "function": method.get("function", ""),
                    "change_type": item.get("change_type", "Unknown"),
                    "positive_case": "",
                    "positive_result": "Missing",
                    "positive_input": "",
                    "positive_output": "",
                    "negative_case": "",
                    "negative_result": "Missing",
                    "negative_input": "",
                    "negative_output": "",
                    "nunit_test": "",
                    "notes": "Test case requires implementation.",
                }
            )
    return rows


def collect_scenarios(diff: dict, tests: list[dict]) -> tuple[list[dict], list[dict]]:
    diff_rows = diff_scope_rows(diff)
    diff_keys = {scenario_key(row) for row in diff_rows}
    by_key = {scenario_key(row): row for row in diff_rows}
    out_of_scope = []

    for test in tests:
        key = scenario_key(test)
        if key not in diff_keys:
            out_of_scope.append(test)
            continue
        merged = {**by_key[key], **test}
        by_key[key] = merged

    return list(by_key.values()), out_of_scope


def table(headers: list[str], rows: list[list[str]], status_columns: set[int] | None = None) -> str:
    status_columns = status_columns or set()
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body_rows = []
    for row in rows:
        cells = []
        for index, value in enumerate(row):
            content = badge(value) if index in status_columns else esc(value)
            cells.append(f"<td>{content}</td>")
        body_rows.append(f"<tr>{''.join(cells)}</tr>")
    if not body_rows:
        body_rows.append(f'<tr><td colspan="{len(headers)}" class="empty">No data</td></tr>')
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"


def field_grid(fields: list[tuple[str, str]]) -> str:
    rows = []
    for label, value in fields:
        rows.append(f"<div class=\"field-label\">{esc(label)}</div><div class=\"field-value\">{esc(value)}</div>")
    return f"<div class=\"field-grid\">{''.join(rows)}</div>"


def build_step_rows(build: dict) -> list[list[str]]:
    rows = []
    for label, key in [("Restore", "restore"), ("Build", "build"), ("NUnit Test", "test")]:
        step = build.get(key, {})
        rows.append(
            [
                label,
                step.get("command", ""),
                step.get("exit_code", ""),
                step.get("result", "Unknown"),
                step.get("output_tail", ""),
            ]
        )
    return rows


def changed_item_rows(diff: dict) -> list[list[str]]:
    rows = []
    for item in diff.get("files", []):
        methods = item.get("methods") or [{"class": "", "function": "(unknown)"}]
        for method in methods:
            rows.append(
                [
                    item.get("file", ""),
                    item.get("change_type", "Unknown"),
                    method.get("class", ""),
                    method.get("function", ""),
                ]
            )
    return rows


def ignored_file_rows(diff: dict) -> list[list[str]]:
    return [
        [
            item.get("file", ""),
            item.get("change_type", "Unknown"),
            item.get("reason", "Ignored"),
        ]
        for item in diff.get("ignored_files", [])
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--diff-json", required=True)
    parser.add_argument("--build-json", default="")
    parser.add_argument("--tests-json", default="")
    parser.add_argument("--output", required=True)
    parser.add_argument("--site", default="")
    parser.add_argument("--request-no", default="")
    parser.add_argument("--requirement", default="")
    parser.add_argument("--user-tester", default="")
    parser.add_argument("--it-tester", default="")
    parser.add_argument("--customer", default="")
    parser.add_argument("--package", default="")
    args = parser.parse_args()

    diff = load_json(args.diff_json)
    build = load_json(args.build_json)
    tests_payload = load_json(args.tests_json) if args.tests_json else {}
    tests = tests_payload.get("tests", []) if tests_payload else []
    scenarios, out_of_scope_tests = collect_scenarios(diff, tests)

    build_pass = build.get("overall") == "Pass"
    build_step_pass = build.get("build", {}).get("result") == "Pass" or build_pass
    has_testable_function_changes = bool(scenarios)
    positive_ok = all(
        str(s.get("positive_result", "")).lower() == "pass"
        and str(s.get("positive_input", "")).strip()
        and str(s.get("positive_output", "")).strip()
        for s in scenarios
    ) and bool(scenarios)
    negative_ok = all(
        str(s.get("negative_result", "")).lower() == "pass"
        and str(s.get("negative_input", "")).strip()
        and str(s.get("negative_output", "")).strip()
        for s in scenarios
    ) and bool(scenarios)
    push_allowed = build_step_pass if not has_testable_function_changes else build_pass and positive_ok and negative_ok
    push_label = "Yes" if push_allowed else "No"

    impact = f"Base Tag {diff.get('base_tag', '')} 至 Branch {diff.get('branch', '')}，可測 C# function 變更共 {len(scenarios)} 筆。"
    requirement = args.requirement or f"依 {diff.get('diff_range', '')} diff 產生 NUnit 單元測試報告。"

    fields = [
        ("站點", args.site),
        ("IT影響評估", impact),
        ("申請單號", args.request_no),
        ("需求內容", requirement),
        ("User 測試人員", args.user_tester),
        ("限定客戶", args.customer),
        ("限定PACKAGE", args.package),
        ("IT 測試人員", args.it_tester),
        ("產生時間", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    ]

    scenario_rows = []
    index = 1
    for s in scenarios:
        for kind, case_key, result_key in [
            ("Positive", "positive_case", "positive_result"),
            ("Negative", "negative_case", "negative_result"),
        ]:
            scenario_rows.append(
                [
                    index,
                    kind,
                    s.get("file", ""),
                    s.get("class", ""),
                    s.get("function", ""),
                    s.get(case_key, ""),
                    s.get("positive_input" if kind == "Positive" else "negative_input", ""),
                    s.get("positive_output" if kind == "Positive" else "negative_output", ""),
                    s.get("nunit_test", ""),
                    "Pass expected behavior" if kind == "Positive" else "Reject invalid behavior",
                    s.get(result_key, ""),
                    s.get(result_key, "Missing"),
                    s.get("notes", ""),
                ]
            )
            index += 1

    detail_rows = [
        [
            diff.get("branch", ""),
            diff.get("base_tag", ""),
            diff.get("commit", ""),
            s.get("file", ""),
            s.get("class", ""),
            s.get("function", ""),
            s.get("change_type", ""),
            s.get("positive_case", ""),
            s.get("positive_input", ""),
            s.get("positive_output", ""),
            s.get("positive_result", "Missing"),
            s.get("negative_case", ""),
            s.get("negative_input", ""),
            s.get("negative_output", ""),
            s.get("negative_result", "Missing"),
            s.get("notes", ""),
        ]
        for s in scenarios
    ]

    result_rows = [
        ("Branch", diff.get("branch", ""), "指定本地分支"),
        ("Base Tag", diff.get("base_tag", ""), "最新 tag"),
        ("Commit", diff.get("commit", ""), "分支 HEAD"),
        ("Restore", build.get("restore", {}).get("result", "Unknown"), ""),
        ("Build", build.get("build", {}).get("result", "Unknown"), ""),
        (
            "NUnit Test",
            build.get("test", {}).get("result", "Unknown") if has_testable_function_changes else "Skipped",
            "" if has_testable_function_changes else "無 C# 函數變更，免執行 NUnit 覆蓋驗證",
        ),
        (
            "正向測試覆蓋",
            "Pass" if positive_ok else "Skipped" if not has_testable_function_changes else "Fail",
            "無 C# 函數變更，免正向測試" if not has_testable_function_changes else "每個 diff function 必須有正向測試、輸入、輸出且 pass",
        ),
        (
            "反向測試覆蓋",
            "Pass" if negative_ok else "Skipped" if not has_testable_function_changes else "Fail",
            "無 C# 函數變更，免反向測試" if not has_testable_function_changes else "每個 diff function 必須有反向測試、輸入、輸出且 pass",
        ),
        ("HTML Report", "Pass", args.output),
        ("Push Allowed", push_label, "無 C# 函數變更時 build pass 即可 push" if not has_testable_function_changes else "全部 gate pass 才允許 push"),
    ]

    validation_fields = [
        ("Diff JSON", args.diff_json),
        ("Build JSON", args.build_json),
        ("Tests JSON", args.tests_json),
        ("Diff Range", diff.get("diff_range", "")),
        ("Working Tree Dirty", diff.get("working_tree_dirty", "")),
        ("Coverage Scope", "Diff changed files/functions only"),
        ("Has Testable C# Function Changes", has_testable_function_changes),
        ("Scenario Count", len(scenarios)),
        ("Tests Payload Count", len(tests)),
        ("Out-of-Scope Tests Ignored", len(out_of_scope_tests)),
        ("Ignored Non-CS Files", len(diff.get("ignored_files", []))),
    ]

    test_payload_rows = [
        [
            item.get("file", ""),
            item.get("class", ""),
            item.get("function", ""),
            item.get("positive_case", ""),
            item.get("positive_input", ""),
            item.get("positive_output", ""),
            item.get("positive_result", ""),
            item.get("negative_case", ""),
            item.get("negative_input", ""),
            item.get("negative_output", ""),
            item.get("negative_result", ""),
            item.get("nunit_test", ""),
            item.get("notes", ""),
        ]
        for item in tests
    ]

    out_of_scope_rows = [
        [
            item.get("file", ""),
            item.get("class", ""),
            item.get("function", ""),
            item.get("positive_case", ""),
            item.get("negative_case", ""),
            "Ignored: outside diff scope",
        ]
        for item in out_of_scope_tests
    ]

    html_text = f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>C# NUnit 單元測試報告</title>
  <style>
    :root {{
      --ink: #17202a;
      --muted: #5d6d7e;
      --line: #d5dce4;
      --head: #1f4e78;
      --head-text: #ffffff;
      --band: #f4f7fb;
      --pass-bg: #dff3df;
      --pass-text: #1e6b2d;
      --fail-bg: #f9d5d3;
      --fail-text: #9b1c17;
      --warn-bg: #fff2c2;
      --warn-text: #7a5b00;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      font: 14px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft JhengHei", sans-serif;
      background: #ffffff;
    }}
    main {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 28px 24px 48px;
    }}
    header {{
      border-bottom: 3px solid var(--head);
      margin-bottom: 22px;
      padding-bottom: 14px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 26px;
      letter-spacing: 0;
    }}
    h2 {{
      margin: 30px 0 12px;
      font-size: 20px;
      border-left: 5px solid var(--head);
      padding-left: 10px;
    }}
    .summary-line {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px 18px;
      color: var(--muted);
    }}
    .decision {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin-top: 10px;
      font-weight: 700;
    }}
    .field-grid {{
      display: grid;
      grid-template-columns: minmax(130px, 180px) 1fr;
      border: 1px solid var(--line);
      border-bottom: 0;
    }}
    .field-label, .field-value {{
      border-bottom: 1px solid var(--line);
      padding: 10px 12px;
      min-height: 40px;
    }}
    .field-label {{
      background: var(--band);
      font-weight: 700;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
      margin-bottom: 20px;
    }}
    th, td {{
      border: 1px solid var(--line);
      padding: 8px 9px;
      vertical-align: top;
      overflow-wrap: anywhere;
      white-space: pre-wrap;
    }}
    th {{
      background: var(--head);
      color: var(--head-text);
      font-weight: 700;
      text-align: left;
    }}
    tr:nth-child(even) td {{ background: #fbfcfe; }}
    .badge {{
      display: inline-block;
      min-width: 68px;
      border-radius: 999px;
      padding: 2px 9px;
      text-align: center;
      font-weight: 700;
    }}
    .badge.pass {{ background: var(--pass-bg); color: var(--pass-text); }}
    .badge.fail {{ background: var(--fail-bg); color: var(--fail-text); }}
    .badge.warn {{ background: var(--warn-bg); color: var(--warn-text); }}
    .badge.neutral {{ background: #e8edf3; color: #34495e; }}
    .empty {{
      color: var(--muted);
      text-align: center;
      padding: 18px;
    }}
    details {{
      border: 1px solid var(--line);
      margin: 0 0 14px;
      background: #ffffff;
    }}
    summary {{
      cursor: pointer;
      padding: 10px 12px;
      background: var(--band);
      font-weight: 700;
    }}
    pre {{
      margin: 0;
      padding: 12px;
      overflow: auto;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      background: #fbfcfe;
      border-top: 1px solid var(--line);
      font: 12px/1.5 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    }}
    @media print {{
      main {{ max-width: none; padding: 12mm; }}
      table {{ page-break-inside: auto; }}
      tr {{ page-break-inside: avoid; page-break-after: auto; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>IT測試報告</h1>
      <div class="summary-line">
        <span>Branch: {esc(diff.get("branch", ""))}</span>
        <span>Base Tag: {esc(diff.get("base_tag", ""))}</span>
        <span>Commit: {esc(diff.get("commit", ""))}</span>
      </div>
      <div class="decision">Push Allowed: {badge(push_label)}</div>
    </header>

    <section>
      <h2>IT測試報告</h2>
      {field_grid(fields)}
    </section>

    <section>
      <h2>情境</h2>
      {table(["編號", "類型", "檔案", "類別", "Function", "測試情境", "輸入", "輸出", "NUnit Test", "預期結果", "實際結果", "結果", "備註"], scenario_rows, {11})}
    </section>

    <section>
      <h2>測試明細</h2>
      {table(["Branch", "Base Tag", "Commit", "File", "Class", "Function", "Change Type", "Positive Case", "Positive Input", "Positive Output", "Positive Result", "Negative Case", "Negative Input", "Negative Output", "Negative Result", "Notes"], detail_rows, {10, 14})}
    </section>

    <section>
      <h2>執行結果</h2>
      {table(["項目", "結果", "備註"], [list(row) for row in result_rows], {1})}
    </section>

    <section>
      <h2>驗證資料</h2>
      {field_grid(validation_fields)}

      <h3>異動檔案與 Function</h3>
      {table(["File", "Change Type", "Class", "Function"], changed_item_rows(diff))}

      <h3>忽略的非 .cs 檔案</h3>
      {table(["File", "Change Type", "Reason"], ignored_file_rows(diff))}

      <h3>Restore / Build / NUnit Test 輸出</h3>
      {table(["Step", "Command", "Exit Code", "Result", "Output Tail"], build_step_rows(build), {3})}

      <h3>Tests JSON 案例資料</h3>
      {table(["File", "Class", "Function", "Positive Case", "Positive Input", "Positive Output", "Positive Result", "Negative Case", "Negative Input", "Negative Output", "Negative Result", "NUnit Test", "Notes"], test_payload_rows, {6, 10})}

      <h3>非 Diff 範圍案例</h3>
      {table(["File", "Class", "Function", "Positive Case", "Negative Case", "處理方式"], out_of_scope_rows)}

      <details>
        <summary>Diff JSON 原始資料</summary>
        <pre>{esc(json.dumps(diff, ensure_ascii=False, indent=2))}</pre>
      </details>
      <details>
        <summary>Build JSON 原始資料</summary>
        <pre>{esc(json.dumps(build, ensure_ascii=False, indent=2))}</pre>
      </details>
      <details>
        <summary>Tests JSON 原始資料</summary>
        <pre>{esc(json.dumps(tests_payload, ensure_ascii=False, indent=2))}</pre>
      </details>
    </section>
  </main>
</body>
</html>
"""

    required = ["IT測試報告", "測試明細", "執行結果", "驗證資料"]
    for marker in required:
        if marker not in html_text:
            raise ValueError(f"Missing required section: {marker}")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html_text, encoding="utf-8")
    print(f"Saved {output}")
    print("PASS: 可 push" if push_allowed else "FAIL: 不可 push")
    return 0 if push_allowed else 2


if __name__ == "__main__":
    raise SystemExit(main())
