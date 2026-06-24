# CURRENT_STATE.md

## Current Task

- task_id: `report_actionability_consistency_v21_1_20260624`
- status: `implemented + QA passed + pushed`
- version: `v21.1`
- live Telegram delivery: not run
- DB schema change: none
- DB write/backfill/delete: none

## Stable Context

- Owner reads Telegram on mobile; every card must answer: can act now, what is missing, and what invalidates the setup.
- Cross-day state must come from production DB or approved persistent source.
- DB structure changes require Owner approval.
- No live Telegram delivery without separate Owner approval.
- `準備觀察` is not buy. Only explicit `可買` is actionable.

## Current Implementation State

- Low-repair:
  - volume gate uses 0.8x not-lost threshold.
  - `support_broken` is persisted in the in-run payload state.
  - support broken cards require reclaim, not waiting to hold.
  - actionable card shows buy action plus invalidation.
- RR after breakout:
  - shows chase-risk wording instead of raw tiny RR gap.
- Failed breakout:
  - reclaim label considers absolute price gap for user readability.

## Verification State

- `12 passed, 219 deselected` for focused report tests.
- `2 passed, 229 deselected` for adjacent message grouping tests.
- Official dry-run smoke passed old-string checks.
- No production DB data was changed.

## Known Findings

- Full `tests/test_generator_report.py` still has older unrelated summary expectations.
- `.pytest_cache` may warn `Permission denied`; tracked git status remains usable with `git -c status.showUntrackedFiles=no`.

## Next Action

- None for this task.
