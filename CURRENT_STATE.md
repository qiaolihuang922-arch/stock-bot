# CURRENT_STATE.md

## Current Task

- task_id: `actionable_report_contract_v21_1_20260623`
- status: `implemented + focused verification passed`
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

- Holding next-step lines now use warning / stop prices instead of generic breakout-zone recovery wording.
- Sharp overheat pullback cards now say `急殺回測，先不接刀` and require `止跌守支撐 + 量能不失控`.
- Failed-breakout cards now show the actual breakout zone and current-price gap when zone data exists.
- Official dry-run confirms the actual message list includes the new holding, unheld, and summary behavior.

## Verification State

- Focused tests: `6 passed, 219 deselected`.
- Holding/today-buy subset: `8 passed, 217 deselected`.
- Related report subset: `14 passed, 211 deselected`.
- Official dry-run: `messages=4`, no live Telegram, key checks true.
- Full `tests/test_generator_report.py`: `206 passed, 22 failed`.
- No production DB data was changed.

## Known Findings

- Full report tests still contain legacy / stale expectations. Separate cleanup should decide which v19/v20 assertions to update or retire.
- `.pytest_cache` warning may appear due local Windows permission; focused tests pass despite the warning.

## Next Action

- Final response must report commit hash, push target, and upstream equality.
- If Owner asks for next cleanup: target full-test legacy expectations and summary readability debt.
