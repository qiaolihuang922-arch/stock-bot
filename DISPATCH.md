# DISPATCH.md

## Active

- task_md_holds: `strategy_axis_memory_backfill_prune_20260615`
- status: `implemented + QA passed`
- current_version: `v21.1`
- no live Telegram delivery in this cycle.

## Result Summary

- Owner applied v21.3 schema and requested real data backfill, duplicate cleanup, and MD closeout.
- Production schema read confirmed both `daily_signal_snapshot` and `signal_items` contain the new columns.
- Backfilled `daily_signal_snapshot` from `daily_price`:
  - date range: `2024-06-15` to `2026-06-15`
  - version: `v21.1`
  - rows written/upserted: `5786`
  - schema fallback: `false`
- Read-after-write confirmed all `5786` snapshot rows now have non-null strategy-axis memory fields.
- Duplicate/version prune ran:
  - keep version: `v21.1`
  - delete candidates: `0`
  - deleted rows: `0`
- `signal_items` historical rows were not fabricated; future bot runs will fill new item fields.
- Added reusable `AGENTS.md` rule: DB backfill/prune tasks must automatically update MD and cleanup evidence.

## Verification

- Production read-after-write:
  - `stock_strength_state`: `5786/5786`
  - `entry_setup_state`: `5786/5786`
  - `actionability_state`: `5786/5786`
  - `setup_family`: `5786/5786`
  - `data_quality_state`: `5786/5786`
  - `volume_basis`: `5786/5786`
  - `retest_state`: `5786/5786`
- Duplicate audit:
  - exact duplicate extra rows: `0`
  - stock/date multi-version extra rows: `0`
- Prune result:
  - `deleted_rows=0`
- No live Telegram delivery.

## Current Git State

- branch: `main`
- upstream: `origin/main`
- closeout uses Windows-equivalent git checks because bash scripts may fail on this machine without WSL/Hyper-V.

## Next Action

- Commit/push MD closeout.
- Observe next scheduled `run_mode=bot` report to confirm future `signal_items` rows naturally fill the new fields.
