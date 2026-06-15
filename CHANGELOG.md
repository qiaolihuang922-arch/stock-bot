# CHANGELOG: strategy_feature_persistence_v21_1_20260615

## Changes
- `db/sql/v21_1_strategy_feature_snapshot_columns.sql`
  - Added idempotent manual migration for v21.1 strategy-feature columns on `daily_signal_snapshot` and `signal_items`.
  - Adds typed V10/V20, 20D/60D resistance, breakout prices/distances, retest-zone fields, and `daily_signal_snapshot.raw_result`.
  - Does not change RLS, grants, policies, roles, indexes, or constraints.
- `core/signal_snapshot.py`
  - Added shared `STRATEGY_FEATURE_FIELDS` and `strategy_feature_payload`.
  - `analyze_ohlcv_snapshot` and `snapshot_from_result` now expose typed v21.1 strategy-feature fields in the snapshot row itself, not only inside raw_result.
- `services/daily_snapshot_store.py`
  - Daily after-close payload now includes typed strategy features and compact raw_result.
  - `record_daily_snapshots` now falls back to legacy signal snapshot columns if production schema has not been migrated yet.
- `services/signal_store.py`
  - `signal_items` payload now carries typed strategy-feature fields and stores the same compact feature payload inside raw_result.
  - Insert path falls back to legacy item columns if production schema has not been migrated yet.
- `scripts/backfill_signals.py`
  - Backfill rows now include typed v21.1 strategy features and compact raw_result.
  - Added schema-missing fallback for `daily_signal_snapshot` upsert.
  - Added `--lookback-days`; recommended v21.1 strategy-feature backfill is `730` days with 120-day warmup.
- `services/strategy_evidence.py`
  - Derived feature rows now keep V20 and 20D/60D breakout distances when present.
- `services/volume_calibration.py`
  - Calibration now buckets volume by V20 first, falling back to legacy volume ratio only when V20 is absent.
  - New-column read falls back to legacy select if schema has not been applied.
- Tests:
  - Added persistence/fallback assertions in daily snapshot and backfill tests.
  - Updated volume calibration test to assert V20-first behavior.
- `presentation/report.py`
  - Added shared compact setup context for non-actionable unheld cards, including retest / breakout zone, breakout distance, V10/V20 status, and RR status where data exists.
  - Fixed the inconsistent display where only the `急彈待回測` branch showed detailed buy-blocker evidence while `等型態` / `等RR修復` fell back to generic text.
  - Suppressed redundant after-hours `盤面：證據不足｜待確認` and `數據：...風控不適用` lines for waiting / rejected tracking cards when `量化差距` already carries the decision evidence.
  - Moved breakout distance to a standalone `距突破：x%｜狀態` line for both holding and unheld cards whenever the value exists.
  - Removed the breakout-distance segment from `盤面`, so `盤面` only carries structure / strength / volume context.
- `tests/test_unheld_gap_format.py`
  - Added report-level formatter coverage for `等型態` and `急彈待回測` unheld cards.
- `tests/test_generator_report.py`
  - Updated regression coverage so breakout distance must be shown as a standalone line and must not be embedded back into `盤面`.

## Contract Impact
- Repo now has a DB migration artifact, but this task did not execute it.
- Production daily writer remains compatible before migration because of schema fallback.
- After SQL migration, daily runner and guarded backfill can persist the new typed fields.
- Backfill command can be driven by `--lookback-days` instead of hand-computed dates.
- Unheld report card strategy decisions are unchanged; only the visible explanation/noise layout changed.
- Non-actionable unheld cards can now expose the same setup evidence shape instead of only one special branch showing it.
- Breakout distance visibility no longer depends on strategy branch; it is a display-level stock-card field when data exists.

## Verification
- Focused persistence/backfill/calibration:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_daily_snapshot_store.py tests/test_backfill_signals.py tests/test_volume_calibration.py tests/test_analysis_engine.py::AnalysisEngineTest::test_v21_1_snapshot_exports_multi_window_volume_and_retest_zone -q --tb=short
  ```
  Result: `19 passed`.
- Report readability regression:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_unheld_gap_format.py tests/test_generator_report.py -q --tb=short
  ```
  Result: `205 passed, 147 warnings, 44 subtests passed`.
- Official generator dry-run was executed with `dry_run=True`; no live Telegram delivery.

## Coverage Layers
- DB migration artifact.
- Official daily signal snapshot payload.
- Guarded historical backfill payload.
- `signal_items` report-run persistence payload.
- Schema-missing fallback path.
- Volume calibration consumer.
- Telegram unheld-card formatter for waiting/rejected tracking cards.
- Official generator report regression suite.
- Holding and unheld stock card breakout-distance presentation.

## Residual Risk
- Production DB still needs the manual SQL migration before typed columns are actually stored.
- Historical feature rows need a production backfill after migration.
- This task does not validate live Supabase writes or live Telegram delivery.
- Report readability fix does not change buy/sell strategy thresholds; future strategy tuning remains a separate task.
