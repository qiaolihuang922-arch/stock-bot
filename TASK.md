# TASK: strategy_axis_memory_schema_v21_3_20260615

## Status

- task_id: `strategy_axis_memory_schema_v21_3_20260615`
- task_type: `major`
- status: `implemented`
- version: `v21.1 runtime / v21.3 schema artifact`
- QA level: `L3`

## Owner Problem

Owner wants the strategy to stop pretending it remembers multi-day state when the DB has no such memory. The three report axes (`強弱`, `買點`, `行動`) must become persistable evidence, not only runtime/report text.

## User Visible Result

- New SQL file is ready for Owner review/execution:
  - `db/sql/v21_3_strategy_axis_memory_columns.sql`
- Daily strategy snapshots and signal items can persist:
  - stock strength axis;
  - entry setup state;
  - actionability state;
  - setup family/blockers;
  - data quality state;
  - volume basis;
  - retest memory.
- Existing schema fallback remains: if SQL has not been applied yet, DB writes fall back instead of breaking the report.

## Non Goals

- No live Telegram delivery.
- No agent-executed production SQL.
- No production backfill in this task.
- No RLS/grant/policy/role/index/constraint change.
- No threshold calibration.

## Impacted Modules And Direct Consumers

- `db/sql/v21_3_strategy_axis_memory_columns.sql`
  - Direct consumer: Owner/Supabase SQL editor.
- `core/signal_snapshot.py`
  - Direct consumer: `daily_signal_snapshot` payloads and backfill/replay payloads.
- `services/analysis.py`
  - Direct consumer: strategy result payload.
- `services/daily_snapshot_store.py`
  - Direct consumer through `STRATEGY_FEATURE_FIELDS`.
- `services/signal_store.py`
  - Direct consumer through `strategy_feature_payload`.
- `tests/test_analysis_engine.py`

## Output Contract

- Multi-day strategy memory must come from DB columns or explicit DB JSON fields.
- Missing data must be representable as `insufficient`, `source_error`, `stale`, or `missing_source`; it must not be silently converted into normal evidence.
- `setup_blockers` is JSON, `setup_valid` is boolean, and text labels remain text.
- `daily_price` remains OHLCV only; derived strategy evidence belongs in `daily_signal_snapshot` / `signal_items`.

## Version Contract

- Runtime report header remains `v21.1`.
- Schema artifact is named `v21_3` because it extends persisted memory fields.

## Acceptance Conditions

- SQL artifact is idempotent and contains only `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` plus comments and validation marker.
- Snapshot payload includes the new fields before DB execution.
- Existing DB write fallback remains available when columns are missing.
- Related tests pass.
- Official dry-run report still renders.

## Fixture / Failure Specimen

- Owner concern: strategy output can say multi-day-like conclusions even when the DB has no explicit memory for setup state, retest state, or blockers.
- Required replay route: snapshot test plus official `generate_report(dry_run=True)`.

## Forbidden And Blocking Conditions

- Do not execute production SQL from agent.
- Do not hand-write production DML.
- Do not claim backfill is done before Owner applies schema and backfill script runs.
- Do not use local cache or report text as cross-day memory.
