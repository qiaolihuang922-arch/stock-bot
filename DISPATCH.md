# DISPATCH.md

## Active

- task_md_holds: `intraday_low_repair_buy_state_sync_v21_1_20260622`
- status: `implemented + verification passed + git completion passed`
- current_version: `v21.1`
- live Telegram delivery: `not run`
- DB schema change: `none`
- DB write/backfill/delete: `none`

## Result Summary

- Fixed the intraday low-repair card contradiction where title/buy text could say `可買｜小倉` while the state line still said `等資料`.
- Intraday low-repair can now show a coherent executable state:
  - `交易狀態：可買｜動作：小倉試單｜條件：守支撐/5日均，不追價`
- After-hours low-repair remains `可準備`, with a clear next-session trigger:
  - `開盤不追高；守支撐/5日均 + 量能不失控，小倉確認`

## When It Can Buy

- Intraday:
  - DB-backed low-repair checklist is complete.
  - No core market-data source error or unresolved conflict.
  - Not overheated / locked limit-up.
  - Price keeps support / 5-day MA and volume is not losing control.
  - Output becomes `可買｜小倉`.
- After-hours / close:
  - Same checklist becomes `可準備`, because execution still needs next-session open confirmation.

## Verification

- Low-repair tests: `4 passed, 213 deselected`
- Related report tests: `14 passed, 203 deselected, 2 subtests passed`
- Official dry-run: `messages=4`, `live_telegram=False`
- No live Telegram.
- No DB write.

## Current Git State

- This follow-up is committed and pushed to `origin/main`.
- Git completion gate passed.

## Next Action

- Monitor the next intraday low-repair candidate: if the checklist is complete during the action phase, the card should say `可買｜小倉`; after-hours should only say `可準備`.
