# DISPATCH.md

## Active

- task_md_holds: `trade_state_machine_v21_completion_20260608`
- status: `QA passed, pending git completion`
- owner_request:
  - Finish the next round and implement a complete v21 effect.
  - Use dry-run/report output, not live Telegram delivery.

## Current Result

- Version: `v21.0`.
- Full generator/state-machine regression passes: `193 passed, 145 warnings, 44 subtests passed`.
- Official dry-run generated v21.0 messages; no live Telegram delivery.
- Holding cards show trade state/action/trigger and stronger today-buy wording.
- Unheld cards now show wait states instead of only reject/eliminate.
- Blocker attribution is fixed: volume/market/RR/pullback blockers are primary when visible; source gaps stay in decision evidence.
- State machine remains read-only: no DB write, no schema change.

## Verification

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py tests/test_trade_state_machine.py -q --tb=short
```

Result: `193 passed, 145 warnings, 44 subtests passed`.

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages, _ = generate_report(dry_run=True); print('\\n\\n--- MESSAGE ---\\n\\n'.join(messages))"
```

Result: v21.0 dry-run message list generated; no live Telegram delivery.

## Fixed Commands

Local dry-run only:

```powershell
cd D:\reserch\stock-bot
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages, _ = generate_report(dry_run=True); print('\\n\\n--- MESSAGE ---\\n\\n'.join(messages))"
```

## Next Action

- Commit and push this completion patch, then run git completion gate.
