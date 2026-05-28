---
name: csharp-nunit-dll-test-report
description: Use when generating positive and negative NUnit test cases and an Excel IT test report for a C# DLL project by comparing a local branch against the latest Git tag. The workflow analyzes changed C# functions, creates or updates NUnit tests, runs dotnet build/test, generates a department-style .xlsx report, and decides whether the branch is allowed to push.
---

# C# NUnit DLL Test Report

Use this skill when the user asks to generate a positive/negative test report for a C# DLL project, especially with wording like "指定 xxx 分支產生正反相測試報告".

## Inputs

Required:
- Local Git branch name.

Optional:
- Site (`站點`)
- Request number (`申請單號`)
- User tester (`User 測試人員`)
- IT tester (`IT 測試人員`)
- Limited customer (`限定客戶`)
- Limited package (`限定PACKAGE`)
- Output path for the Excel report.

Defaults:
- Base version is the latest reachable Git tag.
- Test framework is NUnit.
- Report output is a modern `.xlsx` file.
- Do not push automatically.

## Workflow

1. Confirm the working tree state with `git status --short`.
2. Confirm the requested local branch exists.
3. Resolve the base tag:
   - Prefer `git describe --tags --abbrev=0 <branch>^` when the branch has commits after a tag.
   - Fall back to `git describe --tags --abbrev=0 <branch>`.
4. Compare `base_tag..branch`.
5. Identify changed `.cs` files and changed functions.
6. Inspect the existing solution/project layout:
   - `.sln`
   - DLL project `.csproj`
   - existing test project
   - existing NUnit package/version and naming style
7. Generate or update NUnit tests.
8. Run restore/build/test using the repo's existing commands where available. This step is required before generating the final report:
   - `dotnet restore`
   - `dotnet build`
   - `dotnet test`
9. Generate the Excel report even when restore/build/test fails. Failed commands must be recorded in the report and must make `Push Allowed = No`.
10. Validate the Excel report:
   - The file opens with `openpyxl.load_workbook(...)`.
   - The workbook has at least one visible worksheet.
   - `unzip -t` reports no archive errors.
   - Root and workbook relationship files use the package relationship namespace: `http://schemas.openxmlformats.org/package/2006/relationships`.
11. Mark push allowed only when all gate rules pass.

## Test Rules

For every changed function, create or verify:
- At least one positive NUnit test.
- At least one negative NUnit test.
- Test names clearly identify the target function and scenario.
- Assertions check behavior, not only "no exception".
- Negative tests cover invalid input, null/empty input, boundary values, permission/customer/package restrictions, or expected exceptions where relevant.

When behavior is unclear, generate a test skeleton with `Assert.Inconclusive(...)` only as a temporary marker and mark the report result as `Missing` or `Fail`. Do not count inconclusive tests as pass.

Use the repo's existing NUnit style. If no style exists, prefer:

```csharp
[TestFixture]
public class TargetClassTests
{
    [Test]
    public void MethodName_ValidInput_ReturnsExpectedResult()
    {
        // Arrange

        // Act

        // Assert
    }

    [Test]
    public void MethodName_InvalidInput_ThrowsExpectedException()
    {
        // Arrange

        // Act + Assert
        Assert.Throws<ArgumentException>(() => /* call */);
    }
}
```

## Excel Report

Generate a modern `.xlsx`; do not preserve legacy Excel binary format even if the department template file has an `.xlsx` extension.

Do not hand-write `.xlsx` files by manually zipping OOXML parts. Always generate the workbook through `scripts/generate_excel_report.py` or another real Excel library such as `openpyxl`. A hand-written workbook can pass `unzip -t` but still fail in Excel when relationship namespaces or worksheet targets are invalid.

The main workbook should contain:

1. `IT測試報告`
   - Follows the department template sections:
     - `站點`
     - `IT影響評估`
     - `申請單號`
     - `需求內容`
     - `情境`
     - `User 測試人員`
     - `限定客戶`
     - `限定PACKAGE`
     - `IT 測試人員`
   - The `情境` section should list positive and negative test scenarios grouped by changed function.

2. `測試明細`
   - One row per changed function and scenario.
   - Include function, file, change type, positive case/result, negative case/result, NUnit test name, and notes.

3. `執行結果`
   - Include branch, base tag, commit, build result, NUnit result, coverage result, report path, and push decision.

See `references/excel-report-template.md` for the field mapping.

## Push Gate

Push is allowed only when:
- `dotnet build` passes.
- `dotnet test` passes.
- Every changed function has at least one positive NUnit test.
- Every changed function has at least one negative NUnit test.
- All positive and negative tests pass.
- Excel report is generated successfully.

If any condition fails, report:

```text
FAIL: 不可 push
```

If all conditions pass, report:

```text
PASS: 可 push
```

Do not run `git push` unless the user explicitly asks after seeing the report.

## Helper Scripts

Use scripts when they fit the repo:
- `scripts/analyze_diff.py` summarizes branch/tag diff and likely changed C# functions.
- `scripts/run_build_test.py` runs restore/build/test and writes a JSON result.
- `scripts/generate_excel_report.py` creates the department-style `.xlsx` from JSON.

The scripts are helpers, not a substitute for engineering judgment. Inspect generated tests before treating the gate as passed.
