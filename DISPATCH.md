# DISPATCH.md

## Active

- task_md_holds: `approach_distance_gap_v21_1_20260616`
- status: `implemented + QA passed + pushed`
- current_version: `v21.1`
- no live Telegram delivery in this cycle.
- no DB schema/write/backfill in this cycle.

## Result Summary

- Owner reported that `等接近` cards still showed `個股弱勢` and generic gap/unlock text.
- Implemented formatter correction:
  - `等接近` title label is `遠離觸發`;
  - gap is distance-specific: `距突破 X%，仍未進入觸發區`;
  - unlock is actionable: `接近觸發區，或出現趨勢延續/回測承接買點型態`.
- Official dry-run now shows `等接近｜遠離觸發` for approach cards and no generic `需解除後重新評估` in those cards.

## Verification

- Dry-run:
  - `generate_report(dry_run=True)`
  - checked unheld official message.
- Targeted tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py tests\test_trade_state_machine.py -q --tb=short`
  - result: `212 passed, 44 subtests passed`
- Full tests:
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - result: `479 passed, 8 skipped, 108 subtests passed`
- No live Telegram delivery.
- No DB schema/write/backfill.

## Current Git State

- branch: `main`
- upstream: `origin/main`
- latest commit: `4d4fd8e Clarify approach distance gaps`
- HEAD equals upstream: true after push
- worktree/index: clean after closeout push

## Next Action

- Observe next scheduled `run_mode=bot` report and confirm production Telegram artifact matches dry-run wording.
