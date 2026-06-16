# DISPATCH.md

## Active

- task_md_holds: `strategy_buy_path_db_replay_audit_v21_1_20260616`
- status: `implemented + QA passed + full pytest passed`
- current_version: `v21.1`
- no live Telegram delivery in this cycle.
- no DB schema/write/backfill/prune in this cycle.

## Result Summary

- Owner asked for DB replay to verify whether the current strategy is deadlocked.
- Implemented read-only replay:
  - `scripts/audit_strategy_buy_path_replay.py`
  - artifact: `reports/audit/strategy_buy_path_replay_v21_1_20260616.json`
- Main result:
  - real buyable path exists: `700` buyable/trend stock-days;
  - including prepare: `1035` stock-days;
  - funnel false-negative over raw tradeable snapshots: `0`;
  - `等回測` is not guaranteed to become buy; it often moves to cooling / approach / reject.

## Verification

- Targeted tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_strategy_buy_path_replay.py tests\test_dry_run_replay.py -q --tb=short`
  - result: `6 passed, 1 warning`
- Full:
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - result: `486 passed, 8 skipped, 165 warnings, 110 subtests passed`
- DB replay:
  - `.\.venv\Scripts\python.exe scripts\audit_strategy_buy_path_replay.py --lookback-days 730 --version v21.1 --output reports\audit\strategy_buy_path_replay_v21_1_20260616.json`
  - result: artifact generated.

## Current Git State

- branch: `main`
- latest pushed commit: `1b0ec5f`
- completion: git completion passed after push.

## Next Action

- Review replay artifact with Owner; next optional step is outcome replay for buyable signals.
