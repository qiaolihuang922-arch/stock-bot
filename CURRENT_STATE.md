# CURRENT_STATE.md

## Current Task

- task_id: `trade_state_machine_v21_20260608`
- status: `conditional_pass`
- version: `v21.0`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; visible wording must be decision-first and avoid internal pipeline terms.
- Current direction is no longer just report cleanup; system is being upgraded toward a trade state machine.
- Do not expand DB schema unless read-only v1 proves an actual cross-day memory gap.
- Production source-of-truth remains Supabase / runner data, not local cache.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval.
- Fixed Markdown files must be rewritten/compressed, not removed.

## Current Changes

- Version bumped to `v21.0`.
- Added read-only derived trade state machine:
  - `UNTRACKED/WATCH/WAIT_VOLUME/WAIT_PULLBACK/WAIT_RR/WAIT_COOLDOWN/READY/BUYABLE/ENTERED_TODAY/HOLD/REDUCE/TAKE_PROFIT/STOP_LOSS/CLOSED/BLOCKED`.
- TG cards now show a per-stock `交易狀態` line.
- State machine artifact marks `db_write=False` and `schema_change=False`.

## Verification State

- `py_compile` passed.
- state machine tests passed: 4 tests.
- focused generator/state-machine replay passed: 7 tests.
- market theme tests passed: 38 tests, 13 subtests.
- official `generate_report(dry_run=True)` passed: v21.0 local preview messages, no live Telegram delivery.
- Full generator regression currently conditional: 160 passed / 39 failed. Do not claim full QA pass until those old exact-message assertions are reconciled.

## Known Follow-ups

- Reconcile full `tests/test_generator_report.py` with v21 visible state line and state-machine contract.
- Decide whether v21 state snapshots need write-back after read-only behavior is accepted.
- CAO TUI automation gap still needs a runner-level fix.
