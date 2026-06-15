# CURRENT_STATE.md

## Current Task

- task_id: `strategy_axis_memory_backfill_prune_20260615`
- status: `implemented + QA passed`
- version: `v21.1`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; report wording must be decision-first and avoid unexplained internal shorthand.
- Production dispatch model: Render web service is called every five minutes, then GitHub workflow dispatch runs `run_mode=bot`.
- Production source-of-truth is Supabase / runner data, not local cache, worktree state, or agent memory.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval unless explicitly authorized.
- Non-schema DB writes/backfills must use approved repo scripts or service APIs; direct hand-written production DML is forbidden.
- DB backfill/prune tasks must automatically update MD and cleanup evidence.

## Current Implementation State

- Runtime report remains `v21.1`.
- v21.3 strategy-axis memory schema is applied in production.
- `daily_signal_snapshot` backfilled from `daily_price`.
- `daily_signal_snapshot` now has populated strategy-axis memory for `5786` v21.1 rows.
- Retest memory was tightened after audit:
  - only `356` active retest rows have `retest_reference_price` / `retest_days_since_breakout`;
  - non-retest rows keep those fields null.
- `signal_items` schema exists, but historical rows are not backfilled because report-run history cannot be reconstructed truthfully from daily_price alone.
- Duplicate/version prune found no rows to delete.

## Verification State

- Production backfill:
  - `5786` snapshot rows upserted.
  - `schema_fallback=false`.
- Production read-after-write:
  - all `5786` rows have non-null `stock_strength_state`, `entry_setup_state`, and `actionability_state`.
  - `356` rows have active retest anchor/day fields; `5430` non-retest rows do not.
- Production prune:
  - exact duplicate extra rows: `0`.
  - multi-version extra rows: `0`.
  - `deleted_rows=0`.
- No live Telegram delivery.

## Known Follow-ups

- Commit and push MD closeout.
- Observe next scheduled `run_mode=bot` report and check `signal_items` new fields on fresh rows.
- Future tightening: source-error / insufficient-data paths should explicitly set data-quality fields instead of relying on normal defaults.
