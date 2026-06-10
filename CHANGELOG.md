# CHANGELOG: report_state_denoise_followup_20260610

## Changes
- `core/trade_state_machine.py`
  - Added `WAIT_APPROACH` / `等接近` for unheld symbols that are too far from trigger.
  - Added `APPROACH_TRIGGER` and `APPROACH_GATE_FAILED`.
  - Visible state line now keeps market weakness as background when the primary state is a stock-specific gate.
- `core/generator.py`
  - Routes far no-setup unheld symbols to `等接近`.
  - Added `等接近` to funnel groups, tracking counts, summary buckets, conflict scan, and tomorrow trigger text.
- `presentation/report.py`
  - Added `等接近` card/title support.
  - Added `買點：不買，等接近觸發區`.
  - Reworded distance gap so `<=4%` is explicitly a breakout-strategy gate, while trend continuation/pullback requires a separate valid setup.
  - Keeps market weakness as a secondary background note when distance/setup is the primary blocker.
- `core/future_watch.py`
  - Downgrades TWSE historical analogy below 60% to `低相似，不作主結論`.
  - Filters empty low-similarity lines and leaves blank lines between fundamentals stocks.
- Tests
  - Updated unheld official-message and state-machine expectations.
  - Added low-similarity historical analogy regression.
  - Added fundamentals blank-line regression.

## Contract Impact
- User-visible Telegram report wording changed.
- New unheld visible state label: `等接近`.
- No payload shape, DB contract, live delivery, or revenue/EPS calculation change.
- No non-actionable target is upgraded to `可買`.

## Verification
- Generator + state machine:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py tests/test_trade_state_machine.py -q --tb=short
  ```
  Result: `203 passed, 145 warnings, 44 subtests passed`.
- Strategy / evidence / volume related:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_analysis_engine.py tests/test_strategy_evidence.py tests/test_volume_calibration.py tests/test_market_theme_evidence.py -q --tb=short
  ```
  Result: `94 passed, 1 warning, 13 subtests passed`.
- Official dry-run:
  ```powershell
  $env:PYTHONIOENCODING='utf-8'
  .\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages,_=generate_report(dry_run=True); print('messages', len(messages))"
  ```
  Result: `messages 4`; checked unheld, summary, history analogy, and fundamentals spacing. No live Telegram delivery.

## Coverage Layers
- Formatter: `presentation/report.py`, `format_future_watch_message()`.
- State machine: `core/trade_state_machine.py`.
- Official generator: `generate_report(dry_run=True)`.
- Adjacent strategy/volume/evidence test paths.

## Residual Risk
- Runtime source values can still differ by official data availability; this patch does not change data freshness or source fallback rules.
- The current market remains non-actionable for new entries; `等接近` is clearer tracking, not a buy signal.
