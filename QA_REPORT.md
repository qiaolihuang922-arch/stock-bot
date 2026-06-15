# QA_REPORT: strategy_axis_memory_backfill_prune_20260615

## Test Scope

- Production read-after-schema.
- Production backfill through repo script/API.
- Production duplicate/version prune through repo script/API.
- Read-after-write validation for new strategy-axis memory fields.
- MD/process closeout.

## Risk Scan

- If backfill uses a new version, it may create duplicate historical rows.
- If backfill hand-writes DML, it bypasses repo validation.
- If prune deletes without a plan, unique history may be lost.
- If `signal_items` is fabricated from daily_price, report-run history becomes false.
- If docs are not updated, the next round may repeat the same missing-memory confusion.
- If audit fields are populated too broadly, a non-retest day can look like active retest memory.

## Cross-Block Semantic Consistency

- Backfill version remained `v21.1`.
- `daily_signal_snapshot` is the source for strategy memory.
- `signal_items` is not backfilled historically because it is a report-run table.
- Prune result says no duplicates; no deletion was forced.
- No live Telegram delivery occurred.

## User Misread Risk

- Reduced: DB now actually contains the strategy-axis memory fields on historical snapshots.
- Reduced: docs now state exactly what was backfilled and what was not.
- Remaining: future bot run should be observed to confirm `signal_items` new fields fill naturally.

## Failure Specimen Countercheck

- Owner concern: new DB fields existed but would remain empty, leaving no real multi-day memory.
- Countercheck:
  - before backfill: new fields had `0` non-null rows;
  - after backfill: all `5786` `daily_signal_snapshot` rows have non-null strategy-axis fields.

## Evidence

- Backfilled `5786` `daily_signal_snapshot` rows.
- `schema_fallback=false` for every stock backfill.
- Read-after-write non-null counts:
  - `stock_strength_state=5786`
  - `entry_setup_state=5786`
  - `actionability_state=5786`
  - `retest_reference_price=356`
  - `retest_days_since_breakout=356`
  - non-retest rows with retest anchor cleared: `5430`
- Prune write:
  - `deleted_rows=0`
  - exact duplicate extra rows after prune: `0`
  - multi-version extra rows after prune: `0`

## Not Tested

- Live Telegram delivery.
- Next scheduled Render/GitHub bot run.
- Historical `signal_items` reconstruction, intentionally not performed.

## QA Conclusion

通過

Reason: production DB read-after-write confirms the backfill succeeded; repo-script prune confirms there was no duplicate data to delete.
