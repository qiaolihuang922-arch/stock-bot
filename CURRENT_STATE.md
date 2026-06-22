# CURRENT_STATE.md

## Current Task

- task_id: `low_repair_ready_state_v21_1_20260622`
- status: `implemented + QA conditional pass + git completion passed`
- version: `v21.1`
- live Telegram delivery: not run
- DB schema change: none
- DB write/backfill/delete: none

## Stable Context

- Owner reads Telegram on mobile; report wording must answer actionable trading questions without repeated filler.
- Production source-of-truth is Supabase / runner data, not local cache, worktree state, runtime dict, or agent memory.
- Cross-day memory must be DB backed.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval.
- Non-schema DB writes/backfills must use approved repo scripts or service APIs; direct hand-written production DML is forbidden.

## Current Implementation State

- `core/generator.py`
  - Added `daily_price_low_repair_status`.
  - `等低位修復` now promotes to `可準備` when the low-repair checklist is complete.
  - `僅追蹤` count excludes `隔日確認`.
- `presentation/report.py`
  - Low-repair-ready cards render as `可準備｜低位修復成立`.
  - The card says after-hours confirmation is still required and suppresses duplicate generic data/source lines.
  - Empty summary parentheses are suppressed.
- `tests/test_generator_report.py`
  - Regression coverage added for the `3231 緯創` all-met low-repair conflict.
  - Funnel count tests updated so `隔日確認` and `僅追蹤` are mutually exclusive.
- `TASK.md`, `CHANGELOG.md`, `QA_REPORT.md` updated for this cycle.

## Verification State

- Targeted report tests passed:
  - `12 passed`
- Adjacent state/replay tests passed:
  - `16 passed`
- Full generator report suite:
  - `215 passed`, `1 failed`
  - failure is `test_v20_4_47_generate_report_appends_live_readonly_future_watch_sources`, unrelated to low-repair state/display.
- Official `generate_report(dry_run=True)`:
  - `3231 緯創` renders `可準備｜低位修復成立`
  - `2324 仁寶` remains `等低位修復` because it has not stood back above 5-day MA
  - no live Telegram
- Git completion gate passed:
  - commit: `f9c1f79`
  - branch: `main`
  - pushed to `origin/main`

## Known Findings

- `.pytest_cache` still cannot be written on this machine because of local `WinError 5`; tests execute despite the cache warning.
- Future-watch source test currently fails with `global_lines=0`; track separately.

## Next Action

- Open a separate task for the unrelated future-watch source test if Owner wants repo-wide green tests.
