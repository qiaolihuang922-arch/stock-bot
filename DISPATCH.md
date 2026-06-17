# DISPATCH.md

## Active

- task_md_holds: `db_data_quality_multiday_audit_v21_1_20260617`
- status: `implemented + QA pass`
- current_version: `v21.1`
- live Telegram delivery: `not run`
- DB schema change: `none`

## Result Summary

- Added a reusable read-only DB data-quality audit.
- Audited 11 known production tables:
  - `daily_price`
  - `daily_signal_snapshot`
  - `market_theme_confirmed_evidence`
  - `market_theme_index_daily_bars`
  - `position_events`
  - `positions`
  - `sector_theme_members`
  - `signal_items`
  - `signal_outcomes`
  - `signal_runs`
  - `trades`
- Confirmed no duplicate business keys in the checked tables.
- Confirmed `daily_price` has no invalid OHLCV rows.
- Fixed 3 stale `daily_signal_snapshot` rows on `2026-06-16` by approved backfill from `daily_price`:
  - `2408`
  - `3035`
  - `2337`
- No rows were deleted.
- Current strategy-window snapshot gap is `0`.

## Verification

- `.\.venv\Scripts\python.exe -m pytest tests\test_audit_db_data_quality.py tests\test_audit_db_table_health.py -q --tb=short`
  - result: `7 passed`
- `scripts\audit_db_data_quality.py --coverage-start-date 2024-06-17`
  - result: `fix_issue_count=0`, `review_item_count=0`, `current_window_missing_snapshot_rows=0`
- `scripts\prune_daily_signal_snapshot_versions.py --keep-version v21.1 --dry-run`
  - result: `delete_candidate_rows=0`
- `generate_report(dry_run=True)`
  - result: `4` messages, no live Telegram.

## Current Git State

- implementation and verification complete for this cycle.

## Next Action

- No DB cleanup remains for this cycle.
- Strategy gate calibration from replay outcome flags is a separate follow-up task.
