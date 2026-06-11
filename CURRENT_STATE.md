# CURRENT_STATE.md

## Current Task

- task_id: `report_noise_conflict_v21_0_3_20260611`
- status: `complete`
- version: `v21.0.3`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; wording must be decision-first and avoid internal pipeline noise.
- Production dispatch model is Render web service called every five minutes, then GitHub workflow dispatch.
- Production source-of-truth remains Supabase / runner data, not local cache.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval.
- Non-schema DB write/backfill must use existing approved repo scripts or service APIs; direct hand-written production DML is forbidden.

## Current Changes

- Intraday report wording changed from execution wording to risk-advice wording.
- Direct risk holding cards are shorter and keep only high-value action context.
- Unheld `等資料` handling is scoped to state-machine-confirmed data recovery; it no longer swallows normal wait buckets.
- Historical analogy includes a confidence limitation when volume is missing.

## Verification State

- `tests/test_generator_report.py tests/test_trade_state_machine.py tests/test_market_theme_evidence.py`:
  - `244 passed, 145 warnings, 57 subtests passed`.
- Official dry-run confirmed:
  - `v21.0.3`.
  - old `今日盤中交易執行` wording absent.
  - new `今日盤中風控建議` wording present.
  - historical confidence note present.

## Known Follow-ups

- Live Telegram delivery not tested by design.
- During market hours, live/read-only prices can move between dry-runs, so exact per-stock percentage/classification may drift.
