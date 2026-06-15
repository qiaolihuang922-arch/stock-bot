# DISPATCH.md

## Active

- task_md_holds: `db_table_health_audit_20260615`
- status: `implemented + QA passed`
- current_version: `v21.1`
- no live Telegram delivery in this cycle.

## Result Summary

- Added read-only DB table health audit script: `scripts/audit_db_table_health.py`.
- Audited all current active production tables.
- Found no audit read errors.
- Found no table-specific duplicate issue in the checked keys.
- Classified repeated daily values:
  - expected metadata: source, version, formula, basis, static source labels;
  - real data gaps: market index OHLCV/member placeholders, outcome max high/drawdown, historical `signal_items` new fields.
- Strengthened `signal_items` future write-path test so new strategy fields must be present in fresh payloads.

## Verification

- Production audit:
  - command: `.\.venv\Scripts\python.exe scripts\audit_db_table_health.py`
  - result: `errors=[]`
- Tests:
  - command: `.\.venv\Scripts\python.exe -m pytest tests\test_audit_db_table_health.py tests\test_daily_snapshot_store.py tests\test_analysis_engine.py -q --tb=short`
  - result: `56 passed`
- No live Telegram delivery.
- No DB schema change.
- No production deletion.

## Current Git State

- branch: `main`
- upstream: `origin/main`
- latest commit: `f50e2acd7cde6dd344e7cff264227afde981b9a0`
- HEAD equals upstream: `true`
- worktree/index: `clean`
- closeout uses Windows-equivalent git checks because bash scripts may fail on this machine without WSL/Hyper-V.

## Next Action

- Observe next scheduled `run_mode=bot` report and check fresh `signal_items` rows.
- Plan follow-up for `market_theme_index_daily_bars` OHLCV/member source gap and `signal_outcomes` outcome metrics.
