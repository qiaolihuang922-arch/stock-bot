# DISPATCH.md

新對話先讀 `AGENTS.md`、本文件、`CURRENT_STATE.md`。本文件只保留接力必需資訊。

## Current Task

- task_id: `evidence-chain-maturity-100`
- task_name: `Evidence Chain Maturity 100`
- task_type: `risk_patch`
- owner_status: `requested_maturity_72_to_100`
- architect_status: `qa_passed_pending_git_close`
- pm_status: `done`
- tech_status: `done`
- qa_status: `passed`
- latest_commit: see `git log -1`

## Current Result

- 本輪已完成 QA，收口時必須 commit / push 到 `origin/main`。
- Git completion gate：final 前必須以 `tools/cao_agent/check_git_completion_gate.sh` 驗證 `main` matches `origin/main` 且 worktree clean。
- 已吸收 PM -> Tech -> QA 交付到主 repo 工作樹：
  - 報文版本升至 `v20.4.19`。
  - TG message list 順序維持：messages[0] 持倉、messages[1] 未持倉 / 非持倉、messages[2] short/evidence；`include_detail=True` 時 Details Backup 仍追加在最後。
  - 五維 evidence maturity 達 100：data source / anti-fake、Telegram evidence expression、strategy sample evidence、execution memory / ledger evidence、repeatable runner / process。
  - `scripts/generate_structural_evidence_artifact.py --maturity-report --case production_all_sources_available` 產生標準 maturity report；五維 100 且 blocking_findings=[]。
  - strategy sample / ledger production-readonly artifact 均含 source artifact path/hash proof；synthetic-only、stale runner、缺 source hash、偽造 minimal 100 artifact 均 fail closed。
  - `tools/cao_agent/check_evidence_handoff_gate.sh` 檢查五維、三則 messages、artifacts、source hash、safety flags、repo/worktree binding。
  - 不改資料合理度、不修 production ledger conflict、不改策略 decision、DB schema、write path、live Telegram。
- 驗證：
  - QA 結論：`通過`。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py scripts/generate_structural_evidence_artifact.py`：passed。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py`：121 passed，169 warnings（第三方 deprecation 類）。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_strategy_evidence.py tests/test_position_store.py tests/test_cross_day_context.py`：21 passed，12 warnings。
  - `git diff --check`：passed。
  - QA 補充反證：synthetic-only exit 2、stale runner exit 2、forged minimal 100 被 gate 擋下、移除 source hash 被 gate 擋下、舊 repo/worktree binding 被 gate 擋下。
  - scoped 可吸收 diff：`TASK.md`、`CHANGELOG.md`、`QA_REPORT.md`、`core/generator.py`、`scripts/generate_structural_evidence_artifact.py`、`tools/cao_agent/check_evidence_handoff_gate.sh`、`tests/test_generator_report.py`、`tests/test_market_theme_evidence.py`。

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
