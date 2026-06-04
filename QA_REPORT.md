# QA_REPORT:

## 測試範圍

- 任務：`github_actions_manual_workflow_clean_inputs_20260604`。
- 範圍：GitHub Actions manual workflow dispatch schema、runtime config tests、舊 workflow / 舊 inputs 清理。
- 未測：GitHub mobile app 真實 UI，需 push 後重新打開 Actions list 驗證。

## 風險預算與停止條件

- 風險 1：舊 workflow path/name 讓手機端沿用舊表單。驗證：刪除舊 `.github/workflows/stock-bot.yml`，新增 `stock-bot-clean.yml` 並改 workflow name。停止條件：舊 file 仍存在。
- 風險 2：舊 backfill inputs 仍在 schema。驗證：workflow text 不含 `start_date`、`end_date`、`backfill_version`、`backfill_may`、`backfill_and_bot`。停止條件：任一舊欄位仍存在。
- 風險 3：清 workflow 時破壞 daily_evidence / bot runtime config。驗證：`tests/test_workflow_runtime_config.py` 全檔通過。停止條件：runtime config tests failed。

## 關聯風險掃描

- 新 workflow 仍保留 schedule `0 6 * * 1-5`。
- `workflow_dispatch.inputs` 只保留 `run_mode`。
- `Run Phase 3 evidence automation` 與 `Run bot (retry 3 times)` 邏輯未變。
- 未新增 DB write / live Telegram path。

## 跨區塊語意一致性

- TASK 要求只留 `bot` / `daily_evidence`；workflow text 與 tests 一致。
- CHANGELOG 宣告不升報文版本；diff 未改 `core/generator.py`。
- workflow file rename 與測試 `WORKFLOW` path 同步。

## 使用者誤讀風險

- 新 GitHub Actions workflow 名稱是 `Stock Bot`，用來避開手機端舊 `Stock Bot Pro` 表單 cache。
- Owner 需在 GitHub Actions list 點新的 `Stock Bot` workflow；如果看到舊 `Stock Bot Pro` 歷史項目，不應再從該項手動 dispatch。

## 質疑與反證

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/workflow_clean_inputs_pytest arch -arm64 ./.venv/bin/python -m pytest tests/test_workflow_runtime_config.py -q` -> 9 passed。
- `git diff --check` -> passed。
- `find .github/workflows -maxdepth 1 -type f -print` -> only `.github/workflows/stock-bot-clean.yml`。

## 未測項目

- 未實際從 GitHub mobile app 點擊 Run Workflow。
- 未跑 full pytest。
- 未觸發 live Telegram。
- 未做 DB write/backfill。

## QA 結論

通過。
