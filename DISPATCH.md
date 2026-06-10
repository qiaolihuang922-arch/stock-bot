# DISPATCH.md

## Active

- task_md_holds: `revenue_fallback_no_downgrade_20260610`
- status: `complete`
- owner_request:
  - Analyze incorrect revenue output in the pasted v21.0 report.
  - Fix old-month downgrade and impossible revenue YoY values.
  - No live Telegram delivery.

## Current Result

- Version remains `v21.0`.
- Revenue fallback now rejects older MOPS months when an existing newer month is present.
- Revenue fallback no longer treats revenue amount as YoY percentage.
- 2026/06 runs only accept 2026/05 or 2026/04 revenue; older months are omitted.
- Official dry-run generated 4 messages and did not run live Telegram delivery.
- Official dry-run check: `bad_large_pct False`, `too_old False`.

## Recently Done

- `revenue_fallback_no_downgrade_20260610`: fixed revenue downgrade and amount-as-YoY errors.
- `latest_revenue_month_fallback_20260610`: latest available revenue month fallback implemented and tested.
- `report_revenue_noise_fsm_20260610`: MOPS revenue freshness fallback, closing-card denoise, and unheld FSM visible-line improvement.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py::GeneratorReportTest::test_future_watch_refreshes_stale_openapi_revenue_with_mops_month tests/test_generator_report.py::GeneratorReportTest::test_future_watch_revenue_fallback_uses_latest_available_month tests/test_generator_report.py::GeneratorReportTest::test_future_watch_revenue_fallback_never_downgrades_existing_month tests/test_generator_report.py::GeneratorReportTest::test_future_watch_revenue_fallback_does_not_use_revenue_amount_as_yoy tests/test_generator_report.py::GeneratorReportTest::test_future_watch_revenue_fallback_does_not_show_too_old_month -q --tb=short
```

Result: `5 passed, 1 warning`.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py tests/test_trade_state_machine.py -q --tb=short
```

Result: `202 passed, 145 warnings, 44 subtests passed`.

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -c "from core.generator import generate_report; from time import perf_counter; s=perf_counter(); messages,_=generate_report(dry_run=True); joined='\\n'.join(messages); print('messages', len(messages)); print('elapsed_seconds', round(perf_counter()-s,2)); print('bad_large_pct', any(x in joined for x in ['+6255653.0%', '+290183471.0%', '+20647675.0%'])); print('too_old', any(x in joined for x in ['營收 2026/03', '營收 2026/02']))"
```

Result: `messages 4`, `elapsed_seconds 68.47`, `bad_large_pct False`, `too_old False`.

## Fixed Commands

Local dry-run only:

```powershell
cd D:\reserch\stock-bot
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages, _ = generate_report(dry_run=True); print('\\n--- MESSAGE ---\\n'.join(messages))"
```

## Next Action

- Commit/push current patch and run git completion gate.
