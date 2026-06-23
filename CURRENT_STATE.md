# CURRENT_STATE.md

## Current Task

- task_id: `intraday_display_state_sync_v21_1_20260623`
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

- Trading-day phase fallback now keeps 13:00-13:19 as `盤中` and uses `收盤` from 13:20.
- Summary display buckets now map already-pulled-back overheat names from raw `等冷卻` to visible `等回測`.
- Overheat pullback triggers are concrete and match the card body.
- Rejected cards no longer show `觀察` as the primary reason.
- Failed breakout market line no longer presents positive attack-volume wording.
- Low-repair cards show numeric distance to missing MA/support levels.

## Verification State

- Focused tests: `7 passed, 217 deselected`.
- Related report subset: `26 passed, 198 deselected`.
- Official dry-run: `messages=4`, no live Telegram.
- No production DB data was changed.

## Known Findings

- Full `tests/test_generator_report.py` still has legacy expectation failures: `215 passed, 12 failed`.
- `.pytest_cache` warning may appear due local Windows permission; focused tests pass despite the warning.

## Next Action

- Final response must report commit hash, push target, and upstream equality.
- If Owner asks for next cleanup: update stale full-test expectations and further simplify summary section.
