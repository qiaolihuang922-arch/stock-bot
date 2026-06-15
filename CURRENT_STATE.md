# CURRENT_STATE.md

## Current Task

- task_id: `unheld_card_mobile_denoise_20260616`
- status: `implemented + QA passed, pending push`
- version: `v21.1`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; report wording must be decision-first and avoid repeated rows.
- Production dispatch model: Render web service is called every five minutes, then GitHub workflow dispatch runs `run_mode=bot`.
- Production source-of-truth is Supabase / runner data, not local cache, worktree state, or agent memory.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval unless explicitly authorized.
- Non-schema DB writes/backfills must use approved repo scripts or service APIs; direct hand-written production DML is forbidden.

## Current Implementation State

- Runtime report remains `v21.1`.
- Unheld card presentation now removes the unreadable hard-concat rows:
  - no standalone `拆解`;
  - no wall-like `狀態` / `進場檢查`;
  - non-actionable cards show `進場` / `缺口` / `可買`.
- Strategy logic is unchanged.
- No DB operation was performed.

## Verification State

- Dry-run `generate_report(dry_run=True)` checked locally; unheld cards render readable short entry lines.
- Tests:
  - `205 passed, 44 subtests passed`
- No live Telegram delivery.

## Known Follow-ups

- Observe next scheduled `run_mode=bot` report and confirm readable `進場` / `缺口` / `可買` unheld-card layout in production artifact.
- Future cleanup candidate: rejected-card `原因` lines can still be verbose.
- Prior DB follow-ups remain:
  - decide whether to enrich or hide `market_theme_index_daily_bars` OHLCV/member placeholder columns;
  - implement or retire `signal_outcomes` max high/drawdown metrics.
