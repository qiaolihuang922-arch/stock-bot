# CURRENT_STATE.md

## Current Task

- task_id: `cross_day_source_truth_v21_1_20260616`
- status: `implemented + QA passed + pushed`
- version: `v21.1`
- no live Telegram delivery.
- no DB schema/write/backfill/prune.
- DB read-only verification performed for `daily_price`.

## Stable Context

- Owner reads Telegram on mobile; report wording must be decision-first and avoid repeated rows.
- Production dispatch model: Render web service is called every five minutes, then GitHub workflow dispatch runs `run_mode=bot`.
- Production source-of-truth is Supabase / runner data, not local cache, worktree state, runtime dict, or agent memory.
- Cross-day memory must be DB backed. Yahoo/TWSE loader payload is allowed for same-run technical indicators, not for cross-day source-of-truth claims.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval unless explicitly authorized.
- Non-schema DB writes/backfills must use approved repo scripts or service APIs; direct hand-written production DML is forbidden.

## Current Implementation State

- Runtime report remains `v21.1`.
- Multi-day rebound repair now requires DB daily_price:
  - `cross_day_context.source_of_truth` must include `daily_price`.
  - `cross_day_context.recent_daily_price_points` must contain at least 4 DB close points.
  - payload `closes` / live `price` alone cannot trigger `反彈修復待回測`.
- `build_cross_day_contexts` reads `daily_price` along with `daily_signal_snapshot` and `position_events`.
- Hard failure remains hard:
  - `decision=FAIL`
  - `FAILED_BREAKOUT`
  - `reject_family=突破失敗`
- No DB write/backfill/schema change was performed.

## Verification State

- Targeted tests: `3 passed`.
- Broader strategy/report tests: `260 passed, 44 subtests passed`.
- Evidence tests: `53 passed, 13 subtests passed`.
- Full tests: `481 passed, 8 skipped, 108 subtests passed`.
- Official dry-run checked locally.
- Production DB read-only checked for 旺宏 recent `daily_price` close points.

## Known Follow-ups

- Observe next scheduled `run_mode=bot` report and confirm production Telegram artifact matches dry-run wording.
- If production still shows old classification, inspect runner commit/deployment path before changing strategy again.
