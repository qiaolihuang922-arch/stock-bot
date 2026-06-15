# DISPATCH.md

## Active

- task_md_holds: `summary_brief_mobile_denoise_20260616`
- status: `implemented + QA passed + pushed`
- current_version: `v21.1`
- no live Telegram delivery in this cycle.

## Result Summary

- Owner requested summary/brief denoise after 06/16 pre-market third message showed too much non-actionable text.
- Implemented decision-summary cleanup:
  - removed rendered `📎 詳情索引`;
  - removed normal source plumbing from third-message brief;
  - removed generic `原因：...` and `風險：...` rows from brief;
  - removed fixed `持倉：依第一則既有卡片處理...` line for ordinary holdings;
  - changed rejected trace to `淘汰：N 檔｜主因：...` without `詳情見未持倉卡`.
- Preserved actionable content:
  - market/action count;
  - new-entry status;
  - today's risk-control plan;
  - holding control checklist;
  - unheld status/funnel;
  - rejected main reason;
  - stale `LAST_OHLCV` source warning.
- Strategy calculations and blockers are unchanged.
- Header/runtime version remains `v21.1`.

## Verification

- Dry-run:
  - `generate_report(dry_run=True)`
  - third-message forbidden counts all zero: `詳情索引`, normal `📡 資料`, `原因`, `風險`, `持倉：依第一則`, `詳情見未持倉卡`.
- Tests:
  - command: `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q --tb=short`
  - result: `203 passed, 44 subtests passed`
  - command: `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - result: `479 passed, 8 skipped, 108 subtests passed`
- No live Telegram delivery.
- No DB schema change/write/backfill.

## Current Git State

- branch: `main`
- upstream: `origin/main`
- latest commit: `git log -1 --oneline`
- HEAD equals upstream: `true after closeout push`
- worktree/index: `clean after closeout push`

## Next Action

- Observe next scheduled `run_mode=bot` report and confirm production Telegram artifact keeps the compact third-message summary.
