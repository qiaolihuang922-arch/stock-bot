# CHANGELOG: latest_revenue_month_fallback_20260610

## Changes
- `core/future_watch.py`
  - Added `_roc_year_month_candidates` to generate latest-to-older monthly revenue candidates.
  - Updated MOPS target revenue refresh to try candidate months in order and use the first available official row.
  - Added normalized ASCII revenue row support (`stock_code`, `revenue_month`, `revenue_yoy`) before the legacy source-key merge.
- `tests/test_generator_report.py`
  - Added a regression test for a July run where June revenue is unavailable and May is selected automatically.
  - Updated MOPS mock rows to use normalized keys.

## Contract Impact
- Revenue freshness is now month-rolling: no code change is needed when the calendar moves to the next month.
- If the latest theoretical month is unpublished, the report falls back to the newest official month it can fetch.
- Existing fail-closed behavior remains: no official row means no fabricated revenue.
- No DB schema, write path, or live delivery behavior changed.

## Verification
- Command:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py::GeneratorReportTest::test_future_watch_refreshes_stale_openapi_revenue_with_mops_month tests/test_generator_report.py::GeneratorReportTest::test_future_watch_revenue_fallback_uses_latest_available_month -q --tb=short
  ```
- Result: `2 passed, 1 warning`.
- Command:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py tests/test_trade_state_machine.py -q --tb=short
  ```
- Result: `199 passed, 145 warnings, 44 subtests passed`.
- Official dry-run:
  - `messages 4`
  - `elapsed_seconds 58.3`
  - `has_unheld_history_noise False`
  - No live Telegram delivery.

## Coverage Layers
- Collector/helper: latest-to-older MOPS revenue month fallback.
- Formatter/generator: full generator report suite.
- Official generator: `generate_report(dry_run=True)`.

## Residual Risk
- MOPS can still time out; timeout remains fail-closed.
- Candidate stocks may omit revenue if all candidate month fetches fail.
