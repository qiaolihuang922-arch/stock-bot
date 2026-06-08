# DISPATCH.md

## Active

- task_md_holds: `unheld_trade_fsm_contract_20260608`
- status: `QA passed, pending git completion`
- owner_request:
  - Start with unheld stocks first.
  - Do not depend on buy-time/order timing yet.
  - No live Telegram delivery.

## Current Result

- Version remains `v21.0`.
- Unheld FSM now has formal metadata: `phase`, `is_actionable`, `is_terminal`, `transition_event`, `next_required_event`, `guards`, `blocked_by`, `requires_order_lifecycle`.
- Existing visible report remains stable.
- Buyable/ready unheld candidates with source errors fail closed before any order lifecycle.
- State machine remains read-only: no DB write, no schema change.

## Verification

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -m pytest tests/test_trade_state_machine.py -q --tb=short
```

Result: `5 passed, 3 warnings`.

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py tests/test_trade_state_machine.py -q --tb=short
```

Result: `194 passed, 145 warnings, 44 subtests passed`.

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

- Commit and push this unheld FSM contract patch, then run git completion gate.
