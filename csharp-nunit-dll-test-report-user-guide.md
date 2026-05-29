# C# DLL 正反相測試報告 Skill 使用說明

## 這個 Skill 做什麼

這個 Skill 用來協助 C# DLL 專案產生 NUnit 正反相測試與 HTML 測試報告。

使用者只要指定本地分支，Skill 會根據該分支與最新 Git tag 的差異，找出有異動的 C# function，協助產生或檢查單元測試，執行 build/test，最後產出 HTML 報告並判斷是否可 push。

## 適用情境

- C# DLL 專案
- 使用 NUnit 作為測試框架
- 希望根據分支差異產生測試報告
- 需要確認每個異動 function 都有正向與反向測試
- 需要在 push 前確認測試是否全部通過

## 使用前需要準備

請提供：

```text
repo 路徑
本地分支名稱
```

例如：

```text
repo: /Users/kevin/Documents/MyDllProject
branch: feature/update-fee-rule
```

可選提供：

```text
站點
申請單號
User 測試人員
IT 測試人員
限定客戶
限定PACKAGE
```

## 建議使用方式

可以直接對 Agent 說：

```text
使用 csharp-nunit-dll-test-report skill，
針對 /Users/kevin/Documents/MyDllProject 的 feature/update-fee-rule 分支，
用最新 tag 比對，產生 C# DLL NUnit 正反相測試與 HTML 測試報告。
```

## Skill 執行流程

1. 確認指定本地分支存在
2. 取得最新 Git tag 作為上版本基準
3. 比對 `最新 tag..指定分支`
4. 找出 diff 範圍內異動的 `.cs` 檔案與 function，其他副檔名忽略
5. 新增或更新 NUnit 測試
6. 若沒有合適測試專案，建立 NUnit test project
7. 執行：

```bash
dotnet restore
dotnet build
dotnet test
```

8. 產生 HTML 測試報告
9. 判斷是否可 push

## HTML 報告會包含什麼

HTML 報告包含：

- `IT測試報告`
- `情境`
- `測試明細`
- `執行結果`
- `驗證資料`

重點欄位：

| 欄位 | 說明 |
|---|---|
| Branch | 指定分支 |
| Base Tag | 比對用最新 tag |
| File | 異動檔案 |
| Function | 異動 function |
| Positive Case | 正向測試案例 |
| Positive Input | 正向測試輸入 |
| Positive Output | 正向測試輸出 |
| Positive Result | 正向測試結果 |
| Negative Case | 反向測試案例 |
| Negative Input | 反向測試輸入 |
| Negative Output | 反向測試輸出 |
| Negative Result | 反向測試結果 |
| Push Allowed | 是否可 push |

## 覆蓋範圍規則

報告只檢查 diff 範圍內的異動 function。

也就是說，只有 `最新 tag..指定分支` 中有異動的 C# function 會被納入覆蓋檢查。

只有副檔名為 `.cs` 的改動會產生或檢查單元測試，其餘副檔名會忽略。

如果沒有 `.cs` 改動，測試項目會是空的，不會產生假的測試項目。

如果測試資料中包含非 diff 範圍的 function，報告會列在「非 Diff 範圍案例」，但不會計入是否可 push。

## 可 Push 條件

全部符合才會顯示：

```text
PASS: 可 push
```

條件包含：

- `dotnet build` 通過
- `dotnet test` 通過
- 每個 diff function 都有正向測試
- 每個 diff function 都有反向測試
- 每個正反向測試都有輸入與輸出說明
- 所有正反向測試都 pass
- HTML 報告成功產出

只要任一條件失敗，就會顯示：

```text
FAIL: 不可 push
```

## 注意事項

- Skill 不會自動 push，除非使用者明確要求
- build 或 test 失敗時仍會產生 HTML 報告
- 失敗報告會列出原因與驗證資料，方便工程師修正
- HTML 報告可直接用瀏覽器開啟
