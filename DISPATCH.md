# DISPATCH.md

新對話先讀 `AGENTS.md`、本文件、`CURRENT_STATE.md`。本文件只保留接力必需資訊。

## Current Task

- task_id: `pm-20260601-telegram-helper-split`
- task_name: `Pure Telegram Formatter Helpers Presentation Split`
- task_type: `normal_patch`
- owner_status: `requested_continue_split_and_complete_logic_tests`
- architect_status: `qa_passed_pending_git_close`
- pm_status: `done`
- tech_status: `manual_absorb_from_tech_worktree`
- qa_status: `passed`
- latest_commit: see `git log -1`

## Current Result

- 本輪目標是繼續明確拆分：把純 Telegram formatter helper 從 `core/generator.py` 移到既有 `presentation/report.py`，不新增業務模組或架構文檔。
- Git completion gate：final 前必須以 `tools/cao_agent/check_git_completion_gate.sh` 驗證 `main` matches `origin/main` 且 worktree clean。
- 已吸收內容：
  - `presentation/report.py` 承接 `formatTelegramSummary`、`formatTelegramPositionCard`、`formatTelegramUnheldCard`、`format_brief_data_evidence_message` 與 brief evidence 顯示 helper。
  - `core/generator.py` 保留 public wrapper 與 orchestration，透過 `_telegram_presentation_deps()` 注入既有 helper。
  - `presentation/report.py` 沒有 import；不直接 mutate `result/results_map/holding_decision` roots。
  - Telegram 文案、message order、VERSION、strategy decision、RR、holding_status、DB write path 無變更。
- 驗證：
  - QA 結論：`通過`。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py presentation/report.py presentation/__init__.py tests/test_generator_report.py`：passed。
  - 完整邏輯矩陣：187 passed，177 warnings。
  - 追加旁路：`tests/test_daily_snapshot_store.py tests/test_dry_run_replay.py`：12 passed，13 warnings。
  - Re-QA runner：通過；追加手機順序 smoke confirmed。
  - `git diff --check`：passed。
  - scoped diff：`core/generator.py`、`presentation/report.py`、固定 handoff Markdown。

## Next Action

- 收口：commit / push 後跑 `tools/cao_agent/check_git_completion_gate.sh`。
- 下一刀拆分：只搬 remaining pure display helper；不可把策略、DB、ledger、holding status 帶進 presentation。
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
