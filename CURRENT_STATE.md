# CURRENT_STATE.md

## Current Task

- task_id: `intraday_report_state_readability_v21_1_20260624`
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
- `貼近可買` is not a buy signal; it means only one small condition remains.

## Current Implementation State

- Holding cards:
  - `盤中` -> `盤中處理`
  - `盤前` -> `盤前處理`
  - after-hours / close -> `明日處理`
- Low-repair near-ready:
  - computed from DB-backed daily price context.
  - requires all low-repair conditions except reclaiming 5-day MA.
  - only displays near-ready when 5-day MA gap is within 0.8%.
- Failed breakout reclaim:
  - requires a real reclaim anchor from `retest_zone_low`, `breakout_trigger_price`, or `breakout_price`.
  - within 5% becomes `等站回`, not `淘汰`.
  - no anchor means it stays blocked; no fake zone is invented.

## Verification State

- Focused current-contract tests: `3 passed, 223 deselected`.
- Broader related subset: `11 passed, 215 deselected`.
- Official dry-run: `messages=4`; `HAS_NEAR_BUY=True`; `HAS_WAIT_RECLAIM=True`; `INTRADAY_TOMORROW_LABEL=False`.
- No production DB data was changed.

## Known Findings

- Full `tests/test_generator_report.py` still has legacy expectation failures from older report wording.
- `.pytest_cache` warning may appear due local Windows permission; focused tests pass despite it.

## Next Action

- Report verification, hash, push target, and upstream equality.
