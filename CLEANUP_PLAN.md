# CLEANUP_PLAN.md

## Completed This Cycle

- Removed the low-repair dead-end where a complete checklist could only remain `可準備`.
- Added an intraday executable route:
  - `盤中` + DB-backed low-repair ready + no core market-data source-error/conflict -> `可買｜小倉`
  - `盤後` / `收盤` -> `可準備`
- Removed generic source availability as a low-repair blocker.
- Explicit core market-data source-error / unresolved-conflict still blocks.
- Strategy evidence remains auxiliary and must not veto DB-backed setups.
- Reduced misleading summary text when a real low-repair buy exists.

## Cleanup Notes

- No DB schema or production data changes were made.
- No live Telegram was sent.
- No obsolete files were deleted in this follow-up.

## Follow-Ups

- Run a full repository-wide test pass in a separate cycle if Owner wants full green status.
- Continue DB replay calibration for broader "why no buy for many days" strategy quality, separate from this low-repair executable transition.

## Persistent Rule Reminder

- A visible checklist that says all required conditions are met must have a clear next state:
  - executable now
  - executable only next session
  - blocked by named source / risk condition
- Do not hide blockers behind generic wording such as `需解除後重新評估`.
