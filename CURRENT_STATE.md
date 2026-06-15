# CURRENT_STATE.md

## Current Task

- task_id: `strategy_axis_memory_schema_v21_3_20260615`
- status: `implemented + QA conditional pass`
- version: `v21.1 runtime / v21.3 schema artifact`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; report wording must be decision-first and avoid unexplained internal shorthand.
- Production dispatch model: Render web service is called every five minutes, then GitHub workflow dispatch runs `run_mode=bot`.
- Production source-of-truth is Supabase / runner data, not local cache, worktree state, or agent memory.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval unless explicitly authorized.
- Non-schema DB writes/backfills must use approved repo scripts or service APIs; direct hand-written production DML is forbidden.

## Current Implementation State

- Runtime report remains `v21.1`.
- New schema artifact is `db/sql/v21_3_strategy_axis_memory_columns.sql`.
- Strategy results now emit persistable memory fields for:
  - strength/setup/action axes;
  - setup family/blockers;
  - data quality;
  - volume basis;
  - retest memory.
- `STRATEGY_FEATURE_FIELDS` carries these fields into daily snapshot and signal item payloads.
- The SQL has not been executed by the agent.
- Historical rows have not been backfilled in this task.

## Verification State

- `258 passed, 149 warnings, 44 subtests passed`.
- Official generator dry-run printed the unheld report successfully.
- No live Telegram delivery.
- No production DB write, backfill, schema execution, RLS, grant, policy, role, index, or constraint change by agent.

## Known Follow-ups

- Commit and push current patch.
- Owner applies `db/sql/v21_3_strategy_axis_memory_columns.sql`.
- After schema confirmation, run backfill via repo script/interface only.
- Future tightening: source-error / insufficient-data paths should explicitly set data-quality fields instead of relying on normal defaults.
