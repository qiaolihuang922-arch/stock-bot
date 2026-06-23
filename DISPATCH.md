# DISPATCH.md

## Active

- task_md_holds: `actionable_report_contract_v21_1_20260623`
- status: `implemented + QA passed`
- current_version: `v21.1`
- live Telegram delivery: `not run`
- DB schema change: `none`
- DB write/backfill/delete: `none`

## Result Summary

- Unheld cards now avoid repeating the same idea across `等待` / `有效買點` / `明日觸發`.
- Low-repair cards show one support / MA / volume snapshot and one trigger.
- Failed breakout cards show reclaim zone and current-price gap in one compact reason line.
- Summary and card labels now use `準備觀察（待確認）` instead of `可準備（不可買）`.
- Holding summary lines now use warning / stop prices.

## Verification

- Focused tests: `5 passed, 220 deselected`.
- Related report readability subset: `27 passed, 198 deselected`.
- Official dry-run: `messages=4`; duplicate wait/effective-buy pattern absent; low-repair one-trigger check true; failed-breakout compact check true; summary risk-price check true.

## Current Git State

- Implementation will be committed and pushed in this cycle; final response reports the verified hash and upstream equality.

## Next Action

- Commit and push this readability fix, then report hash, push target, and upstream equality.
- Separate follow-up: clean stale v19/v20 report tests and decide which old source / future-watch assertions should be retired.
