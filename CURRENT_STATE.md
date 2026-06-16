# CURRENT_STATE.md

## Current Task

- task_id: `approach_distance_gap_v21_1_20260616`
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
- `等接近` card contract:
  - title label: `遠離觸發`;
  - reason: `還沒到買點區`;
  - gap: `距突破 X%，仍未進入觸發區`;
  - can-buy condition: `接近觸發區，或出現趨勢延續/回測承接買點型態`.
- No DB operation was performed.

## Verification State

- Targeted tests: `212 passed, 44 subtests passed`.
- Full tests: `479 passed, 8 skipped, 108 subtests passed`.
- Dry-run official generator checked locally.

## Known Follow-ups

- Observe next scheduled `run_mode=bot` report and confirm production Telegram artifact matches dry-run wording.
- If production still shows old `等接近｜個股弱勢`, inspect runner commit/deployment path first.
