# TASK: render_dispatch_writeback_logic_20260610

## Status
- task_id: `render_dispatch_writeback_logic_20260610`
- type: `risk_patch`
- status: `complete`
- version: `v21.0.2`
- QA level: `L2`

## Owner Problem
Owner corrected the workflow model: production is Render polling every five minutes and dispatching GitHub workflow runs; GitHub Actions is not the primary scheduler. The previous fix incorrectly moved GitHub cron times and missed the Render stop-after-close logic.

## User Visible Result
- Render remains the scheduler/dispatcher.
- GitHub workflow is dispatch-only and no longer has native cron.
- Render intraday tags now use five-minute buckets.
- Render close dispatch waits until `14:00..14:29 Asia/Taipei`, so market/theme freshness preflight can write after the `14:00` safe-write time before dispatching the bot.
- Render dispatch sends explicit workflow input `run_mode=bot`.

## Non Goals
- No live Telegram delivery.
- No DB schema, RLS, grant, policy, role, index, or constraint change.
- No direct hand-written production DML.
- No new production backfill in this correction; previous approved backfill already brought target tables to `2026-06-10`.

## Impacted Modules And Consumers
- `app.py`
  - Consumer: Render web service called every five minutes.
- `.github/workflows/stock-bot-clean.yml`
  - Consumer: GitHub workflow_dispatch from Render.
- `tests/test_app_render_preflight.py`
- `tests/test_workflow_runtime_config.py`

## Output Contract
- Render owns timing:
  - pre-market: once in `08:30..08:39`
  - intraday: five-minute buckets in `09:00..12:59`
  - close: once in `14:00..14:29`
- Render runs market/theme freshness preflight before GitHub dispatch.
- GitHub workflow has no native `schedule:` block.
- GitHub workflow defaults to `run_mode=bot` unless dispatch inputs say otherwise.
- Freshness warning may be appended, but dispatch can still proceed because report generation itself fails closed on stale evidence.

## Acceptance
- Render test proves 13:25 skips and 14:05 close dispatch runs freshness before GitHub dispatch.
- Render test proves intraday tags use five-minute buckets.
- Render test proves dispatch payload includes `inputs.run_mode=bot`.
- Workflow test proves no native cron and no `github.event.schedule` mapping remains.
- Phase3 evidence tests still pass.

## Failure Specimen And Route
- Owner failure: "Render every five minutes executes Git, then after close it stops; why did you not inspect that writeback logic?"
- Failure layer: Render dispatch gate and workflow scheduling contract.
- Verification route: `tests/test_app_render_preflight.py`, `tests/test_workflow_runtime_config.py`, `tests/test_phase3_evidence_automation.py`.

## Forbidden / Blocking
- Do not restore GitHub native cron as the primary scheduler.
- Do not send live Telegram.
- Do not write production DB outside approved scripts.
