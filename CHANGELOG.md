# CHANGELOG: report_noise_conflict_v21_0_3_20260611

## Changes
- `core/generator.py`
  - Bumped visible version to `v21.0.3`.
  - Renamed intraday summary/detail wording from `交易執行` to `風控建議`.
  - Updated report integrity check to accept the new wording.
  - Added `等資料` to unheld funnel/tracking buckets, but only when `tomorrow_watch_state` already returns `等資料`.
- `presentation/report.py`
  - Summary heading now renders `今日盤中風控建議`.
  - Direct risk cards suppress low-signal `條件` and `數據` lines while preserving decision/reason/next step.
  - Source-wait unheld cards align title/action/buy line with `等資料` only when the state machine says data recovery is the blocker.
  - Compact rejected cards no longer force low-value trade-state/evidence lines when source is otherwise usable.
- `core/future_watch.py`
  - Historical analogy now adds a medium-confidence limitation when volume data is unavailable.
- Tests updated to enforce the new mobile-reading contract and `v21.0.3`.

## Contract Impact
- Telegram message wording changes:
  - `今日盤中交易執行` -> `今日盤中風控建議`
  - detail index `交易執行 N` -> `風控建議 N`
- No DB payload shape change.
- No DB schema change.
- No live delivery path change.

## Verification
- Report tests:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py -q --tb=short
  ```
  Result: `199 passed, 143 warnings, 44 subtests passed`.
- Combined report/state/evidence:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py tests/test_trade_state_machine.py tests/test_market_theme_evidence.py -q --tb=short
  ```
  Result: `244 passed, 145 warnings, 57 subtests passed`.
- Official dry-run:
  ```powershell
  .\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages,_=generate_report(dry_run=True); print('\n\n--- MESSAGE ---\n\n'.join(messages))"
  ```
  Checked: `v21.0.3`, new risk-advice wording, no old execution wording, historical confidence note present.

## Coverage Layers
- Formatter: card and summary wording.
- Official generator: full message list dry-run.
- Trade state/funnel interaction.
- Future-watch historical analogy.
- Market evidence artifact compatibility.

## Residual Risk
- Dry-run uses current live/read-only sources, so prices and some unheld classifications may move during market hours.
- Live Telegram delivery was intentionally not tested.
