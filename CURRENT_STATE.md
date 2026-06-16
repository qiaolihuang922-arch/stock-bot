# CURRENT_STATE.md

## Current Task

- task_id: `rebound_retest_anchor_wording_v21_1_20260616`
- status: `implemented + QA passed + full pytest passed`
- version: `v21.1`
- no live Telegram delivery.
- no DB schema/write/backfill/prune.

## Stable Context

- Owner reads Telegram on mobile; summary must answer decision, next action and risk, not repeat raw counts.
- Production dispatch model: Render web service is called every five minutes, then GitHub workflow dispatch runs `run_mode=bot`.
- Production source-of-truth is Supabase / runner data, not local cache, worktree state, runtime dict, or agent memory.
- Cross-day memory must be DB backed.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval unless explicitly authorized.
- Non-schema DB writes/backfills must use approved repo scripts or service APIs; direct hand-written production DML is forbidden.

## Current Implementation State

- Runtime report remains `v21.1`.
- Multi-day rebound retest cards still require DB-backed `daily_price` cross-day context.
- The user-visible retest anchor now says:
  - `最近反彈收盤 N 附近`
- It no longer says:
  - `最近修復支撐 N 附近`
- Meaning:
  - the bot is waiting for a pullback/retest near the latest rebound close and confirmation that it does not break;
  - it is not claiming the retest already happened;
  - it is not claiming a true support level was computed.

## Verification State

- Targeted official formatter tests passed.
- Full pytest passed: `484 passed, 8 skipped, 165 warnings, 110 subtests passed`.
- Official dry-run 群創 / 旺宏 cards match the new wording.
- Code and closeout docs pushed in commit `c555562`; git completion passed.

## Known Follow-ups

- Observe next production `run_mode=bot` artifact after push.
- If Owner wants true support wording later, implement a real support source first: swing low / moving average / volume area / pivot, with DB-backed evidence and tests.
