# DISPATCH.md

## Active

- task_md_holds: `future_fundamentals_and_unheld_status_20260608`
- status: `qa_passed`
- owner_request:
  1. EPS / revenue must appear for every watched stock, not only stocks with upcoming MOPS meetings.
  2. Scan and fix remaining visible conflicts.
  3. Replace weird `未持倉漏斗（非執行）` wording.

## Current Result

- Version implemented: `v20.4.51`.
- Future watch:
  - `未來30日法說會` remains event-only.
  - New `關注標的財報` section lists EPS / revenue YoY for watch/holding targets.
- Summary:
  - first line now shows `未持倉 7（全部不可行動）`.
  - detail now shows `未持倉狀態：未持倉 7 檔全部不可行動`.
  - no `未持倉漏斗（非執行）` wording.
- No live Telegram delivery was run.

## Verification

- `py_compile` passed.
- focused pytest + market theme tests passed: 44 passed.
- official `generate_report(dry_run=True)` passed with 4 local preview messages.

## Fixed Commands

Local dry-run only, no live Telegram:

```powershell
cd D:\reserch\stock-bot
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages, _ = generate_report(dry_run=True); print('\n\n--- MESSAGE ---\n\n'.join(messages))"
```
