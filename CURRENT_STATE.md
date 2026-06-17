# CURRENT_STATE.md

## Current Task

- task_id: `db_data_quality_multiday_audit_v21_1_20260617`
- status: `implemented + QA pass`
- version: `v21.1`
- live Telegram delivery: not run
- DB schema change: none

## Stable Context

- Owner reads Telegram on mobile; report wording must be useful and not repeat filler.
- Production dispatch model: Render service is called every five minutes, then GitHub workflow dispatch runs `run_mode=bot`.
- Production source-of-truth is Supabase / runner data, not local cache, worktree state, runtime dict, or agent memory.
- Cross-day memory must be DB backed.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval.
- Non-schema DB writes/backfills must use approved repo scripts or service APIs; direct hand-written production DML is forbidden.

## Current Implementation State

- Added `scripts/audit_db_data_quality.py`.
- Added `tests/test_audit_db_data_quality.py`.
- Added `artifacts/` to `.gitignore`.
- Local artifact directory contains this cycle's DB evidence and is intentionally not committed.
- Approved DB repair performed:
  - upserted `v21.1` `daily_signal_snapshot` rows from `daily_price` for `2408`, `3035`, and `2337` on `2026-06-16`.
- No DB rows were deleted.

## Data Quality State

- Checked tables: 11.
- `daily_price` duplicate `(stock_id, trade_date)`: 0.
- `daily_price` invalid OHLCV: 0.
- `daily_signal_snapshot` duplicate `(stock_id, trade_date, version)`: 0.
- `daily_signal_snapshot` prune candidates: 0.
- Current strategy-window missing snapshots from `2024-06-17`: 0.
- Read-after-write data-quality audit:
  - `fix_issue_count=0`
  - `review_item_count=0`

## Strategy Replay State

- DB replay does not show a dead strategy machine:
  - `has_real_buyable_path=True`
  - `has_prepare_path=True`
  - `deadlock_suspected=False`
- Outcome audit still flags blocked groups as possibly too strict; this is a follow-up strategy calibration task, not a DB data-quality failure.

## Known Findings

- `.pytest_cache` cannot be written on this machine because of local `WinError 5`; tests still execute and pass.
- `trades` still has one legacy row and no current `supabase.table("trades")` consumer was found. Deletion needs a dedicated approved prune/delete interface if Owner still wants it removed.

## Next Action

- No DB cleanup remains for this cycle.
- Strategy gate calibration from replay outcome flags is a separate follow-up task.
