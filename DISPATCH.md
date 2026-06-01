# DISPATCH.md

新對話先讀 `AGENTS.md`、本文件、`CURRENT_STATE.md`。本文件只保留接力必需資訊。

## Current Task

- task_id: `tg-message-order-v20.4.12`
- task_name: `Telegram Message Order: Holdings / Unheld / Short Report`
- task_type: `tiny_patch`
- owner_status: `rejected_v20_4_11_summary_first_tg_order`
- architect_status: `absorbed_agent_diff_and_reviewed`
- pm_status: `done`
- tech_status: `done`
- qa_status: `passed`
- latest_commit: see `git log -1`

## Current Result

- 本輪已完成 QA，收口時必須 commit / push 到 `origin/main`。
- Git completion gate：final 前必須以 `tools/cao_agent/check_git_completion_gate.sh` 驗證 `main` matches `origin/main` 且 worktree clean。
- 已吸收 PM -> Tech -> QA 交付到主 repo 工作樹：
  - 報文版本升至 `v20.4.12`。
  - `formatTelegramMessages()` 固定 TG message list：messages[0] 持倉、messages[1] 未持倉 / 非持倉、messages[2] summary + Evidence Compact；`include_detail=True` 時 Details Backup 仍追加在最後。
  - 持倉與未持倉 message 都加上 v20.4.12 header，符合 Owner 指定手機順序：`1.持仓 2.非持仓 3.报文短讯`。
  - 不改策略 decision、持倉/未持倉判斷、DB schema、write path、live Telegram。
- Runner gap 已修：
  - `tools/cao_agent/run_qa_code.sh` 會在 QA 啟動前同步主 repo handoff files 到可重用 tech worktree，避免 QA 驗到 stale `TASK.md / CHANGELOG.md / QA_REPORT.md`。
  - 保留既有 `CAO_QA_USE_REPO_CONFIG=1` 與 safe read-only artifact 路徑；QA sandbox DNS 失敗時可核對 Architect sanitized production-read evidence。
- 驗證：
  - QA 結論：`通過`。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py services/notifier.py`：passed。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_notifier.py`：118 passed，165 warnings（第三方 deprecation 類）。
  - `git diff --check`：passed。
  - QA 補充反證：`services/notifier.py` / mock `send_many()` 確認 sender 依 list order 逐則送出，不會把 summary 排回第一則。
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
