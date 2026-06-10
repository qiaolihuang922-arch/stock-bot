# CHANGELOG: future_watch_fundamental_layout_20260610

## Changes
- `core/future_watch.py`
  - Changed `關注標的財報` rows from one-line pipe-separated output to multi-line per stock.
  - Split `fundamentals_label` by `｜` and renders each part on its own line.
  - Removed `關注原因` from the fundamentals block.
- `tests/test_generator_report.py`
  - Updated fundamentals layout assertions.
  - Added block-scoped assertion that `關注原因：` is absent from `關注標的財報`.

## Contract Impact
- Only Telegram text layout changed.
- EPS/revenue values, collectors, source fallbacks, DB reads/writes, and version remain unchanged.

## Verification
- Targeted:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py::GeneratorReportTest::test_future_watch_refreshes_stale_openapi_revenue_with_mops_month tests/test_generator_report.py::GeneratorReportTest::test_future_watch_revenue_fallback_uses_latest_available_month tests/test_generator_report.py::GeneratorReportTest::test_future_watch_revenue_fallback_never_downgrades_existing_month tests/test_generator_report.py::GeneratorReportTest::test_future_watch_revenue_fallback_does_not_use_revenue_amount_as_yoy tests/test_generator_report.py::GeneratorReportTest::test_future_watch_revenue_fallback_does_not_show_too_old_month -q --tb=short
  ```
  Result: `5 passed, 1 warning`.
- Full generator:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py -q --tb=short
  ```
  Result: `195 passed, 143 warnings, 44 subtests passed`.
- Official dry-run:
  - `關注標的財報` block renders each target as three lines where EPS and revenue are available.
  - No live Telegram delivery.

## Coverage Layers
- Formatter: `format_future_watch_message()`.
- Official generator dry-run: future-watch block extraction.

## Residual Risk
- Some values may still be omitted if official source data is unavailable; this patch intentionally does not change data availability rules.
