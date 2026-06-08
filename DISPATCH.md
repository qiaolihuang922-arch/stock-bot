# DISPATCH.md

## Active

- task_md_holds: `render_git_tg_db_pipeline_check_20260609`
- status: `complete`
- owner_request:
  - Check Render -> git/GitHub -> TG report chain.
  - Check daily DB writes.
  - No live Telegram delivery.

## Current Result

- Version remains `v21.0`.
- Render dispatch URL was broken and is fixed to `stock-bot-clean.yml`.
- Daily evidence workflow no longer requires `MARKET_THEME_APPROVED_PAYLOAD`; it can use official TWSE payload generation.
- Market-theme DB freshness gap was backfilled by the approved repo script for 2026-06-04, 2026-06-05, and 2026-06-08.
- Official dry-run report returns 4 messages and `write_results {}`.
- No live Telegram delivery was run.

## Recently Done

- `render_git_tg_db_pipeline_check_20260609`: Render dispatch fixed, daily evidence workflow unblocked, market-theme DB freshness backfilled/verified, dry-run and guard tests passed, no live Telegram delivery.
- `unheld_transition_table_replay_20260608`: v21.0 unheld transition-table FSM implemented, replayed locally, regression-tested, dry-run verified, no live Telegram delivery.

## Verification

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -m pytest tests/test_workflow_runtime_config.py::WorkflowRuntimeConfigTest::test_workflow_dispatch_supports_git_runner_may_backfill tests/test_workflow_runtime_config.py::WorkflowRuntimeConfigTest::test_workflow_does_not_echo_service_role_secret_value -q --tb=short
```

Result: `2 passed, 1 warning`.

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -m pytest tests/test_app_render_preflight.py tests/test_main_delivery_guard.py tests/test_notifier.py tests/test_daily_snapshot_store.py tests/test_phase3_evidence_automation.py tests/test_market_theme_evidence.py tests/test_market_theme_evidence_handoff.py tests/test_strategy_evidence.py tests/test_cross_day_context.py -q --tb=short
```

Result: `142 passed, 1 warning, 64 subtests passed`.

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages, reply_markup, writes = generate_report(dry_run=True, return_write_results=True); print('messages', len(messages)); print('reply_markup', bool(reply_markup)); print('write_results', writes)"
```

Result: `messages 4`, `reply_markup True`, `write_results {}`.

## Fixed Commands

Local dry-run only:

```powershell
cd D:\reserch\stock-bot
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages, _ = generate_report(dry_run=True); print('\\n--- MESSAGE ---\\n'.join(messages))"
```

## Next Action

- Owner review of Render/GitHub/TG/DB pipeline check result.
