# TASK: db_data_quality_multiday_audit_v21_1_20260617

## Task Status

- task_id: `db_data_quality_multiday_audit_v21_1_20260617`
- task_type: `risk_patch`
- status: `implemented`
- version_contract: runtime report remains `v21.1`
- QA level: L3

## Owner Problem

Owner asked to verify whether global multi-day judgments are using real DB data, whether all current production tables contain correct/non-duplicated data, and to remove or backfill wrong data through approved scripts only.

## User-Visible Result

- Add a repeatable read-only DB data quality audit.
- Check production tables for duplicate business keys, invalid OHLCV, stale/constant fields, and `daily_signal_snapshot` consistency against `daily_price`.
- Repair confirmed wrong current-version snapshot rows through the approved snapshot backfill script.
- Do not delete rows unless a dry-run prune plan identifies safe delete candidates.

## Non-Goals

- No live Telegram delivery.
- No DB schema/RLS/grant/policy/role/index/constraint change.
- No hand-written production DML.
- No strategy gate calibration in this cycle; replay flags are recorded as follow-up evidence.
- No table deletion without a dedicated approved delete/prune interface.

## Impacted Modules And Consumers

- `scripts/audit_db_data_quality.py`: new read-only production DB audit.
- `tests/test_audit_db_data_quality.py`: regression coverage for data-quality checks.
- `scripts/backfill_snapshots_from_daily_price.py`: approved write path used for three 2026-06-16 snapshot repairs.
- Direct consumers: Owner local CLI, future Architect/QA audits, production DB diagnostics.

## Output Contract

The audit artifact reports:

- `read_only`, `db_write`, `schema_change`, `live_telegram`
- table profiles and duplicate business-key checks
- `daily_price` OHLCV validity and stock coverage
- `daily_signal_snapshot` current-version consistency against `daily_price`
- current strategy-window snapshot coverage from `--coverage-start-date`
- `fix_issues`, `review_items`, and summary counts

## Failure Specimen And Acceptance Route

Failure specimen:

- Owner observed multi-day cards that appeared to infer yesterday/today/continuous moves without trustworthy DB backing.
- Owner asked whether DB tables contained repeated fake-looking values.

Acceptance route:

1. Run read-only all-table audit.
2. Run daily signal snapshot prune dry-run.
3. Repair only confirmed mismatched current-version rows through approved backfill.
4. Rerun read-after-write audit.
5. Rerun official generator dry-run to verify report generation still works.

## Acceptance Criteria

- `daily_price` has no duplicate `(stock_id, trade_date)` and no invalid OHLCV rows.
- `daily_signal_snapshot` has no duplicate `(stock_id, trade_date, version)`.
- Current two-year strategy window has zero missing `v21.1` snapshots where daily_price is eligible.
- Read-after-write audit has `fix_issue_count=0`.
- Prune dry-run has `delete_candidate_rows=0` after repair.
- Official `generate_report(dry_run=True)` still returns message list without live delivery.
