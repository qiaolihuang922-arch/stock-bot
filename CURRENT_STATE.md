# CURRENT_STATE.md

## Current Task

- task_id: `near_breakout_tracking_contract_v21_1_20260616`
- status: `implemented + QA passed + full pytest passed + pushed`
- version: `v21.1`
- no live Telegram delivery.
- no DB schema/write/backfill/prune.

## Stable Context

- Owner reads Telegram on mobile; report wording must be decision-first and avoid repeated rows.
- Production dispatch model: Render web service is called every five minutes, then GitHub workflow dispatch runs `run_mode=bot`.
- Production source-of-truth is Supabase / runner data, not local cache, worktree state, runtime dict, or agent memory.
- Cross-day memory must be DB backed. Yahoo/TWSE loader payload is allowed for same-run technical indicators, not for cross-day source-of-truth claims.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval unless explicitly authorized.
- Non-schema DB writes/backfills must use approved repo scripts or service APIs; direct hand-written production DML is forbidden.

## Current Implementation State

- Runtime report remains `v21.1`.
- Distance contract:
  - `<0`: 已突破
  - `<1`: 臨界突破
  - `<=5`: 接近突破
  - `>5`: 遠離突破
- Near-breakout C-quality observation no longer falls through to淘汰.
- Hard failure remains hard:
  - `decision=FAIL`
  - `突破失敗`
  - `FAILED_BREAKOUT`
  - `DISTRIBUTION`
- Weak rebound remains conservative and is not loosened by near-distance alone.

## Verification State

- Targeted tests: `6 passed, 12 subtests passed`.
- Broader report / strategy tests: `255 passed, 46 subtests passed`.
- Full pytest: `482 passed, 8 skipped, 110 subtests passed`.

## Known Follow-ups

- Observe next scheduled `run_mode=bot` report and confirm production Telegram artifact matches the fixed wording.
- If production still shows old classification, inspect runner commit/deployment path before changing strategy again.
