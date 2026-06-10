# CURRENT_STATE.md

## Current Task

- task_id: `future_watch_fundamental_layout_20260610`
- status: `complete, pending commit/push`
- version: `v21.0.1`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; visible wording must be decision-first and avoid internal pipeline terms.
- Current direction is v21 read-only trade state machine plus production pipeline hardening.
- Do not expand DB schema unless read-only behavior proves an actual cross-day memory gap.
- Production source-of-truth remains Supabase / runner data, not local cache.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval.

## Current Changes

- Future-watch `關注標的財報` block now uses multi-line stock/EPS/revenue layout.
- `關注原因` removed from fundamentals block only.
- No data source, calculation, DB write, schema, or live Telegram change.

## Verification State

- Targeted future-watch tests: `5 passed, 1 warning`.
- Full generator tests: `195 passed, 143 warnings, 44 subtests passed`.
- Official dry-run confirmed requested layout.

## Known Follow-ups

- None for this formatting task.
