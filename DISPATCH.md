# DISPATCH.md

## Active

- task_md_holds: `limit_lock_primary_reason_v21_1_20260622`
- status: `implemented + verification passed + git completion passed`
- current_version: `v21.1`
- live Telegram delivery: `not run`
- DB schema change: `none`
- DB write/backfill/delete: `none`

## Result Summary

- Fixed lock-up / overheated unheld cards so the visible primary reason is no-chase / wait-retest, not RR or technical score.
- `LIMIT_LOCK` / `漲停不追` now appears as `等回測｜漲停不追`.
- `LIMIT_REBOUND` / `漲停反彈待確認` now appears as `隔日確認`.
- Failed breakout remains structure-led and is not softened into a retest just because it is limit-like.

## User-Visible Contract

- Locked limit-up:
  - `狀態：漲停/過熱，不追價`
  - `等待：解除鎖定後，看開板回測是否守住`
  - `有效買點：開板/降溫 + 回測不破 + 非追高`
- Low-repair:
  - unchanged from previous cycle.
  - intraday complete checklist -> `可買｜小倉`.
  - after-hours complete checklist -> `可準備`.

## Verification

- Related report tests: `24 passed, 193 deselected, 2 subtests passed`
- Official dry-run: `messages=4`, `live_telegram=False`
- No live Telegram.
- No DB write.

## Current Git State

- This follow-up is committed and pushed to `origin/main`.
- Git completion gate passed.

## Next Action

- Monitor the next limit-up / overheated unheld cards: they should show no-chase / wait-retest as the primary reason, not RR or score blockers.
