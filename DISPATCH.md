# DISPATCH.md

## Active

- task_md_holds: `compact_actionable_buy_card_v21_1_20260624`
- status: `implemented + QA passed`
- current_version: `v21.1`
- live Telegram delivery: `not run`
- DB schema change: `none`
- DB write/backfill/delete: `none`

## Result Summary

- Low-repair actionable buy cards now show a compact small-position instruction instead of repeating trade-state, buy-point, reason, and data lines.
- The card keeps the useful parts:
  - action: small test position, do not chase.
  - condition snapshot: support / 5-day MA / volume.
  - one trigger line.
  - price.
- Summary backtest lines with `無明顯優勢` are hidden because they do not change the action.

## Verification

- Low-repair tests: `5 passed, 220 deselected`.
- Backtest/direct-action/prepare subset: `21 passed, 204 deselected`.
- Related report readability subset: `27 passed, 198 deselected`.
- Official dry-run: `messages=4`; old low-repair buy-card noise absent; compact buy line present; no-edge backtest summary hidden.

## Current Git State

- Pending commit / push for this task.

## Next Action

- Commit and push the compact actionable buy-card patch.
