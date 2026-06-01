# DISPATCH.md

新對話先讀 `AGENTS.md`、本文件、`CURRENT_STATE.md`。本文件只保留接力必需資訊。

## Current Task

- task_id: `report_v20_4_21_mobile_readability_remaining_fixes`
- task_name: `V20.4.21 Mobile Readability Remaining Fixes`
- task_type: `normal_patch`
- owner_status: `requested_start_repair_current_issues`
- architect_status: `qa_passed_pending_git_close`
- pm_status: `done`
- tech_status: `manual_absorb_from_tech_worktree`
- qa_status: `passed`
- latest_commit: see `git log -1`

## Current Follow-up

- task_id: `report_v20_4_21_holding_rr_conflict_followup`
- task_name: `V20.4.21 Holding RR Conflict Follow-up`
- task_type: `normal_patch`
- architect_status: `qa_passed_pending_git_close`
- qa_status: `passed`

## Current Result

- 本輪目標是修 v20.4.21 剩餘手機閱讀問題：三日資料只稱短期背景、非加碼持倉 RR 一致、盤後下一步用明日語境、未持倉卡片資料來源降噪、第三則資料依據人話化。
- Git completion gate：final 前必須以 `tools/cao_agent/check_git_completion_gate.sh` 驗證 `main` matches `origin/main` 且 worktree clean。
- 已吸收內容：
  - `presentation/report.py` 將 `交易證據日` 改為短期背景 / 短期背景資料。
  - 盤後 `盤中先觀察` / `盤中觀察修復狀況` 改為明日語境。
  - 盤後未持倉卡片不再逐張輸出長資料來源句。
  - 第三則資料依據改為：持倉與價格支持風控；未持倉只支持分類觀察，不支持直接進場。
  - VERSION 仍為 `v20.4.21`；strategy decision、RR 計算、holding_status、DB write path 無變更。
- 驗證：
  - QA 結論：`通過`。
  - Re-QA output：`.cao_agent_context/outputs/20260601_181248_1516_stock_qa_code_readonly.answer.txt`，結論 `通過`。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m py_compile presentation/report.py tests/test_generator_report.py tests/test_market_theme_evidence.py`：passed。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py`：128 passed，181 warnings。
  - QA source-error phone-order probe：passed。
  - `git diff --check`：passed。
  - scoped diff：`presentation/report.py`、`tests/test_generator_report.py`、`tests/test_market_theme_evidence.py`、固定 handoff Markdown。
- Follow-up 驗證：
  - 建準 dry-run 卡片已顯示 `數據：新倉 RR：不適用（既有持倉）`，不再顯示 `數據：RR 2.73`。
  - Re-QA output：`.cao_agent_context/outputs/20260601_183214_25279_stock_qa_code_readonly.answer.txt`，結論 `通過`。
  - `tests/test_generator_report.py`：92 passed，181 warnings。
  - presentation boundary gate：未新增 DB writer、evidence writer、schema alter 或 fake production path。

## Next Action

- 收口：commit / push 後跑 `tools/cao_agent/check_git_completion_gate.sh`。
- 後續同類報文任務：先補或更新手機閱讀 probe，再改 formatter；不要只寫規則。
- 旁支另開：Telegram reply markup 仍附在最後一則 message，新 message order 下可能需要 delivery consumer 任務評估按鈕落點。
- 旁支另開：如果 Owner 認定 2356 英業達實際未賣，需查 production ledger/source truth 為何目前為 `shares=0 / CLOSED`；本輪未寫 DB、不校正 ledger。

## Fixed Commands

Owner 對 Architect：

```text
你是 Architect / 總控，不是 PM、Tech、QA。先讀 AGENTS.md、DISPATCH.md、CURRENT_STATE.md；產品/策略/報文 feature 先分派 PM，不直接寫產品代碼。
```

Architect 入口：

```text
tools/cao_agent/run_architect_task.sh research "<研究問題>"
tools/cao_agent/run_architect_task.sh plan "<技術規劃問題>"
tools/cao_agent/run_architect_task.sh auto "<Owner 任務>"
```

CAO 服務：

```text
tools/cao_agent/ensure_cao_services.sh
CAO API: http://127.0.0.1:9889/
CAO UI:  http://127.0.0.1:5173/
```
