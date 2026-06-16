# CURRENT_STATE.md

## Current Task

- task_id: `strategy_buy_path_db_replay_audit_v21_1_20260616`
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
- New read-only strategy replay tool:
  - `scripts/audit_strategy_buy_path_replay.py`
- New replay artifact:
  - `reports/audit/strategy_buy_path_replay_v21_1_20260616.json`
- Replay result:
  - events: `5798`
  - buyable/trend stock-days: `700`
  - buy-like including prepare: `1035`
  - snapshot tradeable blocked by funnel: `0`
  - deadlock suspected: `false`

## Verification State

- Targeted replay tests passed: `6 passed, 1 warning`.
- Full pytest passed: `486 passed, 8 skipped, 165 warnings, 110 subtests passed`.
- Commit/push pending.

## Known Follow-ups

- Run full pytest and complete git closeout.
- If Owner wants next strategy audit, run outcome replay for buyable days: next 1/3/5/10 day returns, MAE/MFE and stop-hit rate.
