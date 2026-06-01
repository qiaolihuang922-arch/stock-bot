# DISPATCH.md

新對話先讀 `AGENTS.md`、本文件、`CURRENT_STATE.md`。本文件只保留接力必需資訊。

## Current Task

- task_id: `evidence-chain-structural-coverage-100`
- task_name: `Structural Evidence Coverage 100`
- task_type: `risk_patch`
- owner_status: `requested_structural_coverage_100_before_reasonableness`
- architect_status: `qa_passed_pending_git_close`
- pm_status: `done`
- tech_status: `done`
- qa_status: `passed`
- latest_commit: see `git log -1`

## Current Result

- 本輪已完成 QA，收口時必須 commit / push 到 `origin/main`。
- Git completion gate：final 前必須以 `tools/cao_agent/check_git_completion_gate.sh` 驗證 `main` matches `origin/main` 且 worktree clean。
- 已吸收 PM -> Tech -> QA 交付到主 repo 工作樹：
  - 報文版本升至 `v20.4.18`。
  - TG message list 順序維持：messages[0] 持倉、messages[1] 未持倉 / 非持倉、messages[2] short/evidence；`include_detail=True` 時 Details Backup 仍追加在最後。
  - structural evidence coverage 達 100%：每個必要層都有 `layer / target / source / status / use / limit / conflict / visible_refs` slot。
  - 必要層包含 market-theme、strategy-sample、positions、ledger、price-ohlcv、rr-score-volume、funnel-classification、execution-plan、next-day-plan、missing-data、conflict。
  - 新增 read-only artifact CLI：`scripts/generate_structural_evidence_artifact.py --case <case>`，支援 `all_sources_available`、`missing_strategy_sample_source`、`ledger_position_conflict`。
  - Verifier 覆蓋率 100% 時仍會保留 missing-source / unresolved-conflict 狀態；若 blocking source status 下出現 `可買 / 通過 / 有效進場`，verifier 會 fail。
  - 不改資料合理度、不修 production ledger conflict、不改策略 decision、DB schema、write path、live Telegram。
- 驗證：
  - QA 結論：`通過`。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py scripts/generate_structural_evidence_artifact.py`：passed。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py`：119 passed，169 warnings（第三方 deprecation 類）。
  - `git diff --check`：passed。
  - 三個 artifact case：coverage_pct=100.0、coverage_percent=100.0、missing_slots=[]、fail_closed_violations=[]。
  - QA 補充反證：在 missing-source artifact 注入 `通過 / 有效進場` 後 verifier 回傳 pass=false 且 fail_closed_violations 非空。
  - scoped 可吸收 diff：`TASK.md`、`CHANGELOG.md`、`QA_REPORT.md`、`core/generator.py`、`tests/test_generator_report.py`、`tests/test_market_theme_evidence.py`、`scripts/generate_structural_evidence_artifact.py`。

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
