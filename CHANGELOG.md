# CHANGELOG: db_data_quality_multiday_audit_v21_1_20260617

## Changes

- Added `scripts/audit_db_data_quality.py`
  - Read-only Supabase audit for current production tables.
  - Checks duplicate business keys for known tables.
  - Checks `daily_price` OHLCV legality.
  - Recomputes `daily_signal_snapshot` close, volume ratios, breakout levels, and retest zones from `daily_price`.
  - Separates all-history snapshot gaps from current strategy-window gaps.
  - Classifies expected constant/null fields so source-limited fields are not mistaken for fake data.
- Added `tests/test_audit_db_data_quality.py`
  - Invalid OHLC detection.
  - Snapshot-vs-price mismatch detection.
  - Expected constants not becoming review noise.
  - Current-window coverage separation.
- Updated `.gitignore`
  - Ignore local `artifacts/` DB audit evidence.

## Production DB Actions

- No schema change.
- No live Telegram.
- No hand-written DML.
- Prune dry-run:
  - `daily_signal_snapshot` delete candidates: `0`
  - exact duplicate `(stock_id, trade_date, version)`: `0`
- Approved snapshot backfill writes:
  - `2408` on `2026-06-16`: 1 `v21.1` row upserted from `daily_price`
  - `3035` on `2026-06-16`: 1 `v21.1` row upserted from `daily_price`
  - `2337` on `2026-06-16`: 1 `v21.1` row upserted from `daily_price`

## Evidence Artifacts

Local artifacts were generated under `D:\reserch\stock-bot\artifacts\` and are intentionally ignored by git:

- `db_table_health_20260617.json`
- `daily_signal_snapshot_prune_plan_20260617.json`
- `db_data_quality_20260617.json`
- `snapshot_backfill_*_20260616_dry_run.json`
- `snapshot_backfill_*_20260616_write.json`
- `db_data_quality_20260617_after_write.json`
- `daily_signal_snapshot_prune_plan_20260617_after_write.json`
- `strategy_buy_path_replay_30d_20260617_after_write.json`
- `strategy_rule_outcomes_120d_20260617_after_write.json`

## Verification

- Targeted tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_audit_db_data_quality.py tests\test_audit_db_table_health.py -q --tb=short`
  - result: `7 passed`
- Read-after-write DB quality audit:
  - tables checked: `11`
  - `fix_issue_count=0`
  - `review_item_count=0`
  - `current_window_missing_snapshot_rows=0`
  - `safe_to_delete_rows=0`
- Prune read-after dry-run:
  - `delete_candidate_rows=0`
  - `exact_duplicate_extra_rows=0`
- Strategy replay:
  - `deadlock_suspected=False`
  - `has_real_buyable_path=True`
  - `has_prepare_path=True`
- Official generator dry-run:
  - `generate_report(dry_run=True)` returned `4` messages.

## Residual Risk

- `strategy_rule_outcomes_120d` still flags several blocked groups as possibly too strict. That is a strategy-calibration task, not a DB data-quality failure.
- `trades` still exists with a legacy row but no current code path was found consuming `supabase.table("trades")`; deletion needs a dedicated approved prune/delete interface if Owner still wants it removed.
