# CURRENT_STATE.md

## Current Task

- task_id: `premarket_phase_report_v21_0_6_20260615`
- status: `complete`
- version: `v21.0.6`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; wording must be decision-first and avoid internal pipeline noise.
- Production dispatch model is Render web service called every five minutes, then GitHub workflow dispatch.
- Production source-of-truth remains Supabase / runner data, not local cache.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval.
- Non-schema DB write/backfill must use existing approved repo scripts or service APIs; direct hand-written production DML is forbidden.

## Current Changes

- Trading weekday before 09:00 is `盤前`.
- `盤前` is a today-action phase:
  - no `非交易` header;
  - no `明日計畫`;
  - unheld trigger wording uses `盤前觀察`.
- `盤中` wording remains unchanged.

## Verification State

- `tests/test_trade_state_machine.py tests/test_generator_report.py tests/test_market_theme_evidence.py`:
  - `248 passed, 147 warnings, 57 subtests passed`.
- Patched-time official dry-run confirmed:
  - `【06/15 盤前｜v21.0.6】`;
  - phase `盤前`;
  - no `06/15 非交易`;
  - no `明日計畫`.

## Known Follow-ups

- Live Telegram delivery not tested by design.
- Holiday confirmation beyond weekend checks remains part of the broader source/evidence workflow, not this patch.
