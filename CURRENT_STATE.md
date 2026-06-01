# CURRENT_STATE.md

新會話短上下文。先讀 `AGENTS.md`、`DISPATCH.md`，再讀本文件。

## Stable Context

- 專案：台股策略 Telegram 報文機器人。
- 正式結果以 git / runner 產生報文為準。
- 使用者可見報文版本在 `core/generator.py` 的 `VERSION`，目前 `origin/main` 為 `v20.4.11`。
- 固定 8 份 Markdown 不刪：`AGENTS.md`、`DISPATCH.md`、`RESEARCH.md`、`CURRENT_STATE.md`、`CLEANUP_PLAN.md`、`TASK.md`、`CHANGELOG.md`、`QA_REPORT.md`。
- Architect 是總控；產品 / 策略 / 報文 bug 或 feature 預設走 PM -> Tech -> QA。
- 跨日狀態、已執行交易、歷史 evidence 必須來自 production DB 或 Owner 指定持久來源；local/runtime/worktree 不能當跨日記憶。
- 缺資料、source-error、欄位不足或可信度不足時 fail closed。

## Latest Completed Work

- task_id：`risk_patch_20260531_holiday_report_execution_memory_evidence_dates`
- commits：
  - `6367d78 fix holiday execution memory report`
  - `4f19e16 docs mark holiday fix pushed`
- 結論：05/31 假日报文重複第二段停利已修並推送。
- 關鍵行為：
  - production cross-day execution memory 足夠時，英業達 2356 顯示已執行不重複。
  - prior take-profit guard 存在但 execution memory 缺失或 `sold_shares <= 0` 時，顯示 `停利記憶不足`，不輸出賣出股數，不進明日計畫。
  - market/theme evidence 顯示 actual/latest trade date 與 `lookback_range`。
  - strategy sample 0 與 market/theme production evidence 已分層。
- 驗證：QA `通過`；full pytest 264 passed，153 warnings（第三方 deprecation 類）。

## Current Worktree

- task_id：`intraday_20260601_report_sequence_execution_memory_noise_v20_4_11`
- 狀態：PM done / Tech done / QA `通過`，已 commit / push 到 `origin/main`。
- commit：見 `git log -1`。
- 關鍵行為：
  - 報文版本升到 `v20.4.11`。
  - Telegram 完整輸出順序為 Summary -> action body（持倉/未持倉）-> Evidence Compact -> optional Details Backup。
  - `build_report_context()` 產生共用 `evidence_manifest`，每個使用者可見資料欄位需標出 source_status、source_of_truth、db_table、trade/as_of date、decision_eligible 與 fallback_rule。
  - `evidence_manifest` 補 `stock.<name>.execution_memory`，讓 positions / position_events source truth 可被 evidence 消費。
  - 未持倉 BUY-like candidate 若 price / OHLCV / RR source 不足，Summary、漏斗、交易執行 / 明日計畫、卡片一致 fail closed。
  - Summary `🔥 最強` 已接 source eligibility gate；source-ineligible candidate 不顯示候選名、排序分、評級分，改為 `無有效進場標的`。
  - 混合候選已補強：source-valid BUY 與 runtime/local BUY-like 同報文時，有效 BUY 正常進 Summary / 漏斗 / execution / tomorrow；缺源候選只作不可行動診斷，且不顯示精確 RR / S / V / 價格。
  - 2356 第二段停利 stale guard：未從 position_events 確認「第二」/ `SECOND` / `TP2` 或至少兩筆 sell deltas 時，fail closed 為 `停利記憶不足`，不得說成第二段已執行。
  - verbose source/backtest/detail 噪音移到 compact evidence / details backup，主體保留決策和必要 source truth。
  - market/theme production evidence、strategy sample evidence、stock decision 三層保持分離；market/theme confirmed 不會變 BUY。
  - 不改 BUY/SELL、加減碼、停利停損、DB schema、write path、live Telegram。
- 驗證：
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py services/strategy_evidence.py`：passed。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_strategy_evidence.py tests/test_market_theme_evidence.py tests/test_notifier.py tests/test_cross_day_context.py tests/test_analysis_engine.py`：167 passed，165 warnings。
  - `git diff --check`：passed。
  - QA 補充反證：完整 message list 順序、2356 stale second-stage guard、噪音壓縮、production artifact schema/content 均 passed。
  - 先前 production read-only strategy evidence artifact 仍顯示缺 `classification backtest source-of-truth`，報文正確 fail closed，不回到舊式 `樣本 0｜樣本不足，不判讀`。
- 2356 production read-only artifact：
  - path：`.qa_tmp/production_readonly_2356_positions_events.json`。
  - 安全契約：`credential_values_included=false`、`schema_change=false`、`data_write=false`、`live_telegram=false`。
  - `positions` 摘要：2356 英業達 `shares=0`、`status=CLOSED`、`realized_profit_taken_ratio=0.5`、`last_realized_profit_date=2026-05-25`。
  - `position_events` 摘要：4 筆 sell summary，labels 皆為「賣出」，`second_stage_like_labels=[]`、`has_confirmed_second_stage_label=false`。
  - 解讀：production ledger 目前不是「仍持倉 225」；但也沒有可被報文稱為「已確認第二段停利」的 label。若 Owner 認定實際未賣，需另開 source-of-truth/ledger 稽核任務。
- Runner / 流程修正：
  - `tools/cao_agent/run_qa_code.sh` 已補 QA 啟動前同步主 repo handoff files 到 tech worktree，避免 QA 驗到 stale `CHANGELOG.md`。

## Data / Evidence Status

- production 2026-05 market/theme 資料已回填並通過 read-only audit：
  - `market_theme_confirmed_evidence`：180 rows，20 trade dates，`2026-05-04` 到 `2026-05-29`，duplicate groups 0。
  - `market_theme_index_daily_bars`：200 rows，20 trade dates，`2026-05-04` 到 `2026-05-29`，duplicate groups 0。
  - `sector_theme_members`：12 active mapping rows，只是 mapping，不是 daily history。
  - `daily_signal_snapshot`：每日當時版本留存，不要求舊五月回填為 current version。
- generator 已消費 production `market_theme_confirmed_evidence` history；不是 runtime/local 假資料。

## Next Development

- 本輪已 commit / push；重開對話後先以 `git status --branch --short` 與 `tools/cao_agent/check_git_completion_gate.sh` 確認狀態，不再依賴對話記憶。
- 只把 `CHANGELOG.md` 所列 scoped diff 當成本輪驗收範圍；工作樹其他旁支 dirty files 不能因本輪 QA 通過而整包吸收。
- 另開旁支：若 Owner 認定 2356 英業達實際未賣，查 production positions / position_events 為何目前 artifact 顯示 CLOSED / shares 0。
- 另開旁支：盤點全報文 `追高 / 追蹤` 相關文案。
- 另開旁支：Telegram reply markup 附著最後一則 message 的 delivery consumer 風險。

## Runner Gaps To Fix Later

- CAO auto wrapper QA conclusion parser 已在工作樹修正，待 commit。
- Tech worktree 曾殘留舊 candidate diff；新任務前應自動清理或阻塞並明確提示。
- QA production-read 任務已可用 `CAO_QA_USE_REPO_CONFIG=1` 避免 dummy config；QA sandbox DNS 仍可能失敗，可用 `scripts/smoke_market_theme_evidence_readonly.py --auxiliary-render-artifact-json` 生成 safe read-only artifact。
- QA worktree handoff sync 已補：每次 QA runner 啟動前從主 repo 同步固定 handoff Markdown，避免 stale TASK/CHANGELOG/QA_REPORT 造成反覆 conditional。
- 流程強化：完整報文任務的 QA probe 必須覆蓋 Summary 首屏、卡片、漏斗、交易執行 / 明日計畫，不只驗單一 formatter 或 manifest。
- Git completion gate 已補：repo 落地任務 final 前必須確認 worktree clean、branch 有 upstream、local HEAD 等於 upstream HEAD；標準命令為 `tools/cao_agent/check_git_completion_gate.sh`。
