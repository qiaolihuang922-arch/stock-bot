# DISPATCH.md

新對話先讀 `AGENTS.md`、本文件、`CURRENT_STATE.md`。本文件只保留接力必需資訊。

## Current Task

- task_id: `tg-evidence-short-ux-v20.4.13`
- task_name: `Telegram Short Evidence Noise Reduction`
- task_type: `tiny_patch`
- owner_status: `rejected_v20_4_12_raw_debug_evidence`
- architect_status: `qa_passed_pending_git_close`
- pm_status: `done`
- tech_status: `done`
- qa_status: `passed`
- latest_commit: see `git log -1`

## Current Result

- 本輪已完成 QA，收口時必須 commit / push 到 `origin/main`。
- Git completion gate：final 前必須以 `tools/cao_agent/check_git_completion_gate.sh` 驗證 `main` matches `origin/main` 且 worktree clean。
- 已吸收 PM -> Tech -> QA 交付到主 repo 工作樹：
  - 報文版本升至 `v20.4.13`。
  - TG message list 順序維持：messages[0] 持倉、messages[1] 未持倉 / 非持倉、messages[2] short/evidence；`include_detail=True` 時 Details Backup 仍追加在最後。
  - 第三則保留決策短訊，但過濾 raw/debug evidence 行，例如 `Source：核心價格`、`Source：漏斗 count`、`證據日期`、`來源：watchlist_breadth/sector_index`、`latest_trade_date`、`lookback_range`、`position_events`、`db_table`、`source_of_truth`、舊 `Evidence Compact`。
  - 第三則追加自然語言「簡短證據摘要」：持倉依據、未持倉依據、資料不足 fail-closed、最終結論。
  - 策略樣本 `missing-source` 仍 fail closed；不把 unavailable 樣本包裝成可買或推薦。
  - 不改策略 decision、持倉/未持倉判斷、DB schema、write path、live Telegram。
- 驗證：
  - QA 結論：`通過`。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py services/notifier.py`：passed。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_notifier.py`：119 passed，169 warnings（第三方 deprecation 類）。
  - `git diff --check`：passed。
  - QA 補充反證：手造 market/theme 只有 `sector_index` 的 sample，確認 raw summary 可能產生的 `來源：sector_index/latest_trade_date` 在第三則已被過濾；message order 仍為持倉、未持倉、short/evidence。
  - scoped 可吸收 diff：`TASK.md`、`CHANGELOG.md`、`QA_REPORT.md`、`core/generator.py`、`tests/test_generator_report.py`、`tests/test_market_theme_evidence.py`。

## Next Action

- 若 `git status --branch --short` 顯示未推送或 dirty，先完成 commit / push 並跑 `tools/cao_agent/check_git_completion_gate.sh`，不得開新產品任務。
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
