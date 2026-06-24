# DISPATCH.md

## Active

- task_md_holds: `report_actionability_consistency_v21_1_20260624`
- status: `follow-up implemented + QA passed + pushed`
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
- Warning-breached holdings now show `警戒觀察，不加碼`, not `輕虧不加碼`.
- Low-repair buy cards now show `盤面：低位修復成立｜小倉觀察｜量能分級`.
- Failed-breakout reclaim labels now use absolute gap globally, so large gaps show `站回距離偏大`.

## Verification

- Focused current-contract tests: `12 passed, 219 deselected`.
- Adjacent message grouping tests: `2 passed, 229 deselected`.
- Official dry-run smoke:
  - `HAS_LIGHT_LOSS_WITH_WARNING=False`
  - `HAS_LOW_REPAIR_WEAK_MARKET_BUY=False`
  - `HAS_RAW_TINY_RR_CHASE=False`
  - `MESSAGE_COUNT=1`
- Follow-up focused report tests: `13 passed, 218 deselected`.

## Current Git State

- Implementation commit: `c98ebef`.
- Previous closeout commits: `7acc6aa`, `fcbd2c6`, `9791735`.
- Follow-up implementation commit: `cecbaff`.
- Pushed to `origin/main`; git completion gate pending final closeout commit.

## Next Action

- Commit/push this closeout doc update, then run git completion checks.
