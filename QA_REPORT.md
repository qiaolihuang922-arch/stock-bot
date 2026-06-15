# QA_REPORT: strategy_axis_memory_schema_v21_3_20260615

## Test Scope

- Schema artifact for strategy-axis DB memory.
- Snapshot payload field propagation.
- Type handling for text/bool/json/numeric strategy feature fields.
- Official report dry-run compatibility.

## Risk Scan

- If SQL exists but payload does not write fields, DB memory remains empty.
- If payload writes JSON/bool fields as numeric, Supabase writes will fail or data will be corrupted.
- If agent executes SQL directly, it violates DB schema-change boundary.
- If fallback is removed, production report can break before Owner applies schema.
- If data-quality defaults are overused, missing evidence can still look normal.

## Cross-Block Semantic Consistency

- `daily_price` remains OHLCV only.
- Strategy memory belongs to `daily_signal_snapshot` and `signal_items`.
- Three-axis report states are now persistable as DB fields.
- Existing report wording still separates strength/setup/action.

## User Misread Risk

- Reduced after schema execution: future reports/backtests can audit why a card was waiting or non-actionable.
- Remaining: until SQL is applied and backfilled, historical rows do not have these explicit columns.
- Remaining: source-error and insufficient-data paths still need a follow-up tightening pass.

## Failure Specimen Countercheck

- Owner concern was that multi-day memory must not be invented.
- Countermeasure:
  - explicit columns for setup state, blockers, retest state, data quality, and volume basis;
  - snapshot payload test proves these fields are emitted from strategy result;
  - SQL is manual, reviewable, and idempotent.

## Evidence

- `258 passed, 149 warnings, 44 subtests passed`.
- Official dry-run unheld report rendered successfully.
- SQL artifact exists at `db/sql/v21_3_strategy_axis_memory_columns.sql`.

## Not Tested

- Production SQL execution.
- Production backfill.
- Scheduled Render/GitHub runner after push.
- Live Telegram delivery.

## QA Conclusion

conditional pass

Reason: code and SQL artifact are ready and tested locally, but DB persistence is conditional on Owner applying the schema and then running a separate backfill.
