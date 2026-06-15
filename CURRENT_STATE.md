# CURRENT_STATE.md

## Current Task

- task_id: `strategy_axis_split_v21_1_20260615`
- status: `implemented + QA passed`
- version: `v21.1`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; report wording must be decision-first and avoid unexplained internal shorthand.
- Production dispatch model: Render web service is called every five minutes, then GitHub workflow dispatch runs `run_mode=bot`.
- Production source-of-truth is Supabase / runner data, not local cache, worktree state, or agent memory.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval unless explicitly authorized.
- Non-schema DB writes/backfills must use approved repo scripts or service APIs; direct hand-written production DML is forbidden.

## Current Implementation State

- v21.1 strategy thresholds remain unchanged.
- Unheld cards now separate:
  - `強弱`: stock behavior/strength;
  - `買點`: setup readiness;
  - `行動`: buy/wait/no-chase/no-buy actionability.
- New raw-result derived fields:
  - `stock_strength_state`
  - `entry_setup_state`
  - `actionability_state`
- Display fallback recalculates from explicit behavior if a replay payload has stale derived values.
- This is not a DB schema change; the fields are derived in the analysis/report path.

## Verification State

- `258 passed, 149 warnings, 44 subtests passed`.
- Official generator dry-run printed split-axis unheld cards.
- Snapshot probes confirmed:
  - confirmed breakout can reach `READY` / `BUYABLE`;
  - limit-up can be strong while not chaseable;
  - strong rebound can wait for retest instead of looking like generic D weakness.
- No live Telegram delivery.
- No DB write, backfill, schema change, RLS, grant, policy, role, index, or constraint change in this task.

## Known Follow-ups

- Commit and push current patch.
- Observe next scheduled `run_mode=bot` report after push.
- Optional future strategy task: calibrate thresholds from production outcomes, separate from this presentation/derived-state split.
