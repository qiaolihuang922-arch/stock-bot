# CURRENT_STATE.md

## Current Task

- task_id: `report_actionability_readability_v21_1_20260624`
- status: `implemented + QA passed + pushed`
- version: `v21.1`
- live Telegram delivery: not run
- DB schema change: none
- DB write/backfill/delete: none

## Stable Context

- Owner reads Telegram on mobile; every card must answer what is happening now, what exact condition is missing, and when it becomes actionable.
- Cross-day state must come from production DB or an approved persistent source, not agent memory.
- DB structure changes require Owner approval.
- No live Telegram delivery without separate Owner approval.
- `貼近條件` is not a buy signal; only `可買` is actionable.

## Current Implementation State

- Low-repair near-ready:
  - title uses `貼近條件｜等站回5日均`.
  - trigger names only the missing gate.
  - volume label uses qualitative wording.
- Failed breakout reclaim:
  - requires a real reclaim anchor.
  - within 7% becomes `等站回`.
  - 5%~7% distance line displays `站回觀察`.
- Summary:
  - no `執行動作 0`.
  - no `今日新建倉 0`.
  - no standalone backtest line for non-actionable prepare-only cards.
- History:
  - no raw `前次 eliminated` or `權重 +1` wording in official dry-run.

## Verification State

- Focused current-contract tests: `5 passed, 222 deselected`.
- Broader related subset: `10 passed, 217 deselected`.
- Official dry-run:
  - `messages=4`.
  - `HAS_NEAR_BUY=False`.
  - `HAS_NEAR_CONDITION=True`.
  - `HAS_WAIT_RECLAIM=True`.
  - `HAS_ELIMINATED=False`.
  - `HAS_BACKTEST_STANDALONE=False`.
  - `HAS_ZERO_ACTION=False`.
  - `INTRADAY_TOMORROW_LABEL=False`.
- No production DB data was changed.

## Known Findings

- Full `tests/test_generator_report.py` still has legacy expectation failures from older report wording.
- `.pytest_cache` warning may appear due local Windows permission; focused tests pass despite it.

## Next Action

- Run git completion gate and report final status.
