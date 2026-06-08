# DISPATCH.md

## Active

- task_md_holds: `historical_analogy_granularity_20260608`
- status: `qa_passed`
- owner_request:
  - Strengthen historical analogy granularity after the previous report cleanup.

## Current Result

- Version implemented: `v20.4.52`.
- Historical analogy now shows:
  - most similar event / similarity / pattern / pressure level.
  - `相似點`.
  - `不相似/限制`.
  - `下一步觀察`.
  - `資料`.
- No live Telegram delivery was run.

## Verification

- `py_compile` passed.
- focused pytest passed: 7 passed; market theme tests passed: 38 passed.
- official `generate_report(dry_run=True)` passed with 4 local preview messages.

## Fixed Commands

Local dry-run only, no live Telegram:

```powershell
cd D:\reserch\stock-bot
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages, _ = generate_report(dry_run=True); print('\n\n--- MESSAGE ---\n\n'.join(messages))"
```
