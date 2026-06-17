# CURRENT_STATE.md

## Current Task

- task_id: `db_backed_price_transition_v21_1_20260617`
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
- Cross-day price transition now uses DB-backed `daily_price` recent closes plus current price:
  - `UP_THEN_DOWN`
  - `DOWN_THEN_UP`
  - `CONTINUOUS_UP`
  - `CONTINUOUS_DOWN`
- Multi-day rebound / pullback route:
  - DB-confirmed multi-day rebound followed by current pullback becomes `等回測`.
  - It no longer depends on a prior `WEAK_REBOUND` label.
- Volume gate:
  - data/report `volume_ratio >= 1.1` releases visible `量能不足`.
  - data/report `volume_ratio < 1.1` is primary only near setup; far names keep `等低位修復` / `等接近`.
  - data-aware result is local only and does not mutate original payload.
- Formatter:
  - cards use the same data-aware volume/distance as core state.
  - DB-backed continuous down prevents `極強` / `不可追高觀察` misread.

## Verification State

- Generator report tests passed:
  - `211 passed, 163 warnings, 46 subtests passed`
- Full pytest passed:
  - `494 passed, 8 skipped, 175 warnings, 110 subtests passed`
- Official generator dry-run generated `4` messages and showed:
  - 聯電: `等量能｜等量`.
  - 旺宏: `等回測｜反彈修復待回測`.
  - 群創: not `等量能｜量能不足`.
  - 緯創 / 技嘉 / 仁寶: `等低位修復`.

## Known Findings

- `.pytest_cache` cannot be written on this machine because of local `WinError 5`; tests still execute and pass.
- No schema expansion was needed for this task.

## Next Action

- No active follow-up in this cycle.
