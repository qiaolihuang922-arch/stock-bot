# CURRENT_STATE.md

## Current Task

- task_id: `dry_run_strategy_evidence_near_breakout_v21_1_20260616`
- status: `implemented + QA passed + full pytest passed + pushed`
- version: `v21.1`
- no live Telegram delivery.
- no DB schema/write/backfill/prune.

## Stable Context

- Owner reads Telegram on mobile; report wording must be decision-first and avoid repeated rows.
- Production dispatch model: Render web service is called every five minutes, then GitHub workflow dispatch runs `run_mode=bot`.
- Production source-of-truth is Supabase / runner data, not local cache, worktree state, runtime dict, or agent memory.
- Cross-day memory must be DB backed.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval unless explicitly authorized.
- Non-schema DB writes/backfills must use approved repo scripts or service APIs; direct hand-written production DML is forbidden.

## Current Implementation State

- Runtime report remains `v21.1`.
- dry-run:
  - no DB writes;
  - no live Telegram;
  - now read-only loads strategy evidence to avoid false `策略樣本證據不足`.
- near-breakout C-quality:
  - `<=5%` near breakout;
  - C quality + non-D/E + non-hard-failure remains tracking / setup wait;
  - not可買, not淘汰.

## Verification State

- Full pytest: `484 passed, 8 skipped, 110 subtests passed`.
- Official dry-run:
  - 聯電: `等型態｜觀察`
  - `距突破：4.06%｜接近突破`
  - summary no longer lists 聯電淘汰.

## Known Follow-ups

- Observe next production `run_mode=bot` artifact to confirm runner uses this commit.
