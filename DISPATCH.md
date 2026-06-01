# DISPATCH.md

新對話先讀 `AGENTS.md`、本文件、`CURRENT_STATE.md`。本文件只保留接力必需資訊。

## Current Task

- task_id: `pm-20260601-afterhours-telegram-brief-dedupe`
- task_name: `Afterhours Telegram Brief Dedup And Noise Reduction`
- task_type: `normal_patch`
- owner_status: `requested_optimize_and_review_process`
- architect_status: `qa_passed_pending_git_close`
- pm_status: `done`
- tech_status: `manual_absorb_from_tech_worktree`
- qa_status: `passed`
- latest_commit: see `git log -1`

## Current Result

- 本輪目標是修 v20.4.21 盤後 Telegram 可讀性：第三則摘要化、策略樣本狀態單一化、卡片去除逐檔策略樣本不可用噪音、盤後語境正確、非加碼持倉 RR 不誤導。
- Git completion gate：final 前必須以 `tools/cao_agent/check_git_completion_gate.sh` 驗證 `main` matches `origin/main` 且 worktree clean。
- 已吸收內容：
  - `presentation/report.py` 盤後第三則改為 `📌 盤後簡報`，不再複製完整 summary / 交易細節。
  - 策略樣本不可用只在盤後第三則集中顯示一次，原因單一化。
  - 盤後卡片不再逐檔重複策略樣本不可用，並替換盤中語境詞。
  - 非加碼持倉仍顯示 `新倉 RR：不適用（既有持倉）`，新倉候選 RR 保留。
  - VERSION 仍為 `v20.4.21`；strategy decision、holding_status、DB write path 無變更。
- 驗證：
  - QA 結論：`通過`。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py`：passed。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py`：92 passed，181 warnings。
  - QA independent source-error fixture：all checks true。
  - `git diff --check`：passed。
  - scoped diff：`core/generator.py`、`presentation/report.py`、`tests/test_generator_report.py`、固定 handoff Markdown。

## Next Action

- 收口：commit / push 後跑 `tools/cao_agent/check_git_completion_gate.sh`。
- 後續同類報文任務：先補或更新手機閱讀 probe，再改 formatter；不要只寫規則。
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
