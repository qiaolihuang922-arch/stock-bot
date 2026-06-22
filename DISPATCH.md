# DISPATCH.md

## Active

- task_md_holds: `low_repair_remove_meaningless_source_gate_v21_1_20260622`
- status: `implemented + verification passed + git completion passed`
- current_version: `v21.1`
- live Telegram delivery: `not run`
- DB schema change: `none`
- DB write/backfill/delete: `none`

## Result Summary

- Removed the meaningless generic source-eligibility gate from low-repair `可買`.
- Low-repair now blocks only explicit source-error / unresolved-conflict.
- Missing context or strategy sample insufficiency no longer blocks a DB-backed low-repair setup.
- Low-repair `可買` is deliberately conservative:
  - small position only
  - no chasing
  - must keep support / 5-day MA / volume conditions valid
- Summary execution text now recognizes real low-repair buy candidates instead of still saying no buy exists.

## Verification

- Low-repair tests:
  - `4 passed, 213 deselected`
- Related report tests:
  - `17 passed, 200 deselected`
- Source-error negative case:
  - no `可買｜小倉`
- Official dry-run:
  - `messages=4`
  - no live Telegram

## Current Git State

- This follow-up is committed and pushed to `origin/main`.
- Git completion gate passed.

## Next Action

- Monitor the next intraday low-repair candidate: missing strategy context should not block `可買｜小倉`; explicit source-error/conflict should still block.
