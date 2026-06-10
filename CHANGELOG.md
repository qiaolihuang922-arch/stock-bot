# CHANGELOG: future_watch_source_and_card_denoise_20260610

## Changes
- `core/future_watch.py`
  - Added retry support to `_request_get_json()`.
  - TWSE historical source now retries transient API failures.
  - Historical source-error line now states official TWSE is unreadable instead of implying no similar sample.
  - Added TWSE listed-company monthly revenue OpenAPI to fundamentals source loading.
- `presentation/report.py`
  - Compact wait cards for non-actionable `等接近` / `等型態`.
  - `等接近` gap wording is shorter and no longer repeats quality/market secondary gates.
  - Suppresses low-signal market, data, and RR/backtest basis lines for compact wait cards.
- `core/generator.py`
  - Bumped visible report version to `v21.0.2`.
- Tests
  - Added TWSE retry regression.
  - Added source-error wording regression.
  - Added TWSE listed revenue OpenAPI regression.
  - Synced visible report version snapshots to `v21.0.2`.

## Contract Impact
- Telegram report text changes.
- Fundamentals source coverage expanded from TPEX revenue only to TWSE + TPEX revenue.
- State-machine schema version remains `v21.0.1`; only visible report version is `v21.0.2`.
- No DB contract, payload shape, live delivery, or buy/sell decision change.

## Verification
- Generator + state machine:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py tests/test_trade_state_machine.py -q --tb=short
  ```
  Result: `206 passed, 145 warnings, 44 subtests passed`.
- Adjacent strategy / evidence / volume / theme:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_market_theme_evidence.py tests/test_analysis_engine.py tests/test_strategy_evidence.py tests/test_volume_calibration.py tests/test_market_theme_evidence.py -q --tb=short
  ```
  Result: `94 passed, 1 warning, 13 subtests passed`.
- Official dry-run:
  - `messages 4`.
  - Header shows `v21.0.2`.
  - First `等接近` card is compact and non-actionable.
  - Future-watch confirms historical source route and 2303 / 2301 2026/05 revenue.
  - No live Telegram delivery.

## Coverage Layers
- Source helper: TWSE retry and listed revenue OpenAPI.
- Formatter: compact unheld card.
- Official generator: dry-run visible report.

## Residual Risk
- External TWSE/MOPS APIs can still fail; failure remains fail-closed and visible as source unavailable.
- MOPS法說會 parsing remains fail-closed when official page is not parseable.
