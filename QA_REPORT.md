# QA_REPORT: db_table_health_audit_20260615

## Test Scope

- Production read-only audit across all active bot tables.
- Duplicate-key risk check for event-like tables.
- Future `signal_items` write-path payload contract.
- MD consistency for normal constants vs real data gaps.

## Risk Scan

- Same value across days can mean either useful metadata or a broken backfill.
- Generic duplicate detection can falsely mark valid event history as duplicate data.
- Filling old report-run item columns from daily bars would create fake history.
- All-null outcome or market OHLCV fields can mislead future strategy logic if consumed without guards.

## Cross-Block Semantic Consistency

- `daily_signal_snapshot` is the real historical strategy-memory table.
- `signal_items` is report-run item history and was not backfilled artificially.
- `market_theme_index_daily_bars` currently should not be treated as full OHLCV/breadth history.
- `signal_outcomes` cannot support max high/drawdown decisions until those columns are populated by a real job.

## User Misread Risk

- Reduced: constant source/formula/version fields are now classified as expected metadata.
- Reduced: retest fields had already been tightened so non-retest rows do not carry fake anchors.
- Remaining: users may still see all-null placeholder columns in Supabase; `CLEANUP_PLAN.md` now marks which ones need source enrichment or cleanup.

## Failure Specimen Countercheck

- Owner concern: "every day same values cannot be useful."
- Countercheck:
  - expected same values: `source`, `version`, formula/basis fields, static source metadata;
  - real gaps: `market_theme_index_daily_bars` OHLCV/member fields, `signal_outcomes` high/drawdown fields, historical `signal_items` new strategy fields.

## Evidence

- Production audit:
  - command: `.\.venv\Scripts\python.exe scripts\audit_db_table_health.py`
  - result: `errors=[]`
- Tests:
  - command: `.\.venv\Scripts\python.exe -m pytest tests\test_audit_db_table_health.py tests\test_daily_snapshot_store.py tests\test_analysis_engine.py -q --tb=short`
  - result: `56 passed`
- No live Telegram delivery.
- No DB schema change.
- No production deletion.

## Not Tested

- Next scheduled Render/GitHub `run_mode=bot` production write.
- Filling `market_theme_index_daily_bars` OHLCV/member fields.
- Filling `signal_outcomes.max_high_pct` / `max_drawdown_pct`.

## QA Conclusion

通過

Reason: all active tables were audited read-only, the reusable audit tool avoids false duplicate claims, and tests now cover the future write path for strategy fields. Data gaps remain documented follow-ups, not silently hidden.
