# DISPATCH.md

## Active

- task_md_holds: `report_actionability_consistency_v21_1_20260624`
- status: `implemented + QA passed`
- current_version: `v21.1`
- live Telegram delivery: `not run`
- DB schema change: `none`
- DB write/backfill/delete: `none`

## Result Summary

- Low-repair volume gate now matches the wording `量能不失控`: `0.8x~1.0x` is `偏低未失控`, not a hard blocker.
- Low-repair support break now says `已跌破` and requires `重新站回支撐`.
- Low-repair support-broken cards show `等重新築底｜低位修復失效`.
- Breakout-with-low-RR cards now explain `追價風險過高` instead of showing raw tiny RR gaps.
- Failed-breakout reclaim cards show `站回距離偏大` when percent looks close but absolute price gap is still large.
- Low-repair buy cards now read as an action: `可買：小倉試單｜不追價`, with invalidation line.

## Verification

- Focused current-contract tests: `12 passed, 219 deselected`.
- Adjacent message grouping tests: `2 passed, 229 deselected`.
- Official dry-run smoke:
  - `HAS_NEAR_BUY=False`
  - `HAS_RAW_ELIMINATED=False`
  - `HAS_OLD_LOW_BUY=False`
  - `HAS_SUPPORT_WAIT_WHEN_BROKEN_SAMPLE=False`
  - `MESSAGE_COUNT=4`

## Current Git State

- Pending commit/push.

## Next Action

- Commit, push, and run git completion gate.
