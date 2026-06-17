# CLEANUP_PLAN.md

## Completed This Cycle

- Added a reusable DB data-quality audit script.
- Separated real data errors from expected constant/null source fields.
- Repaired three confirmed stale `daily_signal_snapshot` rows through the approved backfill script.
- Verified read-after-write:
  - no remaining fix issues
  - no current-window snapshot gaps
  - no duplicate snapshot rows
- Confirmed no rows were safe to delete in this cycle.
- Kept local evidence under ignored `artifacts/`.

## Cleanup Notes

- `artifacts/` is ignored because it contains local DB audit evidence and should not be committed.
- The old `trades` table still has one legacy row. No current code path was found calling `supabase.table("trades")`; table cleanup should be a separate DB prune/delete task with an approved interface.
- `signal_runs`, `signal_items`, and `signal_outcomes` are still consumed by `services.signal_store` and monitoring/diagnostic code; they are not dead tables.
- `market_theme_index_daily_bars` has null OHLC/volume fields by source limitation; current consumer uses close/change and confirmed evidence breadth.

## Follow-Ups

- Strategy calibration from replay outcome flags:
  - blocked `遠離觸發`, `等低位修復`, `等回測`, `等量能`, and `RR不足` groups had positive 5-day follow-through in the 120-day audit.
  - This needs a separate PM/Tech/QA cycle focused on entry gate calibration, not DB cleanup.
- If Owner wants the legacy `trades` table removed, create an approved prune/delete script with dry-run, write confirmation, and read-after-prune verification.

## Persistent Rule Reminder

- DB data repairs must use approved scripts/service APIs.
- Deletion must have a dry-run plan first.
- If delete candidate count is `0`, record `deleted_rows=0` and do not hard delete.
