# CURRENT_STATE.md

## Current Task

- task_id: `db_backed_low_repair_v21_1_20260616`
- status: `implemented + QA pass`
- version: `v21.1`
- no live Telegram delivery.
- no DB schema/write/backfill/prune.

## Stable Context

- Owner reads Telegram on mobile; report wording must explain what is being waited for without repeated filler lines.
- Production dispatch model: Render web service is called every five minutes, then GitHub workflow dispatch runs `run_mode=bot`.
- Production source-of-truth is Supabase / runner data, not local cache, worktree state, runtime dict, or agent memory.
- Cross-day memory must be DB backed.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval unless explicitly authorized.
- Non-schema DB writes/backfills must use approved repo scripts or service APIs; direct hand-written production DML is forbidden.

## Current Implementation State

- Runtime report remains `v21.1`.
- `daily_price` read path now preserves OHLCV in `recent_daily_price_points`.
- New DB-backed observation route:
  - `等低位修復` is allowed only when `cross_day_context.source_of_truth` includes `daily_price` and enough DB daily points exist.
  - It is not a buy signal.
  - Effective buy requires support hold + reclaim 5-day MA + volume repair + risk/reward >= 1.5.
- Far pullback/reclaim stocks with DB daily_price no longer get forced back to `等接近突破區`.
- Missing / insufficient DB daily_price still fails closed.

## Verification State

- DB read probe confirmed daily OHLCV for 2324 / 3231 / 2376 / 2337 / 3481.
- Targeted tests passed:
  - `223 passed, 159 warnings, 46 subtests passed`
- Full pytest passed:
  - `491 passed, 8 skipped, 169 warnings, 110 subtests passed`
- Official generator dry-run generated `4` messages and showed 仁寶 / 緯創 / 技嘉 as `等低位修復`.

## Known Findings

- `.pytest_cache` cannot be written on this machine because of local `WinError 5`; tests still execute and pass.
- No schema expansion was needed for this task.

## Next Action

- Push closeout doc update and run git completion gate.
