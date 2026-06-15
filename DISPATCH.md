# DISPATCH.md

## Active

- task_md_holds: `strategy_axis_memory_schema_v21_3_20260615`
- status: `implemented + QA conditional pass`
- current_version: `v21.1 runtime / v21.3 schema artifact`
- no live Telegram delivery in this cycle.

## Result Summary

- Owner requested DB-backed memory for strategy axes, not local/runtime/report-text memory.
- Added SQL artifact:
  - `db/sql/v21_3_strategy_axis_memory_columns.sql`
- Added persistable fields for:
  - `stock_strength_state`
  - `entry_setup_state`
  - `actionability_state`
  - `setup_family`
  - `setup_valid`
  - `setup_blocker`
  - `setup_blockers`
  - `data_quality_state`
  - `price_data_state`
  - `volume_data_state`
  - `volume_basis`
  - `intraday_volume_run_rate`
  - `retest_state`
  - `retest_reference_price`
  - `retest_days_since_breakout`
  - `breakout_reference_type`
- Wired these through snapshot/report item payload paths.
- Agent did not execute production SQL, write production data, backfill, or send live Telegram.

## Verification

- Related regression:
  - `258 passed, 149 warnings, 44 subtests passed`.
- Official generator dry-run:
  - unheld report still renders.
  - no live Telegram delivery.
- SQL artifact:
  - idempotent `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`.
  - no RLS/grant/policy/role/index/constraint change.

## Current Git State

- branch: `main`
- upstream: `origin/main`
- closeout uses Windows-equivalent git checks because bash scripts may fail on this machine without WSL/Hyper-V.

## Next Action

- Commit/push this patch.
- Owner applies `db/sql/v21_3_strategy_axis_memory_columns.sql` in Supabase SQL editor.
- After schema is confirmed, run a separate backfill task; do not claim historical DB memory exists before backfill.
