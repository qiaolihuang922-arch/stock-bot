# CURRENT_STATE.md

## Current Task

- task_id: `unheld_market_overlay_version_20260610`
- status: `complete`
- version: `v21.0.1`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; visible wording must be decision-first and avoid internal pipeline terms.
- Current direction is v21 read-only trade state machine plus production pipeline hardening.
- Do not expand DB schema unless read-only behavior proves an actual cross-day memory gap.
- Production source-of-truth remains Supabase / runner data, not local cache.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval.

## Current Changes

- Report version bumped to `v21.0.1`.
- Weak market no longer hides stock-specific unheld gates.
- Current dry-run shows `等型態｜市場弱` and summary `未持倉 7｜僅追蹤 7（等型態）`.
- No fake data, DB write, schema change, or live Telegram delivery.

## Verification State

- Targeted tests: `2 passed, 5 warnings`.
- Broad suite: `296 passed, 145 warnings, 57 subtests passed`.
- Official `generate_report(dry_run=True)`: `4` messages, `v21.0.1`, no live Telegram delivery.
- Patch commit `52a5ae8` pushed to `origin/main`; final completion check follows closeout.

## Known Follow-ups

- Adaptive strategy thresholds from volume calibration remain a separate next strategy tuning task.
- MOPS/TWSE external sources can still time out; those paths remain fail-closed.
