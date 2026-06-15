# CURRENT_STATE.md

## Current Task

- task_id: `acute_rebound_retest_anchor_v21_0_9_20260615`
- status: `complete`
- version: `v21.0.9`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; wording must be decision-first and avoid internal pipeline noise.
- Production dispatch model is Render web service called every five minutes, then GitHub workflow dispatch.
- Production source-of-truth remains Supabase / runner data, not local cache.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval.
- Non-schema DB write/backfill must use existing approved repo scripts or service APIs; direct hand-written production DML is forbidden.

## Current Changes

- Acute rebound wait cards now explain both sides:
  - why not buy now: `急彈追價區，尚未回測`;
  - what can make it buyable later: `回測前高/突破區不破 + 非漲停追價 + 量能有效 + 品質B以上 + RR>=1.5`.
- Real RR is preserved on acute rebound wait cards when available, preventing a visible conflict between `RR達標` and `RR -`.
- Limit-up / overheat hard blockers were explicitly protected by focused tests.

## Verification State

- Focused acute/limit-up specimens:
  - `3 passed`.
- `tests/test_trade_state_machine.py tests/test_generator_report.py tests/test_market_theme_evidence.py`:
  - `249 passed, 149 warnings, 57 subtests passed`.
- Official dry-run confirmed:
  - `v21.0.9`;
  - retest anchor condition line present in generated 旺宏 card;
  - no live Telegram delivery;
  - no current 旺宏 weak-rebound reject string in generated dry-run output.

## Known Follow-ups

- Strong rebound threshold is rule-based, not learned from DB outcomes yet.
- `品質B以上` is internal composite strategy quality; future calibration should define which DB-backed features move D to B.
- Git closeout completed for the current version when this file was last updated.


