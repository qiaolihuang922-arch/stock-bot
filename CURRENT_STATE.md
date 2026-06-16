# CURRENT_STATE.md

## Current Task

- task_id: `explicit_approach_zone_wording_v21_1_20260616`
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
- `等接近` unheld cards now show concrete zones:
  - `等接近突破區 399~400.99`
  - `尚未接近突破區 399~400.99`
  - fallback only when no zone exists: `突破區/回測支撐`.

## Verification State

- Targeted等接近 tests passed.
- Full pytest passed: `484 passed, 8 skipped, 165 warnings, 110 subtests passed`.
- Official dry-run 技嘉 card matches Owner-visible route.
- Pending commit / push.

## Known Follow-ups

- Observe next production `run_mode=bot` artifact after push.
