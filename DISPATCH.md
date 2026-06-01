# DISPATCH.md

新對話先讀 `AGENTS.md`、本文件、`CURRENT_STATE.md`。本文件只保留接力必需資訊。

## Current Task

- task_id: `import-boundary-gate-20260601`
- task_name: `Strategy Presentation Import Boundary Gate`
- task_type: `process`
- owner_status: `requested_layer_map_without_new_files`
- architect_status: `qa_passed_pending_git_close`
- pm_status: `done`
- tech_status: `manual_absorb_from_rejected_runner`
- qa_status: `passed`
- latest_commit: see `git log -1`

## Current Result

- 本輪目標是防止後續拆分靠記憶：不新增業務模組、不新增架構文檔，只在既有測試檔加入可重跑 import boundary gate，並在固定文件寫高信號分層地圖。
- Git completion gate：final 前必須以 `tools/cao_agent/check_git_completion_gate.sh` 驗證 `main` matches `origin/main` 且 worktree clean。
- 已吸收內容：
  - `tests/test_generator_report.py` 新增 AST import gate。
  - Gate 掃描 `presentation/`、`services/`、`core/`、`main.py`、`app.py`。
  - 禁止 `presentation` import DB writer / signal writer / strategy evidence writer。
  - 禁止 `services/` 與 `core/` import `presentation`。
  - 唯一 transitional allowlist：`core/generator.py -> presentation.report`。
  - Fake import fixture 反證 gate 會輸出 offending rule/file/import。
  - Telegram / VERSION / DB write path 無變更。
- 驗證：
  - QA 結論：`通過`。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m py_compile tests/test_generator_report.py`：passed。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py`：91 passed，177 warnings。
  - `git diff --check`：passed。
  - scoped diff：`TASK.md`、`CHANGELOG.md`、`QA_REPORT.md`、`DISPATCH.md`、`CURRENT_STATE.md`、`CLEANUP_PLAN.md`、`tests/test_generator_report.py`。

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
