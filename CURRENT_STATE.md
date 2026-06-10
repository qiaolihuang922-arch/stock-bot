# CURRENT_STATE.md

## Current Task

- task_id: `revenue_fallback_no_downgrade_20260610`
- status: `complete`
- version: `v21.0`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; visible wording must be decision-first and avoid internal pipeline terms.
- Current direction is v21 read-only trade state machine plus production pipeline hardening.
- Do not expand DB schema unless read-only behavior proves an actual cross-day memory gap.
- Production source-of-truth remains Supabase / runner data, not local cache.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval.

## Current Changes

- Revenue fallback rejects old-month downgrades.
- Revenue fallback no longer uses revenue amount as YoY.
- Revenue fallback only accepts latest completed month or one-month fallback.
- No DB write path, schema, or live Telegram delivery changed.

## Verification State

- Targeted revenue tests: `5 passed, 1 warning`.
- Generator/state machine suite: `202 passed, 145 warnings, 44 subtests passed`.
- Official `generate_report(dry_run=True)`: `4` messages, `bad_large_pct False`, `too_old False`, no live Telegram delivery.
- Commit `eca967c` pushed to `origin/main`; equivalent git completion check passed (`HEAD == origin/main`).

## Known Follow-ups

- MOPS monthly revenue fallback is best-effort and can time out per target.
- CAO TUI automation gap remains separate from this product patch.
