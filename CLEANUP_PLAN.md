# CLEANUP_PLAN.md

## Completed This Cycle

- Completed `report_state_sync_v21_1_20260617`:
  - retest wording now follows current price vs retest basis instead of fixed `尚未回測`
  - warning-line breaches override stale `未跌破風控`
  - overheat vs limit-up wording is separated
  - wait-volume cards show current ratio and target threshold
  - after-hours summary filler was removed
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

- Continue strategy calibration separately from display-state sync:
  - a card can now explain wait/fail states more clearly, but this cycle did not change core entry-gate thresholds.
  - next calibration should use DB replay/outcome evidence, not new hard-coded single-stock rules.
- Strategy calibration from replay outcome flags:
  - blocked `遠離觸發`, `等低位修復`, `等回測`, `等量能`, and `RR不足` groups had positive 5-day follow-through in the 120-day audit.
  - This needs a separate PM/Tech/QA cycle focused on entry gate calibration, not DB cleanup.
- If Owner wants the legacy `trades` table removed, create an approved prune/delete script with dry-run, write confirmation, and read-after-prune verification.

## Persistent Rule Reminder

- Report cards should describe data events that already happened, not repeat a desired state:
  - if price is below a retest basis, do not say `尚未回測`
  - if price is below warning, do not say `未跌破風控`
  - if current day is not near limit-up, do not say `漲停`
- DB data repairs must use approved scripts/service APIs.
- Deletion must have a dry-run plan first.
- If delete candidate count is `0`, record `deleted_rows=0` and do not hard delete.
