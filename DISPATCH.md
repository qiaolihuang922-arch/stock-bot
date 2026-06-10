# DISPATCH.md

## Active

- task_md_holds: `latest_revenue_month_fallback_20260610`
- status: `complete`
- owner_request:
  - Make revenue fetch latest available automatically.
  - Avoid monthly code changes.
  - No live Telegram delivery.

## Current Result

- Version remains `v21.0`.
- MOPS monthly revenue fallback now tries latest-to-older candidate months automatically.
- A July run can try `11506` first and fall back to `11505` if June has not published.
- Normalized revenue row keys are supported so internal adapters/tests do not depend on fragile Chinese/mojibake column names.
- Official dry-run generated 4 messages in about 58 seconds and did not run live Telegram delivery.
- Commit `66658e1` pushed to `origin/main`; equivalent git completion check passed (`HEAD == origin/main`).

## Recently Done

- `latest_revenue_month_fallback_20260610`: latest available revenue month fallback implemented and tested.
- `report_revenue_noise_fsm_20260610`: MOPS revenue freshness fallback, closing-card denoise, and unheld FSM visible-line improvement.
- `render_git_tg_db_pipeline_check_20260609`: Render dispatch fixed, daily evidence workflow unblocked, market-theme DB freshness backfilled/verified, dry-run and guard tests passed, no live Telegram delivery.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py::GeneratorReportTest::test_future_watch_refreshes_stale_openapi_revenue_with_mops_month tests/test_generator_report.py::GeneratorReportTest::test_future_watch_revenue_fallback_uses_latest_available_month -q --tb=short
```

Result: `2 passed, 1 warning`.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py tests/test_trade_state_machine.py -q --tb=short
```

Result: `199 passed, 145 warnings, 44 subtests passed`.

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -c "from core.generator import generate_report; from time import perf_counter; s=perf_counter(); messages,_=generate_report(dry_run=True); print('messages', len(messages)); print('elapsed_seconds', round(perf_counter()-s,2))"
```

Result: `messages 4`, `elapsed_seconds 58.3`.

## Fixed Commands

Local dry-run only:

```powershell
cd D:\reserch\stock-bot
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages, _ = generate_report(dry_run=True); print('\\n--- MESSAGE ---\\n'.join(messages))"
```

## Next Action

- Owner review of latest revenue month fallback.
