# DISPATCH.md

## Active

- task_md_holds: `report_conflict_future_watch_format_20260608`
- status: `qa_passed`
- owner_request:
  1. Analyze and fix visible report conflicts in the v20.4.49 dry-run sample.
  2. Keep future-30-day MOPS meeting filtering, but split EPS / revenue into a per-meeting child line.

## Current Result

- Version target implemented: `v20.4.50`.
- Summary conflict fixed:
  - `今日已買` -> `今日買入紀錄`.
  - `新增有效進場：無` remains the strategy-new-entry conclusion.
- Unheld card conflict fixed:
  - title blocker and `卡關主因` now align.
  - source/sample gaps no longer override visible trading blocker.
- Future watch format fixed:
  - meeting main line keeps date/code/name/event/reason.
  - EPS / revenue appears as indented `財報：...` line under that meeting.
- No live Telegram delivery was run.

## Verification

- `py_compile` passed.
- focused pytest passed.
- official `generate_report(dry_run=True)` passed with 4 local preview messages.

## Fixed Commands

Local dry-run only, no live Telegram:

```powershell
cd D:\reserch\stock-bot
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages, _ = generate_report(dry_run=True); print('\n\n--- MESSAGE ---\n\n'.join(messages))"
```
