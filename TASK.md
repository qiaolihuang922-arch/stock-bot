# TASK: github_actions_manual_workflow_clean_inputs_20260604

## 任務狀態

- task_id：`github_actions_manual_workflow_clean_inputs_20260604`
- 任務類型：normal_patch
- 狀態：ready_for_tech
- 版本建議：不升 `core/generator.py` 報文版本
- QA 分級：L2

## Owner 問題

Owner 手動執行 GitHub Actions 時，手機畫面仍顯示舊 backfill 欄位 `start_date`、`end_date`、`backfill_version`，執行後 GitHub 回 `Unexpected inputs provided`。

## 使用者可見結果

GitHub Actions 手動執行入口只保留有效欄位：

- `run_mode`
- choices：`bot`、`daily_evidence`

不得再顯示或接受舊 backfill 手動欄位：

- `start_date`
- `end_date`
- `backfill_version`
- `backfill_may`
- `backfill_and_bot`

## 非目標

- 不改 Telegram 報文版本。
- 不改交易策略、RR、持倉風控。
- 不改 DB schema / write path。
- 不新增 live Telegram delivery。

## 影響模組與直接消費者

- GitHub Actions manual workflow UI。
- `.github/workflows/*`。
- `tests/test_workflow_runtime_config.py`。

## 輸出契約

- workflow file 使用新的乾淨 identity，避免 GitHub mobile app 沿用舊 workflow path/name 的 dispatch form cache。
- repo 只保留一個 stock bot workflow file。
- workflow_dispatch inputs 只包含 `run_mode`。

## 版本契約

- 不升 `core/generator.py` VERSION。
- GitHub workflow 名稱可改，以重置手動執行表單。

## 驗收條件

- `.github/workflows` 只剩新的乾淨 workflow file。
- workflow text 不含 `start_date`、`end_date`、`backfill_version`、`backfill_may`、`backfill_and_bot`。
- runtime config tests 通過。
- `git diff --check` 通過。

## 失敗標本與驗收路由

- 失敗標本：Owner 手機截圖顯示舊欄位並報錯 `Unexpected inputs provided: ["start_date", "end_date", "backfill_version"]`。
- 驗收路由：workflow yaml -> workflow_runtime_config tests -> git diff check。

## 禁止事項與阻塞條件

- 不得為了繞過錯誤重新啟用 backfill inputs。
- 不得新增 DB write / live Telegram。
- 若 clean workflow 仍包含舊欄位，阻塞。
