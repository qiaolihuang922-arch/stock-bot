# TASK: strategy_axis_memory_backfill_prune_20260615

## Status

- task_id: `strategy_axis_memory_backfill_prune_20260615`
- task_type: `risk_patch`
- status: `implemented`
- version: `v21.1`
- QA level: `L3`

## Owner Problem

Owner applied the v21.3 strategy-axis memory schema and requested actual DB backfill, duplicate cleanup, and complete MD handoff. Owner also requested that future DB/data work automatically updates documents and cleanup evidence without repeated reminders.

## User Visible Result

- `daily_signal_snapshot` has been backfilled from `daily_price`.
- New strategy-axis memory fields are populated for historical v21.1 snapshot rows.
- Duplicate/version prune was executed through the repo script; no duplicate rows existed, so no rows were deleted.
- Process rule added to `AGENTS.md` requiring future DB backfill/prune tasks to update MD and cleanup evidence automatically.

## Non Goals

- No live Telegram delivery.
- No hand-written production DML.
- No production schema change in this task; schema was already applied by Owner.
- No fake reconstruction of historical `signal_items`.
- No threshold calibration.

## Impacted Modules And Direct Consumers

- Production DB:
  - `daily_signal_snapshot`
- Existing repo scripts:
  - `scripts/backfill_snapshots_from_daily_price.py`
  - `scripts/prune_daily_signal_snapshot_versions.py`
- Process docs:
  - `AGENTS.md`
  - `DISPATCH.md`
  - `CURRENT_STATE.md`
  - `CLEANUP_PLAN.md`
  - `TASK.md`
  - `CHANGELOG.md`
  - `QA_REPORT.md`

## Output Contract

- Backfill source must be `daily_price`.
- Version must remain `v21.1` so upsert updates existing rows instead of creating a new duplicate version.
- Duplicate cleanup must keep `v21.1`.
- If delete candidates are zero, record zero deletion instead of forcing data deletion.
- `signal_items` historical rows must not be fabricated from `daily_price`; future bot runs will fill those report-item columns naturally.

## Version Contract

- Backfilled snapshot version: `v21.1`.
- Runtime report header remains `v21.1`.

## Acceptance Conditions

- Read-before-write confirms schema exists.
- Backfill writes snapshot rows with `schema_fallback=false`.
- Read-after-write confirms new fields are non-null on `daily_signal_snapshot`.
- Prune plan/write confirms exact duplicate and multi-version duplicate counts are zero.
- MD files record results and future cleanup rules.
- No live Telegram delivery.

## Fixture / Failure Specimen

- Owner concern: DB had new columns but no historical values, so multi-day state would still be missing.
- Required route:
  - production read audit;
  - repo-script backfill;
  - production read-after-write;
  - repo-script prune;
  - MD closeout.

## Forbidden And Blocking Conditions

- Do not hand-write DML.
- Do not backfill `signal_items` by inventing historical report runs.
- Do not delete data unless repo prune plan selects candidates.
- Do not claim future bot-run data exists before it is written.
