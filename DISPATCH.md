# DISPATCH.md

## Active

- task_md_holds: `report_actionability_readability_v21_1_20260624`
- status: `implemented + QA passed + pushed`
- current_version: `v21.1`
- live Telegram delivery: `not run`
- DB schema change: `none`
- DB write/backfill/delete: `none`

## Result Summary

- Low-repair near-ready no longer says `貼近可買`; it now says `貼近條件｜等站回5日均`.
- Low-repair trigger lines now list only the missing gates.
- Volume display now uses `不足 / 剛好 / 有效 / 攻擊量`.
- Failed-breakout reclaim watch band is now 7% when a real reclaim zone exists.
- Engineering history terms such as `前次 eliminated` no longer appear in the user-facing report.
- Summary no longer shows zero-count action lines or standalone backtest snippets for non-actionable prepare-only cards.

## Verification

- Focused current-contract tests: `5 passed, 222 deselected`.
- Broader related subset: `10 passed, 217 deselected`.
- Official dry-run: `messages=4`; `HAS_NEAR_BUY=False`; `HAS_NEAR_CONDITION=True`; `HAS_WAIT_RECLAIM=True`; `HAS_ELIMINATED=False`; `HAS_ZERO_ACTION=False`; `INTRADAY_TOMORROW_LABEL=False`.

## Current Git State

- Implementation commit: `f3c4377`.
- Dispatch state commit: `ebe0f37`.
- Pushed to `origin/main`; git completion gate passed by equivalent PowerShell checks.

## Next Action

- None for this task.
