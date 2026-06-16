# CURRENT_STATE.md

## Current Task

- task_id: `multi_day_rebound_retest_v21_1_20260616`
- status: `implemented + QA passed + pushed`
- version: `v21.1`
- no live Telegram delivery.
- no DB schema/write/backfill.

## Stable Context

- Owner reads Telegram on mobile; report wording must be decision-first and avoid repeated rows.
- Production dispatch model: Render web service is called every five minutes, then GitHub workflow dispatch runs `run_mode=bot`.
- Production source-of-truth is Supabase / runner data, not local cache, worktree state, or agent memory.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval unless explicitly authorized.
- Non-schema DB writes/backfills must use approved repo scripts or service APIs; direct hand-written production DML is forbidden.

## Current Implementation State

- Runtime report remains `v21.1`.
- Multi-day rebound repair:
  - `WEAK_REBOUND` + three rising moves + >=5% rebound => `等回測`;
  - display label: `反彈修復待回測`;
  - still not buyable until standing back / retest holds / non-chase / volume valid.
- Hard failure remains hard:
  - `decision=FAIL`
  - `FAILED_BREAKOUT`
  - `reject_family=突破失敗`
- No DB operation was performed.

## Verification State

- Targeted tests: `2 passed`.
- Full tests: `480 passed, 8 skipped, 108 subtests passed`.
- Dry-run official generator checked locally.

## Known Follow-ups

- Observe next scheduled `run_mode=bot` report and confirm production Telegram artifact matches dry-run wording.
- If production still shows 旺宏 as `淘汰｜弱反彈待確認`, inspect runner commit/deployment path first.
