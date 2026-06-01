# DISPATCH.md

新對話先讀 `AGENTS.md`、本文件、`CURRENT_STATE.md`。本文件只保留接力必需資訊。

## Current Task

- task_id: `pm-20260601-presentation-report-split`
- task_name: `Presentation Report Split First Cut`
- task_type: `normal_patch`
- owner_status: `requested_strategy_presentation_split`
- architect_status: `qa_conditional_pass_pending_git_close`
- pm_status: `done`
- tech_status: `done`
- qa_status: `conditional pass`
- latest_commit: see `git log -1`

## Current Result

- 本輪 QA conditional pass，條件是 `presentation/__init__.py` 與 `presentation/report.py` 必須明確納入 commit；收口時必須 commit / push 到 `origin/main`。
- Git completion gate：final 前必須以 `tools/cao_agent/check_git_completion_gate.sh` 驗證 `main` matches `origin/main` 且 worktree clean。
- 已吸收 PM -> Tech -> QA 交付到主 repo 工作樹：
  - 報文版本升至 `v20.4.21`。
  - TG message list 順序維持：messages[0] 持倉、messages[1] 未持倉 / 非持倉、messages[2] short/evidence；`include_detail=True` 時 Details Backup 仍追加在最後。
  - 第一刀拆分：新增 `presentation/report.py`，承接 Telegram message assembly。
  - `core/generator.py` 保留 `formatTelegramMessages(...)` public wrapper，透過 deps 呼叫 `presentation.report.render_telegram_messages(...)`。
  - Side-effect gate：presentation module 不 import / call `record_daily_signals`、`record_strategy_evidence`、`get_supabase_client`、`record_daily_snapshots`，不直接 mutate `results_map/result/holding_decision` roots。
  - 不改策略 decision、RR、holding_status、DB schema、write path、live Telegram。
- 驗證：
  - QA 結論：`conditional pass`，條件為新 presentation files 必須 stage/commit；Architect 收口時必須確認。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py presentation/report.py presentation/__init__.py tests/test_generator_report.py`：passed。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py`：125 passed，177 warnings（第三方 deprecation 類）。
  - `scripts/generate_structural_evidence_artifact.py --maturity-report --case production_all_sources_available` + `tools/cao_agent/check_evidence_handoff_gate.sh`：passed，maturity_score=100。
  - `git diff --check`：passed。
  - QA 補充反證：直接 consumer smoke 確認 messages[0] 持倉、messages[1] 未持倉、messages[2] 簡報＋資料依據，Details Backup 只在 include_detail=True 時追加最後。
  - scoped 可吸收 diff：`TASK.md`、`CHANGELOG.md`、`QA_REPORT.md`、`core/generator.py`、`presentation/__init__.py`、`presentation/report.py`、`tools/cao_agent/check_evidence_handoff_gate.sh`、`tests/test_generator_report.py`、`tests/test_market_theme_evidence.py`。

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
