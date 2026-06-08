# CURRENT_STATE.md

## Current Task

- task_id: `unheld_trade_fsm_contract_20260608`
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

- Unheld state machine now has formal pre-order FSM fields.
- Wait states are non-actionable and non-terminal.
- Source-error buyable candidates fail closed before order lifecycle.
- State artifact includes guards/blocked_by/next_required_event for dry-run/log inspection.

## Verification State

- `tests/test_trade_state_machine.py`: `5 passed, 3 warnings`.
- `tests/test_generator_report.py tests/test_trade_state_machine.py`: `194 passed, 145 warnings, 44 subtests passed`.
- official `generate_report(dry_run=True)`: v21.0 messages generated locally; no live Telegram delivery.

## Known Follow-ups

- Next logical layer is persisted unheld state snapshots or order lifecycle, but both should be separate tasks.
- CAO TUI automation gap remains separate from this product patch.
