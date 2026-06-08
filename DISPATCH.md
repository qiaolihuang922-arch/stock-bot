# DISPATCH.md

## Active

- task_md_holds: `historical_analogy_library_modules_20260608`
- status: `qa_passed`
- owner_request:
  - Expand Taiwan historical crash / stress-event coverage and make analogy modules more precise.
  - Verify 3231/2337 revenue growth and rename visible `營收YoY` label to `營收`.

## Current Result

- Version implemented: `v20.4.54`.
- Historical analogy now shows:
  - most similar event / similarity / pattern / pressure level.
  - `相似點`.
  - `模組分數`.
  - `不相似/限制`.
  - `下一步觀察`.
  - `資料`.
- Taiwan historical stress-event library expanded from 13 to 19 entries.
- Watched-stock fundamentals now render revenue as `營收`; `營收YoY` is hidden from user-visible messages.
- TWSE official monthly revenue check: 3231 revenue YoY `111.98927364274991`; 2337 revenue YoY `153.71283899759698`.
- No live Telegram delivery was run.

## Verification

- `py_compile` passed.
- focused pytest passed: 8 passed; market theme tests passed: 38 passed.
- official `generate_report(dry_run=True)` passed with 4 local preview messages.

## Fixed Commands

Local dry-run only, no live Telegram:

```powershell
cd D:\reserch\stock-bot
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages, _ = generate_report(dry_run=True); print('\n\n--- MESSAGE ---\n\n'.join(messages))"
```
