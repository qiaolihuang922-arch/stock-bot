# CURRENT_STATE.md

## Current Task

- task_id: `rr_context_standardization_v21_1_20260615`
- status: `implemented`
- version: `v21.1`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; report wording must be decision-first and avoid internal pipeline noise.
- Production dispatch model: Render web service is called every five minutes, then GitHub workflow dispatch runs `run_mode=bot`.
- Production source-of-truth is Supabase / runner data, not local cache, worktree state, or agent memory.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval unless explicitly authorized.
- Non-schema DB writes/backfills must use approved repo scripts or service APIs; direct hand-written production DML is forbidden.

## Current Implementation State

- RR is now represented as an auditable entry / stop / target calculation:
  - `rr_formula` is `(target-entry)/(entry-stop)`;
  - strategy result carries entry, stop, target, reward, risk, risk percent, target basis, and context;
  - daily snapshot / signal item / backfill feature payloads carry the same fields through shared strategy feature plumbing.
- Report display state:
  - non-actionable high RR is `理論RR`, not `RR 達標`;
  - RR不足 remains normal `RR x｜需>=1.5`;
  - setup/retest/quality blockers stay primary so high RR cannot read as a buy recommendation.
- DB state:
  - `db/sql/v21_2_rr_context_columns.sql` exists for Owner review.
  - The agent did not execute schema migration or production DML.

## Verification State

- `263 passed, 147 warnings, 44 subtests passed`.
- Official generator dry-run: `VERSION v21.1`, `messages 4`, no live Telegram delivery.
- Dry-run confirmed:
  - `旺宏` is waiting for retest and shows `理論RR 2.21僅參考`;
  - high-RR weak setup names show `理論RR ...（setup未成立）`;
  - RR不足 card remains normal RR blocker.

## Known Follow-ups

- Owner review/apply `db/sql/v21_2_rr_context_columns.sql`, then run approved backfill/write scripts if production typed RR fields are needed historically.
- Confirm next scheduled `run_mode=bot` after push.
- Add a PowerShell-equivalent git completion gate because bash gates fail locally without WSL/Hyper-V.
- Optional dedicated cleanup task: Owner may delete abandoned `trades` table; current code scan found no consumers.
