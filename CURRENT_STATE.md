# CURRENT_STATE.md

## Current Task

- task_id: `multi_window_strategy_v21_1_20260615`
- status: `complete`
- version: `v21.1`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; wording must be decision-first and avoid internal pipeline noise.
- Production dispatch model is Render web service called every five minutes, then GitHub workflow dispatch.
- Production source-of-truth remains Supabase / runner data, not local cache.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval.
- Non-schema DB write/backfill must use existing approved repo scripts or service APIs; direct hand-written production DML is forbidden.

## Current Changes

- v21.1 adds multi-window strategy context:
  - V10 for short-term volume;
  - V20 for swing-volume confirmation;
  - 20D resistance for fast breakout anchor;
  - 60D resistance for higher-timeframe context;
  - concrete retest zone.
- Official report and snapshot/raw_result now share the same fields.
- 旺宏-style acute rebound no longer shows vague `等回測`; it shows whether the breakout zone has been reclaimed.

## Verification State

- Focused v21.1 specimens:
  - `3 passed`.
- Targeted strategy/report/backfill suite:
  - `307 passed, 149 warnings, 57 subtests passed`.
- Official dry-run confirmed:
  - `v21.1`;
  - no live Telegram delivery;
  - zone-aware 旺宏 card with V10/V20.

## Known Follow-ups

- V20/60D thresholds should be calibrated against production DB outcomes in a future strategy-quality task.
- No DB schema change was made; expanded fields live in result/raw_result payloads and report artifacts.
