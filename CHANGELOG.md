# CHANGELOG: strategy_axis_memory_schema_v21_3_20260615

## Changes

- Added `db/sql/v21_3_strategy_axis_memory_columns.sql`:
  - Extends `daily_signal_snapshot`.
  - Extends `signal_items`.
  - Adds strategy-axis, setup-memory, data-quality, volume-basis, and retest-memory columns.
  - Does not write/backfill data.
  - Does not change RLS, grants, policies, roles, indexes, or constraints.
- Updated `core/signal_snapshot.py`:
  - Added the new fields to `STRATEGY_FEATURE_FIELDS`.
  - Added text/bool/json handling so `setup_valid` and `setup_blockers` are not coerced into numeric fields.
- Updated `services/analysis.py`:
  - Derives `setup_family`, `setup_valid`, `setup_blocker`, `setup_blockers`.
  - Derives default data-quality, volume-basis, and retest-memory fields.
  - Keeps the existing three axes: `stock_strength_state`, `entry_setup_state`, `actionability_state`.
- Updated `tests/test_analysis_engine.py`:
  - Snapshot payload now verifies persisted strategy-axis/memory fields.

## Contract Impact

- `daily_signal_snapshot` and `signal_items` can persist strategy memory after Owner applies SQL.
- Before SQL execution, existing schema fallback can still write legacy rows instead of breaking the report.
- `daily_price` remains unchanged.
- No live Telegram delivery.
- No production SQL execution by agent.

## Direct Consumer Sync

- `services.daily_snapshot_store._signal_payload(...)` automatically includes new fields through `STRATEGY_FEATURE_FIELDS`.
- `services.signal_store._item_payload(...)` automatically includes new fields through `strategy_feature_payload(...)`.
- Official Telegram text remains compatible; this patch is persistence/audit support, not a report wording change.

## Verification

- Related regression:
  ```powershell
  $env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -m pytest tests\test_analysis_engine.py tests\test_generator_report.py tests\test_unheld_gap_format.py tests\test_condition_engine.py tests\test_trade_state_machine.py -q --tb=short
  ```
  Result: `258 passed, 149 warnings, 44 subtests passed`.
- Official dry-run:
  ```powershell
  $env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages,_=generate_report(dry_run=True); print(messages[1])"
  ```
  Result: unheld report still renders with three-axis split; no live Telegram delivery.
- SQL artifact read:
  - `db/sql/v21_3_strategy_axis_memory_columns.sql` is UTF-8 readable and contains the manual execution notes.

## Covered Layers

- SQL artifact: file present and idempotent by construction.
- Snapshot payload: covered by `tests/test_analysis_engine.py`.
- Official generator/report: covered by dry-run and existing generator tests.
- DB execution/backfill: not performed by design.

## Residual Risk

- Until Owner applies the SQL, production DB cannot persist the new columns and write path may schema-fallback.
- Backfill is still a separate follow-up after schema execution.
- Data-quality states default to `complete` for normal strategy results; future source-error paths should be tightened to write explicit `insufficient/source_error` where available.
