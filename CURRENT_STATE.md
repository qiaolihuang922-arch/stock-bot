# CURRENT_STATE.md

## Current Task

- task_id: `actionable_report_contract_v21_1_20260623`
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

- Holding next-step and summary lines use warning / stop prices instead of generic breakout-zone recovery wording.
- Overheat, low-repair, and failed-breakout unheld cards now use a compact `狀態/低位修復 + 明日觸發` contract.
- `可準備（不可買）` has been replaced by `準備觀察（待確認）` on the user-visible route.
- Official dry-run confirms the actual message list no longer contains duplicate `等待：熱度` / `有效買點：` patterns.

## Verification State

- Focused tests: `5 passed, 220 deselected`.
- Related report readability subset: `27 passed, 198 deselected`.
- Official dry-run: `messages=4`; duplicate wait/effective-buy pattern absent; low-repair one-trigger check true; failed-breakout compact check true; summary risk-price check true.
- No production DB data was changed.

## Known Findings

- Full report tests may still contain legacy / stale expectations. Separate cleanup should decide which v19/v20 assertions to update or retire.
- `.pytest_cache` warning may appear due local Windows permission; focused tests pass despite the warning.

## Next Action

- Commit and push this readability fix, then report commit hash, push target, and upstream equality.
- If Owner asks for next cleanup: target full-test legacy expectations and future-watch/source wording debt.
