# DISPATCH.md

## Active

- task_md_holds: `multi_day_rebound_retest_v21_1_20260616`
- status: `implemented + QA passed + pushed`
- current_version: `v21.1`
- no live Telegram delivery in this cycle.
- no DB schema/write/backfill in this cycle.

## Result Summary

- Owner reported 旺宏 had risen for three days but was still shown as `淘汰｜弱反彈待確認`.
- Implemented multi-day rebound repair:
  - `WEAK_REBOUND` with recent three rising moves and >=5% rebound is no longer hard rejected;
  - it becomes `等回測｜反彈修復待回測`;
  - single-day +7% rebound still uses `急彈待回測`;
  - `decision=FAIL` / `FAILED_BREAKOUT` remain `淘汰`.
- Official dry-run now shows 旺宏 as `等回測｜反彈修復待回測`, not `淘汰`.

## Verification

- Dry-run:
  - `generate_report(dry_run=True)`
  - checked official unheld message.
- Targeted tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q --tb=short -k "weak_rebound or rebound or v21_1_multi_day"`
  - result: `2 passed`
- Full tests:
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - result: `480 passed, 8 skipped, 108 subtests passed`
- No live Telegram delivery.
- No DB schema/write/backfill.

## Current Git State

- branch: `main`
- upstream: `origin/main`
- worktree/index: clean after closeout push
- HEAD equals upstream: true after closeout push

## Next Action

- Observe next scheduled `run_mode=bot` report and confirm production Telegram artifact matches dry-run wording.
