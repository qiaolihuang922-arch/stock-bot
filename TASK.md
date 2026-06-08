# TASK: render_git_tg_db_pipeline_check_20260609

## Status
- task_id: `render_git_tg_db_pipeline_check_20260609`
- type: `risk_patch`
- status: `QA passed, pending commit/push`
- version: `v21.0`
- QA level: `L3`

## Owner Problem
Owner asked to check whether the Render -> git/GitHub -> Telegram report chain is broken, and whether the daily database writes are working.

## User Visible Result
- Render dispatch now targets the existing GitHub workflow file.
- GitHub daily evidence workflow no longer blocks daily market-theme DB writes when `MARKET_THEME_APPROVED_PAYLOAD` is absent; it falls back to the existing TWSE official payload builder.
- Telegram delivery path remains guarded: failed sends do not mark sent, and no live Telegram delivery was run in this task.
- Official report dry-run still generates the v21.0 message list.

## Non Goals
- No live Telegram delivery.
- No DB schema/RLS/grant/policy/index change.
- No manual SQL/DML.
- No strategy or state-machine logic changes.

## Impacted Modules And Consumers
- `app.py`: Render web trigger dispatch URL.
- `.github/workflows/stock-bot-clean.yml`: daily evidence runner command.
- `tests/test_app_render_preflight.py`: Render dispatch URL regression.
- `tests/test_workflow_runtime_config.py`: workflow command contract.
- `tests/test_phase3_evidence_automation.py`: cross-platform CLI path assertion.
- Direct consumers: Render web app, GitHub Actions workflow dispatch/schedule, Telegram sender, daily DB write scripts.

## Output Contract
- Render must dispatch `.github/workflows/stock-bot-clean.yml`.
- `run_mode=daily_evidence` must skip live bot delivery.
- Daily evidence must run `scripts/run_phase3_evidence_automation.py`; if an approved payload secret exists, use it; otherwise use the script's official TWSE payload path.
- `generate_report(dry_run=True)` must not write DB and must return empty `write_results`.

## Acceptance
- Render/TG/DB focused tests pass.
- Workflow static contract tests pass.
- Official dry-run returns messages and no write results.
- Production DB read-after-write shows current daily rows for `daily_price`, `signal_runs`, `daily_signal_snapshot`, and market-theme evidence tables.

## Failure Specimen And Route
- Found failure: `app.py` dispatched `stock-bot.yml`, but the repo workflow file is `stock-bot-clean.yml`.
- Found daily DB gap: market-theme confirmed evidence was present through 2026-06-03 only before freshness backfill; approved repo script backfilled and verified 2026-06-04, 2026-06-05, and 2026-06-08.

## Forbidden / Blocking
- No live Telegram delivery.
- Do not print secrets.
- Do not hand-write production DML.
- If git completion gate fails, do not claim complete.
