# CHANGELOG: entry_distance_strategy_v21_0_4_20260611

## Changes
- `core/generator.py`
  - Bumped visible version to `v21.0.4`.
  - Added `entry_distance_policy()` and `distance_blocks_entry()`.
  - Breakout/pre-breakout entries use `<=5%`.
  - Base-reversal gets its own wider observation policy.
  - Pullback reclaim and trend continuation are not blocked by breakout distance alone.
  - Kept far-without-setup as non-actionable wait/approach logic.
- `core/trade_state_machine.py`
  - Added matching distance policy helpers.
  - `TOO_FAR_FROM_TRIGGER` now applies only when the setup type has a distance hard gate.
  - Added tests to prove far pullback/trend-continuation are not blocked by pivot distance alone.
- `presentation/report.py`
  - Replaced `突破策略需<=4%` display with strategy-specific `突破買點區需<=5%`.
  - Added display policy helper for gap text.
  - Suppressed conflicting `交易狀態：等資料` line on rejected/source-failed cards when the card's main action is already non-actionable.
- Tests updated to `v21.0.4` and new distance wording.

## Contract Impact
- Telegram visible version changes to `v21.0.4`.
- Unheld gap wording changes from a universal 4% rule to strategy-specific 5% breakout buy-zone wording.
- State machine guard semantics change:
  - `TOO_FAR_FROM_TRIGGER` no longer applies to pullback reclaim / trend continuation solely because breakout distance is high.
- No DB schema or payload shape change.

## Verification
- Combined report/state/evidence:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py tests/test_trade_state_machine.py tests/test_market_theme_evidence.py -q --tb=short
  ```
  Result: `246 passed, 145 warnings, 57 subtests passed`.
- Official dry-run:
  ```powershell
  .\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages,_=generate_report(dry_run=True); print('\n\n--- MESSAGE ---\n\n'.join(messages))"
  ```
  Checked: `v21.0.4`, no old `<=4%` wording, no old execution wording, no rejected/data-state conflict.

## Coverage Layers
- Research-informed policy.
- State machine guard.
- Official Telegram formatter.
- Official generator dry-run.

## Residual Risk
- This is still rule-based strategy logic, not a learned optimizer.
- Exact live report classifications may move during market hours as prices update.
- Live Telegram delivery was intentionally not tested.
