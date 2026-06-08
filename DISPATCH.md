# DISPATCH.md

## 2026-06-08 Update

- task_md_holds: `telegram_mobile_first_preface_20260608`
- status: `QA conditional pass, committed/pushed`
- result: Telegram official dry-run now starts message 1 with `【先看結論】`, so mobile first screen shows `新倉：無有效進場`, today buys moved to risk control, holding risk priority, and that unheld cards are not a buy list.
- version: `v20.4.48`
- evidence: focused pytest 5 passed; py_compile passed; `generate_report(dry_run=True)` produced 4 messages with the new first-read preface.
- not done: no live Telegram delivery; full historical `tests/test_generator_report.py tests/test_notifier.py` remains 160 passed / 34 failed and is not claimed as fixed.

## Next Action

- Monitor next dry-run / runner artifact only; no live Telegram delivery unless Owner separately approves.

請依 `AGENTS.md` 啟動順序閱讀；本文件只保留當前看板、高信號結果與固定入口。

- task_md_holds: `recently_done`
- task_md_task_id: `today_buy_all_risk_summary_wording_20260608`
- task_md_note: `TASK.md / CHANGELOG.md / QA_REPORT.md 保存最近一輪報文修復；CAO Windows/WSL 部署已補齊並另有 runner patch，未 live Telegram delivery。`

## Active

- none

## Queued

- none

## Recently Done

- `today_buy_all_risk_summary_wording_20260608`（normal_patch/L2）：修正 2026-06-08 盤後 Summary 語意衝突。Owner 標本中市場行已寫 `今日已買 5（已風控 5）`，但結論與明細仍寫 `今日交易已建立新倉 5 檔`。現在全部今日買入已停損 / 減碼 / 硬風控時，結論改為 `今日已買 N 檔，已全部轉入風控/停損減碼`，明細改為 `今日買入後風控：N 檔（...）`。純新倉風控觀察路徑保留既有 `已建立新倉` 語意。驗證：focused `tests/test_generator_report.py` 4 passed + 3 subtests passed；`py_compile` passed；official `generate_report(dry_run=True)` Summary 顯示 `今日已買 5 檔，已全部轉入風控/停損減碼` 與 `今日買入後風控：5 檔（英業達、智原、建準、聯電、旺宏）`。未 live Telegram delivery。
- `github_actions_scheduled_bot_delivery_restore_20260608`（normal_patch/L2）：修復 GitHub scheduled TG bot 被導到 `daily_evidence` 導致不推送；已 commit/push 到 `origin/main`，bot schedule 改為 `10 6 * * 1-5`，daily evidence 保留 `0 6 * * 1-5`。未 live Telegram delivery。
- `cao_wsl_deployment_repair_20260608`（process/runner）：依 `tools/cao_agent/DEPLOYMENT.md` 補齊 Windows 本機 CAO runner。已安裝 WSL Ubuntu、Linux `uv`、CAO CLI/server/MCP、Linux node/npm/tmux、CAO web UI、agent profiles、agent worktree；CAO API `http://127.0.0.1:9889/` 與 UI `http://127.0.0.1:5173/` 已可連。repo patch：CAO shell scripts 固定 LF；`ensure_cao_services.sh` 移除 macOS-only `arch -arm64 npm`；`tools/cao_agent/bin/codex` 在 Linux/WSL 無 `sandbox-exec` 時直接執行 `CODEX_APP_BIN`。WSL Codex binary 位於 `/root/.local/bin/codex-real`，由 Windows app `resources/codex` 複製。未 live Telegram delivery。

## Blocked / Deferred

- CAO agent runner：服務與 profiles 已補齊；若下輪要正式跑 PM/Tech/QA，請從 WSL 執行並設定 `CODEX_APP_BIN=/root/.local/bin/codex-real`。
- future-watch source hardening：MOPS / TWSE / global live readonly source 仍有後續 hardening 項，另開任務。
- production source follow-up：若 Owner 要追查某檔跨日持倉記憶，需用 safe read-only artifact，不得手寫 production DML。

## Next Action

- CAO deployment patch 已 commit / push；WSL CAO services 可用，但 TUI automation 仍需另修 runner prompt/send gap。
- 若 Owner 要本地再看報表，可執行：

```powershell
cd D:\reserch\stock-bot
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages, _ = generate_report(dry_run=True); print('\n\n--- MESSAGE ---\n\n'.join(messages))"
```

## Fixed Commands

Owner 對 Architect：

```text
請用 Architect / 照流程；先讀 AGENTS.md、DISPATCH.md、CURRENT_STATE.md；產品 / 報文 / 策略 bug 走 PM -> Tech -> QA，不得 live Telegram delivery，除非我單獨批准。
```

Architect 入口：

```text
tools/cao_agent/run_architect_task.sh research "<研究問題>"
tools/cao_agent/run_architect_task.sh plan "<技術規劃問題>"
tools/cao_agent/run_architect_task.sh auto "<Owner 任務>"
```
