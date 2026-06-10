# DISPATCH.md

## Active

- task_md_holds: `future_watch_fundamental_layout_20260610`
- status: `complete`
- owner_request:
  - Reformat `關注標的財報` to multi-line per stock.
  - Remove `關注原因` from that fundamentals block.
  - No live Telegram delivery.

## Current Result

- `關注標的財報` now renders as:
  - `code name`
  - `EPS ...`
  - `營收 ...`
- `關注原因` is removed from the fundamentals block only.
- No EPS/revenue source or calculation change.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py::GeneratorReportTest::test_future_watch_refreshes_stale_openapi_revenue_with_mops_month tests/test_generator_report.py::GeneratorReportTest::test_future_watch_revenue_fallback_uses_latest_available_month tests/test_generator_report.py::GeneratorReportTest::test_future_watch_revenue_fallback_never_downgrades_existing_month tests/test_generator_report.py::GeneratorReportTest::test_future_watch_revenue_fallback_does_not_use_revenue_amount_as_yoy tests/test_generator_report.py::GeneratorReportTest::test_future_watch_revenue_fallback_does_not_show_too_old_month -q --tb=short
```

Result: `5 passed, 1 warning`.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py -q --tb=short
```

Result: `195 passed, 143 warnings, 44 subtests passed`.

Official dry-run checked the `關注標的財報` block; no live Telegram delivery.

## Fixed Commands

Local dry-run only:

```powershell
cd D:\reserch\stock-bot
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages, _ = generate_report(dry_run=True); print('\n--- MESSAGE ---\n'.join(messages))"
```

## Next Action

- Owner review of fundamentals block layout.
