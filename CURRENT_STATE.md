# CURRENT_STATE.md

## Current Task

- task_id: `setup_aware_volume_fsm_20260610`
- status: `complete, pending commit/push`
- version: `v21.0`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; visible wording must be decision-first and avoid internal pipeline terms.
- Current direction is v21 read-only trade state machine plus production pipeline hardening.
- Do not expand DB schema unless read-only behavior proves an actual cross-day memory gap.
- Production source-of-truth remains Supabase / runner data, not local cache.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval.

## Current Changes

- Unheld FSM and report now distinguish `WAIT_MARKET`, `WAIT_SETUP`, `WAIT_VOLUME`, `WAIT_PULLBACK`, `WAIT_RR`, and `WAIT_COOLDOWN` visible states.
- Volume is primary only for breakout / pre-breakout contexts; far weak-market candidates wait for market/setup first.
- Distance from breakout is context-sensitive and no longer a universal blocker.
- Added read-only volume calibration artifact using DB history; no DB write or schema change.

## Verification State

- Broad suite: `258 passed, 145 warnings, 44 subtests passed`.
- Official `generate_report(dry_run=True)`: `4` messages, no live Telegram delivery.
- Read-only DB calibration artifact: `source_status=available`, `db_write=false`, `schema_change=false`.

## Known Follow-ups

- Wire calibration artifact into adaptive strategy thresholds only after Owner approves the next strategy tuning task.
- MOPS/TWSE external sources can still time out; those paths remain fail-closed.
