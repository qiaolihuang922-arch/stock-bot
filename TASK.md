# TASK: strategy_feature_persistence_v21_1_20260615

## Status
- task_id: `strategy_feature_persistence_v21_1_20260615`
- type: `major`
- status: `implemented`
- version: `v21.1`
- QA level: `L3`

## Owner Problem
Owner asked to re-check from scratch whether v21.1 strategy features are only fixed at runtime instead of being persisted, and authorized adding fields / recording more data if needed. Owner also asked how long to backfill.

## User Visible Result
- v21.1 strategy features are now prepared for durable DB storage, not just report-time wording.
- Daily runner and backfill payloads carry V10/V20, 20D/60D resistance, breakout distances, retest zone, and compact raw_result.
- A manual SQL migration is provided for Supabase.
- Backfill CLI supports `--lookback-days`; recommended v21.1 strategy-feature backfill is two years / 730 calendar days, with 120-day warmup.

## Non Goals
- No live Telegram delivery.
- No live production DB write in this task.
- No direct hand-written production DML.
- No RLS, grant, policy, role, index, or constraint change.
- No broker/order execution.
- No buy-rule loosening.

## Impacted Modules And Consumers
- `db/sql/v21_1_strategy_feature_snapshot_columns.sql`
  - Consumer: Owner / Supabase SQL editor.
- `core/signal_snapshot.py`
  - Consumer: official daily snapshot and backfill snapshot payload.
- `services/daily_snapshot_store.py`
  - Consumer: after-close daily `daily_signal_snapshot` writer.
- `services/signal_store.py`
  - Consumer: `signal_runs` / `signal_items` report-run persistence.
- `scripts/backfill_signals.py`
  - Consumer: guarded historical backfill CLI.
- `services/strategy_evidence.py`
  - Consumer: derived feature/outcome calibration.
- `services/volume_calibration.py`
  - Consumer: DB-backed volume calibration artifact.

## Output Contract
- `daily_signal_snapshot` payload includes:
  - `volume_ratio_10`, `volume_ratio_20`
  - `resistance_20`, `resistance_60`
  - `breakout_price_20`, `breakout_price_60`
  - `breakout_distance_20`, `breakout_distance_60`
  - `retest_zone_low`, `retest_zone_high`, `retest_zone_label`
  - compact `raw_result`
- `signal_items` payload includes the same typed strategy-feature columns and keeps compact raw_result.
- If production schema is not applied yet, daily snapshot / backfill / signal item writes fall back to legacy columns instead of crashing the runner.
- Backfill default recommendation:
  - apply SQL migration first;
  - backfill `--lookback-days 730`;
  - use existing approved repo script `scripts/backfill_signals.py`;
  - no live Telegram.

## Acceptance
- Tests prove official daily snapshot payload carries new fields.
- Tests prove guarded backfill payload carries new fields.
- Tests prove schema-missing fallback removes new fields and does not crash.
- Tests prove volume calibration uses V20 first and only falls back to legacy volume ratio if V20 is missing.
- SQL migration is idempotent and contains no RLS/grant/policy/role/index/constraint change.

## Failure Specimen And Route
- Failure: v21.1 report showed better strategy context, but durable DB records did not keep typed V20 / resistance / retest-zone features.
- Failure layer: persistence / backfill / calibration, not Telegram formatter.
- Verification route:
  - `tests/test_daily_snapshot_store.py`
  - `tests/test_backfill_signals.py`
  - `tests/test_volume_calibration.py`
  - focused v21.1 snapshot export test
  - dry-run backfill command with no DB write

## Forbidden / Blocking
- Do not claim production DB is updated unless SQL migration and write/backfill are actually executed.
- Do not store full OHLCV arrays inside raw_result.
- Do not use local cache or runtime dict as cross-day source-of-truth.
- Do not replace approved backfill/write scripts with manual production DML.
