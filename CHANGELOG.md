# CHANGELOG: report_revenue_noise_fsm_20260610

## Changes
- `core/future_watch.py`
  - Added MOPS company monthly revenue fallback for stale TWSE/TPEX OpenAPI monthly revenue.
  - Added previous-month ROC calculation, MOPS HTML parsing, retry, and concurrent target refresh.
  - Reduced MOPS fallback latency by skipping the slow/stale TWSE listed-revenue bulk endpoint, using 3-second MOPS target fetches with limited concurrency, and adding a 2-second small retry for missed priority rows.
  - `collect_target_fundamentals` now records expected revenue month and refreshed codes.
- `core/trade_state_machine.py`
  - Added next-event labels for unheld FSM states.
  - Unheld visible state line now reports `還差` / `下一步` instead of repeating trigger text.
- `presentation/report.py`
  - Treats both `盤後` and `收盤` as after-hours card context.
  - Hides cross-day history detail lines on closing/after-hours unheld cards.
  - Uses the explicit `report_phase` argument for unheld card after-hours decisions.
- `tests/test_generator_report.py`
  - Added stale OpenAPI revenue -> MOPS 2026/05 fallback regression.
  - Added closing unheld card history-noise regression.
- `tests/test_trade_state_machine.py`
  - Updated v21 unheld state-line expectation.

## Contract Impact
- Future-watch target fundamentals can show newer MOPS monthly revenue than the bulk OpenAPI source when the OpenAPI source lags.
- If MOPS times out or returns no row for a target, the report keeps the prior official OpenAPI value rather than inventing data.
- Telegram unheld cards remain grouped the same way, but closing/after-hours detail is shorter.
- No DB schema, write path, or live delivery behavior changed.

## Verification
- Command:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py tests/test_trade_state_machine.py -q --tb=short
  ```
- Result: `198 passed, 145 warnings, 44 subtests passed`.
- Command:
  ```powershell
  $env:PYTHONIOENCODING='utf-8'
  .\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages,_=generate_report(dry_run=True); print(len(messages)); print('歷史噪音', '歷史：前次 observe' in '\\n'.join(messages) or '連續觀察 1 天' in '\\n'.join(messages))"
  ```
- Result: `4`, `歷史噪音 False`.
- Official dry-run spot check:
  - Unheld cards show `還差：量能確認` / `還差：回測確認`.
  - Future watch shows 2026/05 revenue for all holding rows in the latest dry-run.
  - Candidate rows can show EPS only when MOPS times out; the report does not fabricate May revenue.
  - Latest timed dry-run completed in about 55-59 seconds.

## Coverage Layers
- Helper/collector: MOPS stale revenue fallback test.
- Formatter: closing unheld card history-noise test.
- Official generator: `generate_report(dry_run=True)` message-list replay.
- State machine: visible unheld line regression.

## Residual Risk
- MOPS company monthly revenue is slow and can time out per target; the fallback is best-effort, short-timeout, and fail-closed.
- Some candidate rows may show EPS only when MOPS times out.
- Live Telegram delivery was not executed.
