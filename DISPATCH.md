# DISPATCH.md

新對話先讀 `AGENTS.md`、本文件、`CURRENT_STATE.md`。本文件只保留接力必需資訊。

## Current Task

- task_id: `telegram-evidence-human-readable-v20-4-20`
- task_name: `Telegram evidence readable and conflict-consistent`
- task_type: `normal_patch`
- owner_status: `requested_reasonableness_and_conflict_fix`
- architect_status: `qa_passed_pending_git_close`
- pm_status: `done`
- tech_status: `done`
- qa_status: `passed`
- latest_commit: see `git log -1`

## Current Result

- 本輪已完成 QA，收口時必須 commit / push 到 `origin/main`。
- Git completion gate：final 前必須以 `tools/cao_agent/check_git_completion_gate.sh` 驗證 `main` matches `origin/main` 且 worktree clean。
- 已吸收 PM -> Tech -> QA 交付到主 repo 工作樹：
  - 報文版本升至 `v20.4.20`。
  - TG message list 順序維持：messages[0] 持倉、messages[1] 未持倉 / 非持倉、messages[2] short/evidence；`include_detail=True` 時 Details Backup 仍追加在最後。
  - 第三則改為人話 `簡報＋資料依據`，不再顯示 `source:/status:/use:/limit:/conflict:` raw slot dump。
  - 內部 evidence_manifest / maturity artifact / gate 保留 machine-readable 欄位與 maturity 100。
  - `🔥 最強` 只允許有效進場標的；新倉無有效進場或候選只是追蹤/不可行動時，顯示 `無有效進場標的`，不顯示排序/評級。
  - 持倉非加碼卡片顯示 `新倉 RR：不適用（既有持倉）`，不顯示新倉 RR 數字。
  - strategy sample 不可用時，卡片顯示不可用/不納入判斷，不顯示樣本、勝率、相對報酬等回測數字。
  - 不改策略 decision、DB schema、write path、live Telegram。
- 驗證：
  - QA 結論：`通過`。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py scripts/generate_structural_evidence_artifact.py`：passed。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py`：124 passed，177 warnings（第三方 deprecation 類）。
  - `scripts/generate_structural_evidence_artifact.py --maturity-report --case production_all_sources_available` + `tools/cao_agent/check_evidence_handoff_gate.sh`：passed，maturity_score=100。
  - `git diff --check`：passed。
  - QA 補充反證：WAIT / HOT blocker 候選即使傳入 best/score，也不會在無有效進場摘要顯示推薦感最強；ledger conflict 仍以人話揭露差異且內部 slot 保留。
  - scoped 可吸收 diff：`TASK.md`、`CHANGELOG.md`、`QA_REPORT.md`、`core/generator.py`、`tools/cao_agent/check_evidence_handoff_gate.sh`、`tests/test_generator_report.py`、`tests/test_market_theme_evidence.py`。

## Next Action

- 若 `git status --branch --short` 顯示未推送或 dirty，先完成 commit / push 並跑 `tools/cao_agent/check_git_completion_gate.sh`，不得開新產品任務。
- 收口：commit / push 後跑 `tools/cao_agent/check_git_completion_gate.sh`。
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
