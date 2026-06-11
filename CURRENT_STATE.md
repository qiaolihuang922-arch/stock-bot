# CURRENT_STATE.md

## Current Task

- task_id: `entry_distance_strategy_v21_0_4_20260611`
- status: `complete`
- version: `v21.0.4`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; wording must be decision-first and avoid internal pipeline noise.
- Production dispatch model is Render web service called every five minutes, then GitHub workflow dispatch.
- Production source-of-truth remains Supabase / runner data, not local cache.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval.
- Non-schema DB write/backfill must use existing approved repo scripts or service APIs; direct hand-written production DML is forbidden.

## Current Changes

- Distance-to-breakout is no longer a universal `<=4%` rule.
- Breakout/pre-breakout uses `<=5%` pivot buy zone.
- Pullback reclaim and trend continuation are allowed to use their own setup gates.
- Far-without-setup remains non-actionable and waits for approach/setup.
- Telegram display uses strategy-specific distance wording.

## Verification State

- `tests/test_generator_report.py tests/test_trade_state_machine.py tests/test_market_theme_evidence.py`:
  - `246 passed, 145 warnings, 57 subtests passed`.
- Official dry-run confirmed:
  - `v21.0.4`.
  - old `<=4%` wording absent.
  - old intraday execution wording absent.
  - rejected/data-state conflict absent.

## Known Follow-ups

- Live Telegram delivery not tested by design.
- This patch separates rule-based entry paths; it does not yet learn thresholds from historical DB outcomes.
