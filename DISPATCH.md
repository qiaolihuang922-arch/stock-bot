# DISPATCH.md

## Active

- task_md_holds: `multi_window_strategy_v21_1_20260615`
- status: `complete`
- owner_request:
  - Scan global strategy code.
  - Add v21.1 multi-window volume / resistance / retest-zone strategy.
  - Deliver a completed, evidence-backed strategy treatment, not a report-only patch.
  - No live Telegram delivery.

## Current Result

- Visible version is now `v21.1`.
- Strategy result now carries:
  - `volume_ratio_10`, `volume_ratio_20`
  - `resistance_20`, `resistance_60`
  - `breakout_price_20`, `breakout_price_60`
  - `retest_zone_low`, `retest_zone_high`
- Volume state now uses V10/V20 context.
- Acute rebound cards show concrete zone and V10/V20.
- If current price is below the zone, report says `突破區 ...（現價未站回）`.
- Acute rebound remains wait/no-chase; no buyability loosening.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py::GeneratorReportTest::test_v21_1_strong_rebound_uses_multi_window_retest_context tests/test_generator_report.py::GeneratorReportTest::test_v21_1_retest_anchor_says_breakout_zone_when_price_is_below_zone tests/test_analysis_engine.py::AnalysisEngineTest::test_v21_1_snapshot_exports_multi_window_volume_and_retest_zone -q --tb=short
```

Result: `3 passed`.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_analysis_engine.py tests/test_signal_validator.py tests/test_trade_state_machine.py tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_backfill_signals.py tests/test_backfill_daily_price_history.py -q --tb=short
```

Result: `307 passed, 149 warnings, 57 subtests passed`.

Official dry-run:
- `VERSION v21.1`
- `messages 4`
- no live Telegram delivery.
- 旺宏 card shows `突破區 175.5~176.38（現價未站回）`.
- 旺宏 card shows `V10 0.52x / V20 0.26x偏弱`.

## Next Action

- Observe next Render/GitHub scheduled report if external confirmation is needed.
