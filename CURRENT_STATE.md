# CURRENT_STATE.md

## Current Task

- task_id: `latest_revenue_month_fallback_20260610`
- status: `complete_pending_git`
- version: `v21.0`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; visible wording must be decision-first and avoid internal pipeline terms.
- Current direction is v21 read-only trade state machine plus production pipeline hardening.
- Do not expand DB schema unless read-only behavior proves an actual cross-day memory gap.
- Production source-of-truth remains Supabase / runner data, not local cache.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval.

## Current Changes

- Monthly revenue lookup now rolls automatically by trying latest-to-older MOPS month candidates.
- Normalized revenue row keys are supported for stable internal merge.
- No DB write path, schema, or live Telegram delivery changed.

## Verification State

- Targeted latest revenue tests: `2 passed, 1 warning`.
- Generator/state machine suite: `199 passed, 145 warnings, 44 subtests passed`.
- Official `generate_report(dry_run=True)`: `4` messages, about `58.3s`, no live Telegram delivery.

## Known Follow-ups

- MOPS monthly revenue fallback is best-effort and can time out per target.
- CAO TUI automation gap remains separate from this product patch.
