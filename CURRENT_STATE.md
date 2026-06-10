# CURRENT_STATE.md

## Current Task

- task_id: `render_dispatch_writeback_logic_20260610`
- status: `complete`
- version: `v21.0.2`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; visible wording must be decision-first and avoid internal pipeline noise.
- Production dispatch model is Render web service called every five minutes, which then dispatches GitHub workflow.
- GitHub Actions workflow should be dispatch-only unless Owner explicitly changes the production timing model.
- Production source-of-truth remains Supabase / runner data, not local cache.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval.
- Non-schema DB write/backfill must use existing approved repo scripts or service APIs; direct hand-written production DML is forbidden.

## Current Changes

- Render intraday tags use five-minute buckets.
- Render close dispatch runs at `14:00..14:29 Asia/Taipei`, after the market/theme safe-write time.
- GitHub workflow native cron was removed.
- GitHub workflow dispatch defaults to `run_mode=bot`; Render sends it explicitly.

## Verification State

- Render/workflow/phase3 tests: `27 passed, 8 skipped`.

## Known Follow-ups

- Live Render external ping and live GitHub Actions execution after this correction push are not yet proven.
- Local bash workflow execution tests skipped because this machine's `bash` points to unavailable WSL/Hyper-V.
- `sector_theme_members` historical membership remains blocked: available source is latest profile mapping, not dated membership history.
