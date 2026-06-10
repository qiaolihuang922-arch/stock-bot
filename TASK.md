# TASK: future_watch_fundamental_layout_20260610

## Status
- task_id: `future_watch_fundamental_layout_20260610`
- type: `tiny_patch`
- status: `complete`
- version: `v21.0.1`
- QA level: `L1`

## Owner Problem
Owner requested the `關注標的財報` block to be easier to read on mobile:

```text
3481 群創
EPS 2026Q1 0.2
營收 2026/05 +10.3%
```

and remove `關注原因`.

## User Visible Result
- Each stock in `關注標的財報` now renders as stock line plus one line per financial datapoint.
- `關注原因` is removed from the fundamentals block.

## Non Goals
- No data source change.
- No revenue/EPS calculation change.
- No live Telegram delivery.
- No DB write/schema change.

## Impacted Modules And Consumers
- `core/future_watch.py`: future-watch Telegram formatter.
- `tests/test_generator_report.py`: formatter regression expectations.
- Direct consumers: official `generate_report(dry_run=True)` and Telegram future-watch message.

## Output Contract
- Fundamentals block format:
  - `code name`
  - `EPS ...` when available
  - `營收 ...` when available
- Do not append `關注原因：...` in the fundamentals block.

## Acceptance
- Future-watch revenue/fundamentals tests pass.
- Full generator report tests pass.
- Official dry-run shows the requested block format.

## Failure Specimen And Route
- Owner specimen: pasted `關注標的財報` one-line rows.
- Failure layer: `format_future_watch_message()`.
- Replay route: generator report tests plus official dry-run future-watch block.

## Forbidden / Blocking
- Do not fabricate EPS/revenue.
- Do not remove `關注原因` from the separate MOPS events block unless separately requested.
