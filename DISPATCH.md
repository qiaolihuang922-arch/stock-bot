# DISPATCH.md

## Active

- task_md_holds: `actionable_report_contract_v21_1_20260623`
- status: `implemented + focused verification passed`
- current_version: `v21.1`
- live Telegram delivery: `not run`
- DB schema change: `none`
- DB write/backfill/delete: `none`

## Result Summary

- Holding cards now show concrete warning / stop price actions instead of generic breakout recovery wording.
- Sharp overheat pullbacks now avoid catch-the-falling-knife ambiguity.
- Failed breakout cards now display reclaim zone and current-price gap.
- Official dry-run message list confirms the user-visible route.

## Verification

- Focused tests: `6 passed, 219 deselected`.
- Holding/today-buy subset: `8 passed, 217 deselected`.
- Related report subset: `14 passed, 211 deselected`.
- Official dry-run: `messages=4`, no live Telegram, key checks true.
- Full report test file: `206 passed, 22 failed`; residual legacy expectation debt remains outside this focused fix.

## Current Git State

- Implementation will be committed and pushed in this cycle; final response reports the verified hash and upstream equality.

## Next Action

- Final response must report commit hash, push target, and upstream equality.
- Separate follow-up: clean stale v19/v20 report tests and decide which old source / summary / action wording assertions should be retired.
