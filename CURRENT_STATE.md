# CURRENT_STATE.md

## Current Task

- task_id: `unheld_transition_table_replay_20260608`
- status: `complete`
- version: `v21.0`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; visible wording must be decision-first and avoid internal pipeline terms.
- Current direction is v21 read-only trade state machine.
- Start with unheld FSM first; holding/order lifecycle remains separate.
- Do not expand DB schema unless read-only behavior proves an actual cross-day memory gap.
- Production source-of-truth remains Supabase / runner data, not local cache.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval.

## Current Changes

- Unheld state machine now has a transition table, not only metadata fields.
- Explicit event paths cover data gate, volume gate, RR gate, pullback gate, setup ready, and buy signal confirmed.
- Wait states are non-actionable; `BUYABLE` is the only actionable unheld state.
- Source-error ready/buyable candidates route to `WAIT_DATA`.
- Wait-state unheld cards no longer show contradictory source-warning text.

## Verification State

- `tests/test_generator_report.py tests/test_trade_state_machine.py`: `196 passed, 145 warnings, 44 subtests passed`.
- official `generate_report(dry_run=True)`: v21.0 messages generated locally; no live Telegram delivery.
- local replay covered six routes: wait-volume, volume-to-ready, ready-to-buyable, ready-source-error, RR repair, pullback repair.
- Git completion gate passed on `main` at `c0e210c` before closeout doc refresh.

## Known Follow-ups

- Next logical layer is persisted unheld state snapshots or order lifecycle, but both should be separate tasks.
- CAO TUI automation gap remains separate from this product patch.
