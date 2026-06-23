# CURRENT_STATE.md

## Current Task

- task_id: `intraday_user_view_state_readability_v21_1_20260623`
- status: `implemented + focused verification passed + git completion passed`
- version: `v21.1`
- live Telegram delivery: not run
- DB schema change: none
- DB write/backfill/delete: none

## Stable Context

- Owner reads Telegram on mobile; every card must answer:
  - what is happening now.
  - what exact condition is missing.
  - when it becomes actionable.
- Cross-day state must come from production DB or an approved persistent source, not agent memory.
- DB structure changes require Owner approval.
- No live Telegram delivery without separate Owner approval.

## Current Implementation State

- Overheat display now depends on current price behavior:
  - positive / locked -> cooling no-chase.
  - pullback <= -2% -> retest confirmation.
  - sharp pullback <= -8% -> support-focused sharp retest.
- Low-repair display uses `low_repair_status` support / MA / volume / RR values and shows only missing conditions.
- Rejected-card history suppresses positive repair lines.

## Verification State

- Focused new tests: `4 passed, 217 deselected`
- Related report subset: `25 passed, 196 deselected`
- Official dry-run: `messages=4`, no live Telegram.
- No production DB data was changed.

## Known Findings

- Full `tests/test_generator_report.py` currently has legacy expectation failures unrelated to this focused fix: `213 passed, 11 failed`.
- `.pytest_cache` warning may appear due local Windows permission; focused tests pass despite the warning.

## Next Action

- Monitor the next 06/23-style intraday cards for title/body consistency.
- If Owner asks for next cleanup: update stale full-test expectations and further simplify summary section.
