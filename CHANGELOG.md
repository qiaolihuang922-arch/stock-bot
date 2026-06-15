# CHANGELOG: premarket_phase_report_v21_0_6_20260615

## Changes
- `core/generator.py`
  - Bumped visible version to `v21.0.6`.
  - Changed weekday pre-open phase from `非交易` to `盤前`.
  - Added `is_today_action_phase()` and `today_trigger_label()`.
  - Included `盤前` in today-action summary helpers.
  - Preserved existing `盤中` wording.
- `presentation/report.py`
  - Added formatter-level today-action helper.
  - Uses `今日盤前風控計畫` heading for premarket action blocks.
  - Uses `盤前觀察` for premarket unheld trigger labels.
  - Prevents `盤前` from falling into `明日計畫` summary routing.
- Tests updated to `v21.0.6`.

## Contract Impact
- Telegram header can now show `盤前`.
- `盤前` reports are treated as today-action reports, not afterhours reports.
- No DB payload, schema, RLS, grant, policy, role, live delivery, or production write change.

## Verification
- Targeted phase tests:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py::GeneratorReportTest::test_v21_0_6_trading_day_before_open_is_pre_market_not_non_trading tests/test_generator_report.py::GeneratorReportTest::test_v21_0_6_pre_market_summary_uses_today_plan_not_tomorrow_plan -q --tb=short
  ```
  Result: `2 passed`.
- Targeted report/state/evidence suite:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_trade_state_machine.py tests/test_generator_report.py tests/test_market_theme_evidence.py -q --tb=short
  ```
  Result: `248 passed, 147 warnings, 57 subtests passed`.
- Official dry-run probe with patched 2026-06-15 08:00 time:
  - Headers render as `【06/15 盤前｜v21.0.6】`.
  - `phase 盤前`.
  - no `非交易` header.
  - no `明日計畫`.

## Coverage Layers
- Phase helper.
- Telegram summary formatter.
- Official generator dry-run.
- Existing report/state/evidence regression suite.

## Residual Risk
- No live Telegram delivery was performed.
- Holiday confirmation is still handled separately by existing weekend / source evidence logic; this patch only fixes trading-day pre-open phase semantics.
