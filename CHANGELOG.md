# CHANGELOG: render_git_tg_db_pipeline_check_20260609

## Changes
- `app.py`
  - Fixed Render dispatch URL from nonexistent `stock-bot.yml` to existing `stock-bot-clean.yml`.
- `.github/workflows/stock-bot-clean.yml`
  - Removed the unconditional `--require-market-theme-payload` blocker from the daily evidence step.
  - Preserved optional `MARKET_THEME_APPROVED_PAYLOAD` support.
  - Allows the existing official TWSE payload builder to run when the secret is absent.
- `tests/test_app_render_preflight.py`
  - Added regression coverage that Render dispatch targets `stock-bot-clean.yml`.
- `tests/test_workflow_runtime_config.py`
  - Updated workflow command contract for optional market-theme payload.
- `tests/test_phase3_evidence_automation.py`
  - Made the write CLI path assertion cross-platform.

## Contract Impact
- Render -> GitHub workflow dispatch is repaired.
- Daily evidence no longer depends on a static market-theme payload secret for normal TWSE official writes.
- Telegram delivery behavior is unchanged; failed delivery still prevents `mark_sent`.
- No DB schema or direct DML change.

## Verification
- Command:
  ```powershell
  $env:PYTHONIOENCODING='utf-8'
  .\.venv\Scripts\python.exe -m pytest tests/test_workflow_runtime_config.py::WorkflowRuntimeConfigTest::test_workflow_dispatch_supports_git_runner_may_backfill tests/test_workflow_runtime_config.py::WorkflowRuntimeConfigTest::test_workflow_does_not_echo_service_role_secret_value -q --tb=short
  ```
- Result: `2 passed, 1 warning`.
- Command:
  ```powershell
  $env:PYTHONIOENCODING='utf-8'
  .\.venv\Scripts\python.exe -m pytest tests/test_app_render_preflight.py tests/test_main_delivery_guard.py tests/test_notifier.py tests/test_daily_snapshot_store.py tests/test_phase3_evidence_automation.py tests/test_market_theme_evidence.py tests/test_market_theme_evidence_handoff.py tests/test_strategy_evidence.py tests/test_cross_day_context.py -q --tb=short
  ```
- Result: `142 passed, 1 warning, 64 subtests passed`.
- Command:
  ```powershell
  $env:PYTHONIOENCODING='utf-8'
  .\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages, reply_markup, writes = generate_report(dry_run=True, return_write_results=True); print('messages', len(messages)); print('reply_markup', bool(reply_markup)); print('write_results', writes)"
  ```
- Result: `messages 4`, `reply_markup True`, `write_results {}`.
- Production DB read-after-write:
  - `market_theme_confirmed_evidence`: 2026-06-02/03/04/05/08 each 9 rows.
  - `market_theme_index_daily_bars`: 2026-06-02/03/04/05/08 each 10 rows.
  - `daily_price`: 2026-06-02/03/04/05/08 each 12 rows.
  - `signal_runs`: 2026-06-02/03/04/05/08 each 1 row.
  - `daily_signal_snapshot`: rows present through 2026-06-08.

## Coverage Layers
- Render helper route: tested with Flask client and mocked GitHub dispatch.
- GitHub workflow contract: static workflow tests.
- Telegram delivery: notifier and main delivery guard tests.
- Daily DB payload/write guard: daily snapshot, phase3 evidence, market-theme, strategy evidence, cross-day tests.
- Official generator: dry-run report generated, no DB writes.

## Residual Risk
- The local Windows Bash environment drops env vars in some shell-fragment tests; static workflow contract tests and Python-level evidence tests were used for this local verification.
- Render/GitHub live dispatch was not executed.
- Live Telegram delivery was not executed.
