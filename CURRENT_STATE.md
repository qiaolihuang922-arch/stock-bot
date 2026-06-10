# CURRENT_STATE.md

## Current Task

- task_id: `report_revenue_noise_fsm_20260610`
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

- Future-watch fundamentals can refresh stale TWSE/TPEX OpenAPI monthly revenue through MOPS company monthly revenue.
- MOPS fallback skips the slow/stale TWSE listed-revenue bulk endpoint, uses 3-second target fetches with limited concurrency, and runs a 2-second small retry for missed priority rows.
- Closing/after-hours unheld cards hide cross-day history noise.
- Unheld FSM visible line now says what confirmation is still missing instead of repeating trigger text.
- No DB write path, schema, or live Telegram delivery changed.

## Verification State

- Generator/state machine suite: `198 passed, 145 warnings, 44 subtests passed`.
- Official `generate_report(dry_run=True)`: `4` messages, about `55-59s`, no live Telegram delivery.
- Official dry-run unheld history noise check: `False`.
- Official dry-run future watch: holding rows refreshed to 2026/05; some candidate rows may show EPS only when MOPS times out.
- Commit `182d26d` pushed to `origin/main`; equivalent git completion check passed (`HEAD == origin/main`).
- WSL shell gate could not run because local WSL reports `HCS_E_HYPERV_NOT_INSTALLED`; PowerShell git checks were used as the equivalent gate.

## Known Follow-ups

- MOPS monthly revenue fallback is best-effort and can time out per target.
- CAO TUI automation gap remains separate from this product patch.
