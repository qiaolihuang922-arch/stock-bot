# DISPATCH.md

新對話先讀 `AGENTS.md`、本文件、`CURRENT_STATE.md`。本文件只保留接力必需資訊。

## Current Task

- task_id: `telegram-evidence-entry-dedupe-v20.4.14`
- task_name: `Telegram Evidence Entry Dedupe`
- task_type: `tiny_patch`
- owner_status: `rejected_v20_4_13_duplicate_evidence_entries`
- architect_status: `qa_passed_pending_git_close`
- pm_status: `done`
- tech_status: `done`
- qa_status: `passed`
- latest_commit: see `git log -1`

## Current Result

- 本輪已完成 QA，收口時必須 commit / push 到 `origin/main`。
- Git completion gate：final 前必須以 `tools/cao_agent/check_git_completion_gate.sh` 驗證 `main` matches `origin/main` 且 worktree clean。
- 已吸收 PM -> Tech -> QA 交付到主 repo 工作樹：
  - 報文版本升至 `v20.4.14`。
  - TG message list 順序維持：messages[0] 持倉、messages[1] 未持倉 / 非持倉、messages[2] short/evidence；`include_detail=True` 時 Details Backup 仍追加在最後。
  - 第三則只保留一個 evidence entry：`v20.4.14 簡短證據摘要`。
  - 第三則會跳過 legacy `📊 策略證據 v20.0` 長段，避免與簡短證據摘要同時出現。
  - 策略樣本 `missing-source / insufficient-data` 仍在唯一摘要內 fail closed；不把 unavailable 樣本包裝成可買或推薦。
  - 不改策略 decision、持倉/未持倉判斷、DB schema、write path、live Telegram。
- 驗證：
  - QA 結論：`通過`。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py services/notifier.py`：passed。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_notifier.py`：119 passed，169 warnings（第三方 deprecation 類）。
  - `git diff --check`：passed。
  - QA 補充反證：注入 legacy `📊 策略證據 v20.0 ... 狀態碼：missing-source`，第三則 `簡短證據摘要` count = 1，legacy heading count = 0，且仍含 `missing-source` 與 `fail-closed`。
  - scoped 可吸收 diff：`TASK.md`、`CHANGELOG.md`、`QA_REPORT.md`、`core/generator.py`、`tests/test_generator_report.py`、`tests/test_market_theme_evidence.py`。

## Next Action

- 若 `git status --branch --short` 顯示未推送或 dirty，先完成 commit / push 並跑 `tools/cao_agent/check_git_completion_gate.sh`，不得開新產品任務。
- 下一張產品任務：Owner 進一步指出第三則整體仍像多段拼接；應整理成單一「簡報 + 資料依據」結構，讓 market/theme、strategy sample、持倉 / 候選 source 在同一處用資料庫狀態說清楚，而不是分散成多個片段。
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
