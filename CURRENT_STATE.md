# CURRENT_STATE.md

## Current Task

- task_id: `strategy_readability_audit_v21_1_20260615`
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

- v21.1 risk/reward calculation remains unchanged:
  - `(target-entry)/(entry-stop)`;
  - non-actionable high values remain theoretical/reference only;
  - production `daily_signal_snapshot` backfill was already verified with no duplicate overlap in the prior cycle.
- This cycle changed only report presentation semantics:
  - user-visible `RR` is rendered as `風險報酬`;
  - non-actionable high risk/reward is rendered according to strategy blocker:
    - type/quality not passed;
    - retest not confirmed;
    - weak rebound not turned strong;
    - open confirmation still required;
  - `等RR修復` is rendered as `等風險報酬`;
  - `setup`, `V10`, and `V20` are removed from visible strategy explanations;
  - strategy decisions and thresholds are unchanged.

## Verification State

- `205 passed, 147 warnings, 44 subtests passed`.
- Official generator dry-run printed the updated unheld message and summary.
- Official dry-run scan found no visible `setup`, `V10`, `V20`, `理論RR`, `理論風險報酬`, or unspaced `風險報酬>=`.
- No live Telegram delivery.
- No DB write, backfill, schema change, RLS, grant, policy, role, index, or constraint change in this task.

## Known Follow-ups

- Observe next scheduled `run_mode=bot` report after push.
- Optional future product task: add a short glossary/legend if Owner wants more explanation than inline wording.
