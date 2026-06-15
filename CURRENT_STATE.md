# CURRENT_STATE.md

## Current Task

- task_id: `entry_quality_d_semantics_v21_1_20260615`
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
- `entry_quality` remains an entry setup grade, not a general stock grade.
- Visible report now separates:
  - true setup quality gap: `買點品質未過（目前 D，需 B 以上）`;
  - rebound/retest state: `買點品質：回測 / 轉強後重評`;
  - cooldown state: `買點品質：降溫後重評`.
- `LIMIT_LOCK`, `LIMIT_REBOUND`, and `WEAK_REBOUND` are preserved as price-behavior states instead of being hidden by generic low quality.
- Snapshot reason for per-stock `market_grade == D` is `個股弱勢`, not `市場弱`.

## Verification State

- `257 passed, 149 warnings, 44 subtests passed`.
- Official generator dry-run printed the updated full message list.
- Snapshot probe confirmed:
  - limit-up can have strong `market_grade` but low `entry_quality` because current entry is not actionable;
  - multi-day rise can still be observation if risk/reward is not enough;
  - true weak rebound remains D.
- No live Telegram delivery.
- No DB write, backfill, schema change, RLS, grant, policy, role, index, or constraint change in this task.

## Known Follow-ups

- Commit and push current patch.
- Observe next scheduled `run_mode=bot` report after push.
- Optional future strategy task: calibrate entry-quality thresholds from production outcomes, separate from display semantics.
