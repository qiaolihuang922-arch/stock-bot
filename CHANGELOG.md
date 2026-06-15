# CHANGELOG: multi_window_strategy_v21_1_20260615

## Changes
- `services/analysis.py`
  - Added V20 into `multi_period_metrics`.
  - Volume state now uses V10/V20 combined context instead of V10 alone.
  - Added 20D/60D resistance helpers and 20D retest zone.
  - Strategy result now carries V10/V20, 20D/60D resistance, breakout price, and retest zone fields.
- `core/generator.py`
  - Bumped visible version to `v21.1`.
  - Added fallback V20 and breakout/retest-zone context for official report payloads.
- `core/signal_snapshot.py`
  - Backfill / daily snapshots now preserve V10/V20 and raw retest-zone context.
- `presentation/report.py`
  - Acute rebound card now shows V10/V20 and concrete zone.
  - If current price is below the breakout zone, card says `現價未站回`.
- `tests/test_analysis_engine.py`
  - Added raw-result / snapshot test for multi-window strategy fields.
- `tests/test_generator_report.py`
  - Added report tests for V10/V20, retest-zone display, and below-zone wording.

## Contract Impact
- New result/raw_result fields:
  - `volume_ratio_10`, `volume_ratio_20`
  - `resistance_20`, `resistance_60`
  - `breakout_price_20`, `breakout_price_60`
  - `retest_zone_low`, `retest_zone_high`, `retest_zone_label`
- Telegram wording changes for acute rebound wait cards.
- No DB schema or live delivery changes.

## Verification
- Focused:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py::GeneratorReportTest::test_v21_1_strong_rebound_uses_multi_window_retest_context tests/test_generator_report.py::GeneratorReportTest::test_v21_1_retest_anchor_says_breakout_zone_when_price_is_below_zone tests/test_analysis_engine.py::AnalysisEngineTest::test_v21_1_snapshot_exports_multi_window_volume_and_retest_zone -q --tb=short
  ```
  Result: `3 passed`.
- Targeted strategy/report/backfill suite:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_analysis_engine.py tests/test_signal_validator.py tests/test_trade_state_machine.py tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_backfill_signals.py tests/test_backfill_daily_price_history.py -q --tb=short
  ```
  Result: `307 passed, 149 warnings, 57 subtests passed`.
- Official dry-run:
  - `VERSION v21.1`
  - no live Telegram delivery
  - 旺宏 card shows `突破區 175.5~176.38（現價未站回）`
  - 旺宏 card shows `V10 0.52x / V20 0.26x偏弱`

## Coverage Layers
- Strategy metrics.
- Signal snapshot / backfill payload.
- Trade state machine guards.
- Telegram unheld formatter.
- Official generator dry-run.

## Residual Risk
- V20/60D are now available and used, but thresholds still need longer historical calibration from production outcomes.
- No DB schema change means new fields are persisted only where raw_result / artifact payload already stores expanded result JSON.
