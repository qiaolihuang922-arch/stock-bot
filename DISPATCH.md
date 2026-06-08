# DISPATCH.md

## Active

- task_md_holds: `unheld_transition_table_replay_20260608`
- status: `complete`
- owner_request:
  - Start with unheld stocks first.
  - Do not depend on buy-time/order timing yet.
  - Do not only add fields; use real transition logic and run it several times before Owner review.
  - No live Telegram delivery.

## Current Result

- Version remains `v21.0`.
- Unheld FSM now uses an explicit transition table.
- Local replay covers `WAIT_VOLUME -> READY -> BUYABLE`, plus source-error, RR, and pullback repair routes.
- Waiting unheld cards no longer show the conflicting internal source-warning line.
- Official dry-run report remains readable and shows no valid new entry.
- State machine remains read-only: no DB write, no schema change.
- Git completion gate passed on `main` at `c0e210c` before closeout doc refresh.

## Recently Done

- `unheld_transition_table_replay_20260608`: v21.0 unheld transition-table FSM implemented, replayed locally, regression-tested, dry-run verified, no live Telegram delivery.

## Verification

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py tests/test_trade_state_machine.py -q --tb=short
```

Result: `196 passed, 145 warnings, 44 subtests passed`.

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages, _ = generate_report(dry_run=True); print('\\n--- MESSAGE ---\\n'.join(messages))"
```

Result: v21.0 dry-run message list generated; no live Telegram delivery.

Local transition replay:

- `volume_missing_label`: `UNKNOWN -> WAIT_VOLUME`.
- `volume_to_ready`: `WAIT_VOLUME -> READY`.
- `ready_to_buyable`: `READY -> BUYABLE`.
- `ready_source_error`: `READY -> WAIT_DATA`.
- `rr_repair_needed`: `WATCH -> WAIT_RR`.
- `pullback_needed`: `WATCH -> WAIT_PULLBACK`.

## Fixed Commands

Local dry-run only:

```powershell
cd D:\reserch\stock-bot
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages, _ = generate_report(dry_run=True); print('\\n--- MESSAGE ---\\n'.join(messages))"
```

## Next Action

- Owner reviews v21.0 unheld FSM dry-run output.
