# QA_REPORT: db_data_quality_multiday_audit_v21_1_20260617

## Test Scope

- New DB data-quality audit helper behavior.
- Production DB read-only table scan.
- Approved snapshot backfill dry-run/write/read-after path.
- Daily signal snapshot prune dry-run.
- Strategy replay and official generator dry-run after DB repair.

## Risk Scan

- Direct production DML: not used.
- Schema change: not used.
- Live Telegram: not used.
- DB deletion: not executed; dry-run delete candidate count was `0`.
- Data source for cross-day judgments: `daily_price` remains the persistent source-of-truth.

## Findings And Rechecks

- Initial read-only audit found no `daily_price` OHLCV errors and no duplicate business keys.
- Initial data-quality audit found 7 current-version snapshot mismatches, all small 2026-06-16 volume-ratio differences:
  - `2408`
  - `3035`
  - `2337`
- Each affected row was repaired through `scripts/backfill_snapshots_from_daily_price.py --write --confirm-write`.
- Read-after-write audit confirms:
  - `fix_issue_count=0`
  - `review_item_count=0`
  - `current_window_missing_snapshot_rows=0`
- Prune dry-run after write confirms:
  - `delete_candidate_rows=0`
  - `exact_duplicate_extra_rows=0`

## User Misread Risk

- The full-table snapshot coverage still has 544 gaps before `2024-06-17`; these are outside the current two-year strategy window and should not be interpreted as today's missing data.
- The audit now exposes `current_window_missing_snapshot_rows` separately to avoid that misread.
- Expected constant fields are classified, so repeated values such as `version=v21.1` or `rr_formula` are not treated as fake repeated data.

## Failure Specimen Rebuttal

- Owner suspected multi-day judgments might be fake or based on agent memory.
- Replay and DB audit show the current strategy window has DB-backed `daily_price` and `v21.1` snapshot coverage.
- Strategy replay has real buy/prepare paths:
  - `has_real_buyable_path=True`
  - `has_prepare_path=True`
  - `deadlock_suspected=False`
- Outcome audit still raises calibration flags, so strategy strictness remains a valid follow-up.

## Not Tested

- Live Telegram delivery.
- Render/GitHub scheduled production run.
- DB table deletion.
- Strategy gate redesign based on outcome flags.

## QA Conclusion

通過.

The DB data-quality issue found in this cycle was repaired and verified by read-after-write. Remaining strategy strictness is documented as a separate calibration task.
