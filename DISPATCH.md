# DISPATCH.md

## Active

- task_md_holds: `low_repair_intraday_buy_v21_1_20260622`
- status: `implemented + verification passed + git completion passed`
- current_version: `v21.1`
- live Telegram delivery: `not run`
- DB schema change: `none`
- DB write/backfill/delete: `none`

## Result Summary

- Fixed the remaining low-repair transition gap:
  - after-hours complete low-repair stays `可準備`
  - intraday complete low-repair can become `可買｜小倉`
  - incomplete / source-ineligible cases do not become buy recommendations
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
- Manual negative source probe:
  - no `可買｜小倉`
- Official dry-run:
  - `messages=4`
  - no live Telegram

## Current Git State

- This cycle is committed and pushed to `origin/main`.
- Git completion gate passed.

## Next Action

- Monitor the next intraday run: complete low-repair candidates should show `可買｜小倉`; after-hours should remain `可準備`.
