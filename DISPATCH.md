# DISPATCH.md

## Active

- task_md_holds: `intraday_report_state_readability_v21_1_20260624`
- status: `implemented + QA passed`
- current_version: `v21.1`
- live Telegram delivery: `not run`
- DB schema change: `none`
- DB write/backfill/delete: `none`

## Result Summary

- Intraday holding cards now use `盤中處理` instead of `明日處理`.
- Low-repair near-ready cards now show `貼近可買｜低位修復接近成立` when the only missing condition is reclaiming the 5-day MA within the configured tolerance.
- Failed-breakout cards with a real reclaim zone and distance within 5% now show `等站回｜突破失敗`, not terminal `淘汰`.
- `等站回` cards are compact and do not show duplicate trade-state / data lines.

## Verification

- Focused current-contract tests: `3 passed, 223 deselected`.
- Broader related subset: `11 passed, 215 deselected`.
- Official dry-run: `messages=4`; `HAS_NEAR_BUY=True`; `HAS_WAIT_RECLAIM=True`; `INTRADAY_TOMORROW_LABEL=False`.

## Current Git State

- Implementation is ready for commit / push.

## Next Action

- Run git status, commit, push, and completion gate.
