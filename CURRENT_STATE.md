# CURRENT_STATE.md

## Current Task

- task_id: `entry_quality_priority_v21_1_20260616`
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
- Strategy display priority is now:
  1. limit-up / overheat / cooldown;
  2. rebound and retest confirmation;
  3. risk-reward repair;
  4. approach / distance to trigger;
  5. setup quality only when no clearer blocker exists.
- `entry_quality D` no longer creates an `ENTRY_QUALITY_LOW` state-machine guard.
- `market_grade D/E` is treated as background stock weakness unless the state is only `WATCH/WAIT_SETUP`.
- Official dry-run unheld sample:
  - `緯創 / 仁寶 / 技嘉`: `等接近｜遠離觸發`;
  - `旺宏`: `等回測｜急彈待回測`;
  - `華邦電`: `等回測｜漲停不追`;
  - `聯電`: `等風險報酬｜觀察`.

## Verification State

- Targeted tests: `257 passed, 44 subtests passed`.
- Full tests: `479 passed, 8 skipped, 108 subtests passed`.
- Dry-run official generator checked locally.

## Known Follow-ups

- Observe next scheduled `run_mode=bot` report and confirm production Telegram artifact matches dry-run priority ordering.
- Prior DB follow-ups remain:
  - decide whether to enrich or hide `market_theme_index_daily_bars` OHLCV/member placeholder columns;
  - implement or retire `signal_outcomes` max high/drawdown metrics.
