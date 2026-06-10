# CHANGELOG: unheld_market_overlay_version_20260610

## Changes
- `core/generator.py`
  - Bumped visible report `VERSION` from `v21.0` to `v21.0.1`.
  - Moved `市場弱` attribution after stock-specific gates in `tomorrow_watch_state()`.
  - Result: market weakness remains a blocker/background, but it does not hide setup/volume/RR/heat gates.
- `core/trade_state_machine.py`
  - Bumped FSM artifact schema version to `v21.0.1`.
- Tests
  - Updated visible version expectations to `v21.0.1`.
  - Updated the v21 weak-market failure specimen to expect `等型態｜市場弱`, not all `等市場`.

## Problem Analysis
- Previous v21.0.1-pre logic returned immediately when `市場弱` appeared in blockers.
- That made every unheld card look the same: `等市場｜市場弱`.
- It was technically fail-closed, but too coarse for decision reading because the user could not see whether the stock itself was missing setup, volume, RR, or cooling.

## Contract Impact
- Weak market still blocks new buy actions.
- Card primary state now reflects the stock-specific next gate when one exists.
- Current dry-run unheld summary changed from `僅追蹤 7（等市場）` to `僅追蹤 7（等型態）`.
- No DB schema/write path/live Telegram behavior changed.

## Verification
- Targeted:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py::GeneratorReportTest::test_v21_0_1_far_low_volume_weak_market_waits_setup_not_market_or_volume tests/test_trade_state_machine.py::TradeStateMachineTest::test_report_cards_include_trade_state_line -q --tb=short
  ```
  Result: `2 passed, 5 warnings`.
- Broad:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py tests/test_trade_state_machine.py tests/test_analysis_engine.py tests/test_strategy_evidence.py tests/test_volume_calibration.py tests/test_market_theme_evidence.py -q --tb=short
  ```
  Result: `296 passed, 145 warnings, 57 subtests passed`.
- Official dry-run:
  - `messages 4`
  - headers show `v21.0.1`
  - unheld summary: `未持倉 7｜僅追蹤 7（等型態）`
  - no live Telegram delivery.

## Coverage Layers
- Helper/state priority: `tomorrow_watch_state()`.
- Formatter/generator: visible unheld cards and summary.
- Official generator: `generate_report(dry_run=True)`.

## Residual Risk
- This improves visible attribution only. It does not yet add adaptive per-stock thresholds from the calibration artifact into live strategy scoring.
