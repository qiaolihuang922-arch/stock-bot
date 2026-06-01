# DISPATCH.md

新對話先讀 `AGENTS.md`、本文件、`CURRENT_STATE.md`。本文件只保留接力必需資訊。

## Current Task

- task_id: `tiny_patch_cleanup_unused_variables_analysis_py_20260601`
- task_name: `Cleanup Unused Variables In Analysis`
- task_type: `tiny_patch`
- owner_status: `requested_batch_task_3_after_task_1`
- architect_status: `qa_passed_pending_git_close`
- pm_status: `done`
- tech_status: `done`
- qa_status: `passed`
- latest_commit: see `git log -1`

## Current Follow-up

- task_id: `report_v20_4_21_afterhours_brief_evidence_merge`
- task_name: `V20.4.21 Afterhours Brief Evidence Merge`
- task_type: `normal_patch`
- architect_status: `qa_passed_pending_git_close`
- qa_status: `passed`

## Current Result

- 任務一已完成並推送：commit `1f9601d fix wait breakout rr gap reason`，Git completion gate passed。
- 本輪目標是任務三：清理 `services/analysis.py` 三處指定 unused / redundant dead code。
- 修正：刪除 `detect_entry_stage()` unused `breakout_lv`、`holding_signal()` unused `profile`、`pick_best_stock()` redundant C/D filter；保留 A+/A allowlist。
- QA：Re-QA `通過`；確認 scoped diff 只刪 8 行，沒有策略 / 輸出 / DB / Telegram / VERSION 變更。
- 靜態檢查：pyflakes / ruff / flake8 環境缺失；Tech/QA 改用 AST targeted static check 與 direct consumer probe，符合 tiny_patch L1 範圍。
- 流程事件：第一次 QA 因 main `CHANGELOG.md` stale 成任務一內容而 blocked；已同步任務三 CHANGELOG 後 Re-QA 通過。
- Git completion gate：final 前必須以 `tools/cao_agent/check_git_completion_gate.sh` 驗證 `main` matches `origin/main` 且 worktree clean。
- 上一輪 v20.4.21 報文修正已在 commit `b177345 restore afterhours control summary` 推送，本輪不再改動該產品 diff。
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
  - 盤後第三則恢復 `持倉風控檢查` 與 `未持倉漏斗（非執行）`。
  - 資料依據合併市場短期背景、持倉數、未持倉分類數、執行記憶邊界與持倉 RR 邊界。
  - Re-QA output：`.cao_agent_context/outputs/20260601_185800_22905_stock_qa_code_readonly.answer.txt`，結論 `通過`。
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
