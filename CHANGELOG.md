# CHANGELOG: db_table_health_audit_20260615

## Changes

- Added `scripts/audit_db_table_health.py`.
  - Reads configured Supabase tables through the normal client.
  - Profiles row count, column count, constant columns, mostly-null columns, and table-specific duplicate candidates.
  - Emits JSON with explicit `read_only`, `live_telegram`, and `schema_change` flags.
- Added `tests/test_audit_db_table_health.py`.
  - Prevents event tables from being misclassified as duplicate just because a stock repeats.
  - Confirms mostly-null columns are reported without guessing values.
- Strengthened `tests/test_daily_snapshot_store.py`.
  - Future `signal_items` payloads must include strategy-axis fields such as `stock_strength_state`, `entry_setup_state`, `actionability_state`, `setup_family`, `setup_valid`, `data_quality_state`, and `volume_basis`.

## Production Audit Result

- `daily_price`
  - Healthy for current use.
  - Constant `source=twse` is expected metadata.
  - No table-specific duplicate finding.
- `daily_signal_snapshot`
  - Healthy for v21.1 strategy memory after previous backfill.
  - Constant fields such as `version=v21.1`, `rr_formula`, `volume_basis=daily_close_volume`, and `breakout_reference_type=close_20` are expected basis/formula metadata.
  - `intraday_volume_run_rate` is all null because the current backfill is daily-close data, not intraday run-rate data.
- `market_theme_confirmed_evidence`
  - Constant source/evidence metadata is expected for this TWSE official-source backfill.
- `market_theme_index_daily_bars`
  - Actionable gap: `open`, `high`, `low`, `volume`, `turnover`, and `member_count` are all null.
  - Current rows are usable only for available index-level close/change evidence, not full OHLCV/breadth analysis.
- `position_events`
  - Repeated stocks are normal event history, not duplicate rows.
  - Constant `telegram_chat_id` and zero `realized_profit_delta` are metadata / current behavior, not strategy signal.
- `positions`
  - No audit issue found.
- `sector_theme_members`
  - Static membership table; repeated source metadata and `is_active=true` are expected.
  - `weight` and `valid_to` are all null; keep as schema placeholders unless weighting / expiry logic is implemented.
- `signal_items`
  - Historical rows have new strategy-memory columns all null.
  - This is expected because old report runs cannot be truthfully reconstructed from `daily_price`.
  - Future write path is now tested.
- `signal_outcomes`
  - Actionable gap: `max_drawdown_pct` and `max_high_pct` are all null.
  - Outcome tracking is incomplete until those metrics are computed by a real outcome job.
- `signal_runs`
  - Constant `run_phase=daily_close` is expected for current runs.

## Contract Impact

- New audit utility is read-only and does not change report generation.
- Future `signal_items` writes have stronger test coverage for the new strategy fields.
- No DB schema change, no DB deletion, no live Telegram delivery.

## Direct Consumer Sync

- Operators can run:
  - `.\.venv\Scripts\python.exe scripts\audit_db_table_health.py`
- The script output should be used as a diagnostic artifact, not as a production decision source.

## Verification

- Production audit command:
  - `.\.venv\Scripts\python.exe scripts\audit_db_table_health.py`
  - result: `errors=[]`
- Test command:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_audit_db_table_health.py tests\test_daily_snapshot_store.py tests\test_analysis_engine.py -q --tb=short`
  - result: `56 passed`

## Covered Layers

- Production DB read-only audit.
- Utility helper tests.
- Future `signal_items` payload contract.
- MD handoff and cleanup classification.

## Residual Risk

- `market_theme_index_daily_bars` still needs either an OHLCV-capable source or cleanup of unused placeholder columns.
- `signal_outcomes` still needs a real outcome metric job if max high/drawdown are intended to be used.
- Next scheduled `run_mode=bot` should still be observed to confirm new `signal_items` rows populate in production.
