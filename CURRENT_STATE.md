# CURRENT_STATE.md

## Current Task

- task_id: `strong_rebound_not_weak_v21_0_7_20260615`
- status: `complete`
- version: `v21.0.7`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; wording must be decision-first and avoid internal pipeline noise.
- Production dispatch model is Render web service called every five minutes, then GitHub workflow dispatch.
- Production source-of-truth remains Supabase / runner data, not local cache.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval.
- Non-schema DB write/backfill must use existing approved repo scripts or service APIs; direct hand-written production DML is forbidden.

## Current Changes

- Strong intraday rebound semantics were added:
  - raw `WEAK_REBOUND` plus live/day change >= 7% becomes `急彈待回測`;
  - state is `等回測`;
  - action remains wait / no chase;
  - low-change weak rebound still rejects as weak.
- Trade state machine can show `主因：急彈待回測`.
- Telegram card reason can show `卡關主因：急彈未回測`.

## Verification State

- `tests/test_trade_state_machine.py tests/test_generator_report.py tests/test_market_theme_evidence.py`:
  - `249 passed, 149 warnings, 57 subtests passed`.
- Official dry-run confirmed:
  - `v21.0.7`;
  - no live Telegram delivery;
  - no current 旺宏 weak-rebound reject string in generated dry-run output.

## Known Follow-ups

- Strong rebound threshold is rule-based, not learned from DB outcomes yet.
- Future strategy-quality work should evaluate thresholds from historical outcomes before changing buyability.
