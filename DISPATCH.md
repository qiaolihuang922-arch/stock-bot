# DISPATCH.md

新對話先讀 `AGENTS.md`、本文件、`CURRENT_STATE.md`。本文件只保留接力必需資訊。

## Current Task

- task_id: `intraday_20260601_report_sequence_execution_memory_noise_v20_4_11`
- task_name: `Intraday Report Sequence / Execution Memory / Noise Compression`
- task_type: `risk_patch`
- owner_status: `reported_0601_intraday_report_order_2356_noise_gap`
- architect_status: `absorbed_agent_diff_and_reviewed`
- pm_status: `done`
- tech_status: `done`
- qa_status: `passed`
- latest_commit: see `git log -1`

## Current Result

- 本輪已 commit / push 到 `origin/main`。
- Git completion gate：push 後必須以 `tools/cao_agent/check_git_completion_gate.sh` 驗證 `main` matches `origin/main` 且 worktree clean。
- 已吸收 PM -> Tech -> QA 交付到主 repo 工作樹：
  - 報文版本升至 `v20.4.11`。
  - `formatTelegramMessages()` 固定輸出：Summary -> action body（持倉/未持倉）-> Evidence Compact -> optional Details Backup。
  - 主體行動不再被 verbose source/backtest/detail 噪音插在前面；長證據移到 compact evidence / details backup。
  - 2356 第二段停利 execution memory 補 stale guard：position_events 未明確確認「第二」/ `SECOND` / `TP2` 或至少兩筆 sell deltas 時，fail closed 為 `停利記憶不足`，不得顯示第二段已執行或重複賣出股數。
  - `evidence_manifest` 補 `stock.<name>.execution_memory`，把 positions / position_events source truth 暴露給 report evidence。
  - 不改 BUY/SELL、加減碼、停利停損策略 engine、DB schema、write path、live Telegram。
- Production read-only artifact：
  - `.qa_tmp/production_readonly_2356_positions_events.json` 已生成並由 QA 驗證。
  - artifact 安全旗標：無 credential、無 write、無 schema change、無 live Telegram。
  - artifact 顯示 production `positions` 目前 2356 英業達為 `shares=0`、`status=CLOSED`；`position_events` 有 4 筆 sell summary，但無 second-stage-like labels。
  - 因此報文不得把一般 `賣出` 事件升格成「已確認第二段停利 event」；若使用者認知仍為未賣，下一步是查 production ledger/source truth，不是讓報文猜。
- Runner gap 已修：
  - `tools/cao_agent/run_qa_code.sh` 會在 QA 啟動前同步主 repo handoff files 到可重用 tech worktree，避免 QA 驗到 stale `TASK.md / CHANGELOG.md / QA_REPORT.md`。
  - 保留既有 `CAO_QA_USE_REPO_CONFIG=1` 與 safe read-only artifact 路徑；QA sandbox DNS 失敗時可核對 Architect sanitized production-read evidence。
- 驗證：
  - QA 結論：`通過`。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py services/strategy_evidence.py`：passed。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_strategy_evidence.py tests/test_market_theme_evidence.py tests/test_notifier.py tests/test_cross_day_context.py tests/test_analysis_engine.py`：167 passed，165 warnings（第三方 deprecation 類）。
  - `git diff --check`：passed。
  - QA 補充反證：完整 message list 順序、2356 stale second-stage guard、噪音壓縮、production artifact schema/content 均 passed。
  - scoped 可吸收 diff：`core/generator.py`、`tests/test_generator_report.py`、`tests/test_market_theme_evidence.py`、`CHANGELOG.md`、`QA_REPORT.md`；其他既存 dirty files 不得用本輪結論整包吸收。

## Next Action

- 本輪已推送完成；下一輪若有 repo 落地變更，收口必跑 `tools/cao_agent/check_git_completion_gate.sh`。
- 旁支另開：Telegram reply markup 仍附在最後一則 message，message order 改為 summary first 後可能需要 delivery consumer 任務評估按鈕落點。
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
