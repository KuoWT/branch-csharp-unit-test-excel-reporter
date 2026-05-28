# HTML Report Template

Generate a standalone UTF-8 `.html` report with these sections.

## IT測試報告

This section mirrors the department test report template.

Top fields:

| Field | Value source |
|---|---|
| 站點 | User input or project/site config |
| IT影響評估 | Summary generated from changed files/functions |
| 申請單號 | User input; leave blank if absent |
| 需求內容 | Commit/diff summary plus user-supplied requirement text |
| User 測試人員 | User input; leave blank if absent |
| IT 測試人員 | User input or current engineer/agent |
| 限定客戶 | User input or test condition |
| 限定PACKAGE | User input or test condition |

Scenario table columns:

| Column | Meaning |
|---|---|
| 編號 | Sequential scenario number |
| 類型 | Positive or Negative |
| 檔案 | Changed C# file |
| 類別 | Class name if known |
| Function | Changed function |
| 測試情境 | Human-readable test scenario |
| NUnit Test | NUnit test method name |
| 預期結果 | Expected behavior |
| 實際結果 | Test result or failure message |
| 結果 | Pass, Fail, Missing, or Inconclusive |
| 備註 | Notes |

## 測試明細

Columns:

| Column | Meaning |
|---|---|
| Branch | Requested local branch |
| Base Tag | Latest tag used as comparison base |
| Commit | Branch head commit |
| File | Changed file |
| Class | Changed class if known |
| Function | Changed function |
| Change Type | Added, Modified, Deleted, or Unknown |
| Positive Case | Positive NUnit scenario/test |
| Positive Result | Pass, Fail, Missing, or Inconclusive |
| Negative Case | Negative NUnit scenario/test |
| Negative Result | Pass, Fail, Missing, or Inconclusive |
| Notes | Details or follow-up |

## 執行結果

Columns:

| 項目 | 結果 | 備註 |
|---|---|---|
| Branch | branch name | Requested local branch |
| Base Tag | tag name | Latest tag comparison base |
| Commit | SHA | Branch head |
| Restore | Pass/Fail | Command output summary |
| Build | Pass/Fail | Command output summary |
| NUnit Test | Pass/Fail | Command output summary |
| 正向測試覆蓋 | Pass/Fail | Every changed function has a positive test |
| 反向測試覆蓋 | Pass/Fail | Every changed function has a negative test |
| HTML Report | Pass/Fail | Report generated |
| Push Allowed | Yes/No | Yes only if all gates pass |

## 驗證資料

This section must include the data used to validate the report decision.

Include:

| Item | Meaning |
|---|---|
| Diff JSON | Path passed to `--diff-json` |
| Build JSON | Path passed to `--build-json` |
| Tests JSON | Path passed to `--tests-json`, if any |
| Diff Range | Tag-to-branch comparison range |
| Changed Files | Changed C# files used for test generation |
| Changed Functions | Class/function pairs used for coverage checks |
| Restore Command | Command, exit code, result, and output tail |
| Build Command | Command, exit code, result, and output tail |
| NUnit Test Command | Command, exit code, result, and output tail |
| Test Payload | Positive/negative case data from tests-json, if provided |

## Formatting

- Use a printable, self-contained HTML page.
- Use readable tables with sticky-looking headers through CSS only; no JavaScript required.
- Use green badges for `Pass` and `Yes`.
- Use red badges for `Fail`, `Missing`, `Inconclusive`, and `No`.
- Use wrapped text for scenario, command output, and notes fields.
