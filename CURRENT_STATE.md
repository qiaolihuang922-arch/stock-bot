# CURRENT_STATE.md

## Current Task

- task_id: `compact_actionable_buy_card_v21_1_20260624`
- status: `implemented + QA passed`
- version: `v21.1`
- live Telegram delivery: not run
- DB schema change: none
- DB write/backfill/delete: none

## Stable Context

- Owner reads Telegram on mobile; every card must answer what is happening now, what exact condition is missing, and when it becomes actionable.
- Cross-day state must come from production DB or an approved persistent source, not agent memory.
- DB structure changes require Owner approval.
- No live Telegram delivery without separate Owner approval.

## Current Implementation State

- Low-repair actionable buy cards now render as a compact decision block:
  - `小倉：可試單｜守支撐/5日均｜不追價`
  - `低位修復：支撐 ... OK｜5日均 ... OK｜量能 ... OK`
  - one phase trigger line.
- Old duplicate lines are suppressed for this state:
  - trade-state line.
  - buy-point line.
  - reason line.
  - risk/reward data line.
- Summary backtest grouping hides `無明顯優勢` lines.

## Verification State

- Low-repair tests: `5 passed, 220 deselected`.
- Backtest/direct-action/prepare subset: `21 passed, 204 deselected`.
- Related report readability subset: `27 passed, 198 deselected`.
- Official dry-run: `messages=4`; compact low-repair buy line present; old noisy lines absent; no-edge backtest summary hidden.
- No production DB data was changed.

## Known Findings

- Full report tests may still contain legacy / stale expectations. Separate cleanup should decide which old v19/v20 assertions to update or retire.
- `.pytest_cache` warning may appear due local Windows permission; focused tests pass despite the warning.

## Next Action

- Push commits to `origin/main` and verify HEAD equals upstream.
