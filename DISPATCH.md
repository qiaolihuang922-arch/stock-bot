# DISPATCH.md

## Active

- task_md_holds: `holding_card_contract_v21_1_20260616`
- status: `implemented + QA passed + pushed`
- current_version: `v21.1`
- no live Telegram delivery in this cycle.
- no DB schema/write/backfill in this cycle.

## Result Summary

- Owner reported that 06/16 holding cards were still noisy and unlike the optimized unheld cards.
- Implemented holding-card formatter correction:
  - removed visible holding-card `交易狀態 / 數據 / 回測 / 歷史`;
  - retained position-critical fields: `倉位 / 風控 / 盤面 / 距突破 / 價格`;
  - added decision contract: `決策 / 缺口 / 可續抱或可恢復或再進場 / 下一步`;
  - kept fail-closed execution-memory wording for take-profit memory gaps.
- Official dry-run now shows compact holding cards aligned with unheld-card readability.

## Verification

- Dry-run:
  - `generate_report(dry_run=True)`
  - checked official holding message.
- Targeted tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q --tb=short`
  - result: `203 passed, 44 subtests passed`
- Full tests:
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - result: `479 passed, 8 skipped, 108 subtests passed`
- No live Telegram delivery.
- No DB schema/write/backfill.

## Current Git State

- branch: `main`
- upstream: `origin/main`
- worktree/index: clean after closeout push
- HEAD equals upstream: true after closeout push

## Next Action

- Observe next scheduled `run_mode=bot` report and confirm production Telegram artifact matches dry-run wording.
