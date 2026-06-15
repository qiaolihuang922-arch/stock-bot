# CURRENT_STATE.md

## Current Task

- task_id: `unheld_readability_v21_1_20260615`
- status: `implemented + QA passed`
- version: `v21.1`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; report wording must be decision-first and avoid internal pipeline noise.
- Production dispatch model: Render web service is called every five minutes, then GitHub workflow dispatch runs `run_mode=bot`.
- Production source-of-truth is Supabase / runner data, not local cache, worktree state, or agent memory.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval unless explicitly authorized.
- Non-schema DB writes/backfills must use approved repo scripts or service APIs; direct hand-written production DML is forbidden.

## Current Implementation State

- RR remains auditable from the previous v21.1 work:
  - `(target-entry)/(entry-stop)`;
  - non-actionable high RR remains theoretical/reference only;
  - production `daily_signal_snapshot` backfill was already verified with no duplicate overlap.
- This cycle changed only report readability:
  - unheld cards now show `不能買 / 還差 / 可買條件`;
  - old main diagnostic labels are removed from blocker explanations;
  - long RR/quality/volume/retest evidence is compacted into readable clauses;
  - strategy decisions and thresholds are unchanged.

## Verification State

- `205 passed, 147 warnings, 44 subtests passed`.
- Official generator dry-run printed the updated unheld message.
- No live Telegram delivery.
- No DB write, backfill, schema change, RLS, grant, policy, role, index, or constraint change in this task.

## Known Follow-ups

- Observe next scheduled `run_mode=bot` report after push.
- Optional future product task: decide whether some secondary evidence can be hidden behind a shorter mode; current patch preserves all material blockers.
