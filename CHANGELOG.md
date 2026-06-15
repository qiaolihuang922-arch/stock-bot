# CHANGELOG: strategy_feature_persistence_v21_1_20260615

## Changes

- Added v21.1 strategy-feature persistence support:
  - `db/sql/v21_1_strategy_feature_snapshot_columns.sql`
  - `core/signal_snapshot.py`
  - `services/daily_snapshot_store.py`
  - `services/signal_store.py`
  - `scripts/backfill_signals.py`
  - `services/strategy_evidence.py`
  - `services/volume_calibration.py`
- Persisted feature set:
  - V10/V20 volume;
  - 20D/60D resistance;
  - 20D/60D breakout prices and distances;
  - retest zone fields;
  - compact `raw_result`.
- Added schema-missing fallbacks so pre-migration runner/backfill paths do not crash.
- Added `--lookback-days` to guarded backfill; two-year backfill with warmup was used after Owner applied migration.
- Wired market/theme freshness into normal `run_mode=bot`; `daily_evidence` remains manual recovery.
- Cleaned duplicate/old `daily_signal_snapshot` versions through approved scripts; final production snapshot rows are `v21.1` only.
- Improved Telegram report display:
  - shared compact setup evidence for non-actionable unheld cards;
  - removed redundant after-hours internal lines;
  - moved breakout distance to standalone `距突破：x%｜狀態` line for holding and unheld cards;
  - removed breakout distance from `盤面`.
- Added strategy-granular wording:
  - cooling cards explain heat/cooling first and hide internal non-actionable data noise;
  - setup/retest/RR-repair cards keep positive evidence as `補充` with blocker-specific caveats;
  - limit-lock and sharp-rebound chase contexts remain `等回測`; pure overheat remains `等冷卻`;
  - unmet RR is not duplicated inside setup evidence once it is already the main blocker;
  - after-hours unheld summary lists state-group names only when bounded and readable;
  - strong rebound holding watch gets a rebound-continuation next step.

## Contract Impact

- DB schema artifact exists and has been applied by Owner; no RLS/grant/policy/role/index/constraint change was introduced by the artifact.
- Daily snapshot, report item, and guarded backfill payloads now carry typed v21.1 strategy fields.
- Report display changed, but buy/sell strategy thresholds did not change.
- `距突破` visibility no longer depends on strategy branch; it is a stock-card display field when data exists.
- Non-actionable evidence wording now depends on funnel state instead of a global delete/keep rule.
- Overheat/cooling priority now checks the strategy state before collapsing a card into `等冷卻`; this is a report-state fix, not a threshold loosening.
- Summary grouping is capped by total/group size to avoid long mobile noise.

## Verification

- Focused persistence/backfill/calibration:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_daily_snapshot_store.py tests/test_backfill_signals.py tests/test_volume_calibration.py tests/test_analysis_engine.py::AnalysisEngineTest::test_v21_1_snapshot_exports_multi_window_volume_and_retest_zone -q --tb=short
  ```
  Result: `19 passed`.
- Report readability / generator regression:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_unheld_gap_format.py tests/test_generator_report.py -q --tb=short
  ```
  Result: `205 passed, 147 warnings, 44 subtests passed`.
- Broader targeted strategy/report/backfill suite: `334 passed, 149 warnings, 57 subtests passed`.
- Official generator dry-run used `dry_run=True`; no live Telegram delivery.
- Official generator dry-run confirmed:
  - `等回測｜急彈待回測` keeps retest context;
  - `已突破，但漲停/過熱不追` appears for limit-up/overheat breakout;
  - RR repair cards do not repeat the same unmet RR blocker in setup context;
  - summary names are bounded by state group.

## Residual Risk

- Next scheduled production `run_mode=bot` should still be observed after the after-close safe-write window.
- Live Telegram delivery was not performed in this cycle.
- Future strategy-quality work should calibrate thresholds from persisted outcome data; this cycle did not loosen buy/sell rules.
