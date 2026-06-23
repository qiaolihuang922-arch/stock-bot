# DISPATCH.md

## Active

- task_md_holds: `intraday_display_state_sync_v21_1_20260623`
- status: `implemented + focused verification passed`
- current_version: `v21.1`
- live Telegram delivery: `not run`
- DB schema change: `none`
- DB write/backfill/delete: `none`

## Result Summary

- Fixed trading-day phase fallback: 06/23 no longer renders as `非交易` during the weekday 13:00 gap.
- Synced summary counts with visible card states for overheat pullbacks.
- Made overheat pullback triggers concrete.
- Removed meaningless `淘汰｜觀察` fallback.
- Prevented failed breakout from displaying positive `攻擊量` / `趨勢量` wording.
- Added low-repair MA/support gap values.

## Verification

- Focused tests: `7 passed, 217 deselected`.
- Related report subset: `26 passed, 198 deselected`.
- Official dry-run: `messages=4`, no live Telegram.
- Full report test file: `215 passed, 12 failed`; residual legacy expectation debt remains outside this task.

## Current Git State

- Implementation will be committed and pushed in this cycle; final response reports the verified hash and upstream equality.

## Next Action

- Final response must report commit hash, push target, and upstream equality.
- Separate follow-up: clean stale v19/v20 report tests and decide which old source/industry wording assertions should be retired.
