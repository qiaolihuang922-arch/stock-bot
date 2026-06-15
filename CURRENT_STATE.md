# CURRENT_STATE.md

## Current Task

- task_id: `report_conflict_entry_gate_v21_0_5_20260615`
- status: `complete`
- version: `v21.0.5`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; wording must be decision-first and avoid internal pipeline noise.
- Production dispatch model is Render web service called every five minutes, then GitHub workflow dispatch.
- Production source-of-truth remains Supabase / runner data, not local cache.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval.
- Non-schema DB write/backfill must use existing approved repo scripts or service APIs; direct hand-written production DML is forbidden.

## Current Changes

- Market-wide weakness and individual-stock weakness are no longer conflated.
- Source/data failure is not inferred from missing report-only context.
- Unheld blockers now separate:
  - market gate;
  - individual stock weakness;
  - setup/distance;
  - volume confirmation;
  - heat/cooldown;
  - RR repair;
  - real data/source failure.
- The current official dry-run has no valid buy signal.

## Verification State

- `tests/test_trade_state_machine.py tests/test_generator_report.py tests/test_market_theme_evidence.py`:
  - `246 passed, 145 warnings, 57 subtests passed`.
- Official dry-run confirmed:
  - `v21.0.5`.
  - no R2-versus-market-weak conflict.
  - no next-day/data-state conflict.
  - no `entry quality low` visible noise.
  - no valid new buy emitted.
  - `聯電` is represented as RR repair, not data failure.

## Known Follow-ups

- Live Telegram delivery not tested by design.
- Strategy remains rule-based; bottom buying requires confirmed setup/RR/heat cooldown, not just a low price.
