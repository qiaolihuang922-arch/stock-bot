# CURRENT_STATE.md

## Current Task

- task_id: `afterhours_summary_trade_plan_v21_1_20260616`
- status: `implemented + QA passed + full pytest passed + pushed`
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
- Afterhours summary now:
  - removes market/count line;
  - removes duplicate today-buy status line;
  - removes empty `新增有效進場：無` line;
  - hides `未持倉狀態` when there is no actionable / prepare candidate;
  - keeps `結論`, `明日計畫`, and `持倉風控檢查`.

## Verification State

- Targeted summary tests passed.
- Full pytest passed: `484 passed, 8 skipped, 165 warnings, 110 subtests passed`.
- Official dry-run summary matches Owner-visible route.
- Code commit pushed; closeout doc commit pending git completion.

## Known Follow-ups

- Observe next production `run_mode=bot` artifact after push.
- If Owner wants even shorter summary, next iteration should tune `明日計畫` grouping only, not re-add counts.
