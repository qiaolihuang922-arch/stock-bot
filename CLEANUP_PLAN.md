# CLEANUP_PLAN.md

## Completed This Cycle

- Removed a user-visible contradiction in intraday low-repair cards:
  - before: `可買｜小倉` could coexist with `交易狀態：等資料`
  - after: executable low-repair cards show `交易狀態：可買｜動作：小倉試單`
- Clarified after-hours low-repair:
  - after-hours is preparation only
  - next action requires open confirmation, support / 5-day MA hold, and volume not losing control
- Added regression coverage for both visible cases.

## Cleanup Notes

- No obsolete files were deleted.
- No DB data was pruned or rewritten.
- No live Telegram was sent.

## Follow-Ups

- Continue broader DB replay calibration separately for:
  - breakout route
  - retest route
  - cooling route
  - holding add/reduce route
- Consider a full repository-wide test pass in a separate cycle.

## Persistent Rule Reminder

- If a card title says a stock is executable, state line, buy line, and trigger must also say executable.
- If a card is only after-hours preparation, it must not read like an immediate buy.
- Avoid generic blockers such as `等資料` unless the actual hard source failure is named.
