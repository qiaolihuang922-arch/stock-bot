# CLEANUP_PLAN.md

## Completed This Cycle

- Removed noisy RR / quality / score display from lock-up cards.
- Promoted lock-up / no-chase as the visible primary reason for limit-like unheld candidates.
- Preserved structure-failure priority over lock-up display.
- Added regression coverage to prevent `等風險報酬` from reappearing on pure lock-up cards.

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

- A card should show only the active primary blocker first.
- Lock-up / overheated names should not expose RR or score as the active reason until the stock is tradable again.
- If structure has failed, keep structure failure ahead of lock-up display.
