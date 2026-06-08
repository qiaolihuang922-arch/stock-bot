# DISPATCH.md

請依 `AGENTS.md` 啟動順序閱讀；本文件只保留當前看板、高信號結果與固定入口。

- task_md_holds: `recently_done`
- task_md_task_id: `today_buy_all_risk_summary_wording_20260608`
- task_md_note: `TASK.md / CHANGELOG.md / QA_REPORT.md 保存本輪今日買入全部轉風控 Summary wording 修復；已 commit/push 到 origin/main，已用 dry-run artifact 反證，未 live Telegram delivery。`

## Active

- none

## Queued

- none

## Recently Done

- `today_buy_all_risk_summary_wording_20260608`（normal_patch/L2）：修正 2026-06-08 盤後 Summary 語意衝突。Owner 標本中市場行已寫 `今日已買 5（已風控 5）`，但結論與明細仍寫 `今日交易已建立新倉 5 檔`。現在全部今日買入已停損 / 減碼 / 硬風控時，結論改為 `今日已買 N 檔，已全部轉入風控/停損減碼`，明細改為 `今日買入後風控：N 檔（...）`。純新倉風控觀察路徑保留既有 `已建立新倉` 語意。驗證：focused `tests/test_generator_report.py` 4 passed + 3 subtests passed；`py_compile` passed；official `generate_report(dry_run=True)` Summary 顯示 `今日已買 5 檔，已全部轉入風控/停損減碼` 與 `今日買入後風控：5 檔（英業達、智原、建準、聯電、旺宏）`。未 live Telegram delivery。
- `github_actions_scheduled_bot_delivery_restore_20260608`（normal_patch/L2）：修復 GitHub scheduled TG bot 被導到 `daily_evidence` 導致不推送；已 commit/push 到 `origin/main`，bot schedule 改為 `10 6 * * 1-5`，daily evidence 保留 `0 6 * * 1-5`。未 live Telegram delivery。

## Blocked / Deferred

- CAO agent runner：本機仍缺 `cao` / `cao-server` binary，正式 PM/Tech/QA runner 不能啟動；本輪用手動等價 handoff docs + tests 收口。
- future-watch source hardening：MOPS / TWSE / global live readonly source 仍有後續 hardening 項，另開任務。
- production source follow-up：若 Owner 要追查某檔跨日持倉記憶，需用 safe read-only artifact，不得手寫 production DML。

## Next Action

- 本輪報文 wording 修復已 commit / push 到 `origin/main`；下一步只需 Owner 本地 dry-run 或等待 GitHub scheduled bot 自然執行，不得未批准 live Telegram delivery。
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
