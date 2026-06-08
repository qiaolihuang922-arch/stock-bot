# CURRENT_STATE.md

## Current Task

- task_id: `trade_state_machine_v21_completion_20260608`
- status: `QA passed, pending git completion`
- version: `v21.0`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; visible wording must be decision-first and avoid internal pipeline terms.
- Current direction is v21 read-only trade state machine, not only report cleanup.
- Do not expand DB schema unless read-only v1 proves an actual cross-day memory gap.
- Production source-of-truth remains Supabase / runner data, not local cache.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval.
- Fixed Markdown files must be rewritten/compressed, not removed.

## Current Changes

- v21 state machine integration completed through official generator regression.
- `tests/test_generator_report.py tests/test_trade_state_machine.py` now pass fully.
- TG cards show per-stock trade state/action/trigger on official report path.
- Unheld cards distinguish wait states such as `WAIT_VOLUME`, `WAIT_PULLBACK`, `WAIT_RR`, and next-day confirmation.
- Blocker precedence fixed: visible hard blocker first; source gate only primary when no clearer blocker exists.

## Verification State

- `tests/test_generator_report.py tests/test_trade_state_machine.py`: `193 passed, 145 warnings, 44 subtests passed`.
- official `generate_report(dry_run=True)`: v21.0 messages generated locally; no live Telegram delivery.
- `.pytest_cache` local permission warning remains but does not block test completion.

## Known Follow-ups

- After Owner reviews v21 dry-run effect, decide whether to persist state snapshots in DB; that would require a separate approved write/schema task if needed.
- CAO TUI automation gap remains separate from this product patch.
