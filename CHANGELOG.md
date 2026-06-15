# CHANGELOG: strategy_axis_memory_backfill_prune_20260615

## Changes

- Tightened retest memory semantics after production distribution audit:
  - `retest_reference_price` is now populated only when `retest_state != not_applicable`.
  - `retest_days_since_breakout` is now populated only when `retest_state != not_applicable`.
  - This prevents non-retest days from looking like they have active retest memory.
- Ran production DB schema read check for v21.3 fields:
  - `daily_signal_snapshot`: all fields readable.
  - `signal_items`: all fields readable.
- Backfilled `daily_signal_snapshot` from `daily_price` via repo script:
  - source: `daily_price`
  - version: `v21.1`
  - date range: `2024-06-15` to `2026-06-15`
  - warmup start: `2024-02-16`
  - stocks: 12 watchlist stocks
  - total snapshot rows written/upserted: `5786`
  - schema fallback: `false`
- Ran duplicate/version prune via repo script:
  - keep version: `v21.1`
  - delete candidates: `0`
  - deleted rows: `0`
- Updated `AGENTS.md` with reusable DB backfill/prune closeout rules.

## Contract Impact

- `daily_signal_snapshot` now has persisted strategy-axis memory fields for v21.1 historical rows.
- `signal_items` schema exists but historical report-run rows were not fabricated; future bot runs will populate them.
- No live Telegram delivery.
- No hand-written production DML.
- No schema/RLS/grant/policy/role/index/constraint change by agent.

## Direct Consumer Sync

- Strategy evidence and future calibration can now query `daily_signal_snapshot` columns directly:
  - `stock_strength_state`
  - `entry_setup_state`
  - `actionability_state`
  - `setup_family`
  - `setup_valid`
  - `setup_blocker`
  - `setup_blockers`
  - `data_quality_state`
  - `volume_basis`
  - `retest_state`
- `signal_items` remains a report-run item table; new rows from future bot runs can persist the same fields.

## Verification

- Backfill write result by stock:
  - 3231: `484`
  - 2421: `484`
  - 3035: `484`
  - 2303: `484`
  - 3481: `477`
  - 2344: `484`
  - 2376: `484`
  - 2408: `469`
  - 2356: `484`
  - 2324: `484`
  - 2301: `484`
  - 2337: `484`
- Read-after-write:
  - total rows: `5786`
  - versions: `{'v21.1': 5786}`
  - `stock_strength_state` non-null: `5786`
  - `entry_setup_state` non-null: `5786`
  - `actionability_state` non-null: `5786`
  - `setup_family` non-null: `5786`
  - `data_quality_state` non-null: `5786`
  - `volume_basis` non-null: `5786`
  - `retest_state` non-null: `5786`
  - `retest_reference_price` non-null after tightening: `356`
  - `retest_days_since_breakout` non-null after tightening: `356`
  - exact duplicate extra rows: `0`
  - stock/date multi-version extra rows: `0`
- Prune write:
  - `deleted_rows=0`
  - after total rows: `5786`
  - unique stock/date: `5786`
  - exact duplicate groups: `0`

## Covered Layers

- Production schema read.
- Production backfill via repo script/API.
- Production read-after-write.
- Production prune via repo script/API.
- MD process closeout.

## Residual Risk

- `signal_items` historical rows remain mostly null for new fields because they represent actual report runs and cannot be truthfully reconstructed from daily_price alone.
- Data-quality fields currently backfill as `complete` because the source was complete `daily_price`; source-error/insufficient-data tightening remains a future task.
