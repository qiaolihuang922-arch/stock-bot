# CLEANUP_PLAN.md

## Completed This Cycle

- Completed low-repair state/display sync for `06/22 盤後｜v21.1`.
- Removed the misleading state where a card said all low-repair conditions were met but remained in `等低位修復`.
- Kept after-hours action conservative:
  - all conditions met -> `可準備`
  - not immediate `可買`
  - next-session confirmation still required
- Fixed unheld funnel count semantics:
  - `隔日確認` is not counted inside `僅追蹤`
  - empty summary parentheses are suppressed

## Cleanup Notes

- No DB schema or production data changes were made.
- No live Telegram was sent.
- Existing local `.pytest_cache` permission warning remains environmental.

## Follow-Ups

- Separate task needed: `test_v20_4_47_generate_report_appends_live_readonly_future_watch_sources` currently fails because future-watch global lines are `0`.
- Continue strategy calibration separately from display-state sync:
  - low-repair readiness now has a coherent state transition
  - broader entry gate calibration still needs DB replay/outcome evidence

## Persistent Rule Reminder

- If a card says every condition is satisfied, the state must not remain in a waiting bucket for the same route.
- If a condition is hidden, either display it or remove it as a gate; do not let hidden blockers contradict the visible checklist.
- Summary buckets must be mutually exclusive unless the text explicitly says they overlap.
