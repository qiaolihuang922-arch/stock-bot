# CHANGELOG: revenue_fallback_no_downgrade_20260610

## Changes
- `core/future_watch.py`
  - Added normalized `stock_code` / `revenue_month` to fetched MOPS rows before merge.
  - Added revenue refresh guard: only newer revenue months can overwrite existing values.
  - Limited month candidates to latest completed month plus one fallback month.
  - Added safe YoY fallback extraction that prefers percentage-like values and avoids large revenue amounts.
- `tests/test_generator_report.py`
  - Added regressions for:
    - stale OpenAPI refresh to MOPS month,
    - latest available month fallback,
    - never downgrading existing month,
    - not using revenue amount as YoY,
    - not showing too-old fallback months.

## Contract Impact
- Future-watch revenue is now conservative: newest official data wins, older rows cannot replace newer rows.
- Too-old revenue rows are omitted rather than shown.
- No DB schema, write path, or live delivery behavior changed.

## Verification
- Command:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py::GeneratorReportTest::test_future_watch_refreshes_stale_openapi_revenue_with_mops_month tests/test_generator_report.py::GeneratorReportTest::test_future_watch_revenue_fallback_uses_latest_available_month tests/test_generator_report.py::GeneratorReportTest::test_future_watch_revenue_fallback_never_downgrades_existing_month tests/test_generator_report.py::GeneratorReportTest::test_future_watch_revenue_fallback_does_not_use_revenue_amount_as_yoy tests/test_generator_report.py::GeneratorReportTest::test_future_watch_revenue_fallback_does_not_show_too_old_month -q --tb=short
  ```
- Result: `5 passed, 1 warning`.
- Command:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py tests/test_trade_state_machine.py -q --tb=short
  ```
- Result: `202 passed, 145 warnings, 44 subtests passed`.
- Official dry-run:
  - `messages 4`
  - `elapsed_seconds 68.47`
  - `bad_large_pct False`
  - `too_old False`
  - No live Telegram delivery.

## Coverage Layers
- Collector/helper: revenue month guard and YoY extraction.
- Formatter/generator: future-watch fundamentals block.
- Official generator: `generate_report(dry_run=True)`.

## Residual Risk
- MOPS can still time out; timeout remains fail-closed.
- Some candidate rows may omit revenue if MOPS cannot provide latest or one-month fallback.
