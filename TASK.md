# TASK: latest_revenue_month_fallback_20260610

## Status
- task_id: `latest_revenue_month_fallback_20260610`
- type: `normal_patch`
- status: `complete`
- version: `v21.0`
- QA level: `L2`

## Owner Problem
Owner pointed out that revenue should always fetch the latest available month; the code must not need a patch every month.

## User Visible Result
- The future-watch fundamentals block now searches for the latest available MOPS monthly revenue by trying the theoretical latest month first, then falling back to earlier months.
- Example: on 2026-07-10 it tries ROC `11506`; if that month is not published for a stock, it automatically falls back to `11505`, then older candidates.

## Non Goals
- No live Telegram delivery.
- No DB schema/RLS/grant/policy/index change.
- No holding decision or trade state transition change.

## Impacted Modules And Consumers
- `core/future_watch.py`: MOPS monthly revenue candidate-month search and normalized revenue row merge.
- `tests/test_generator_report.py`: latest-available-month fallback regression.
- Direct consumers: official `generate_report(dry_run=True)`, Telegram future-watch message, GitHub/Render runner artifact.

## Output Contract
- Latest revenue search starts from the previous calendar month in ROC format.
- If that month is unavailable, search earlier month candidates without code changes.
- Use the first official row returned by MOPS.
- Accept normalized internal keys (`stock_code`, `revenue_month`, `revenue_yoy`) so tests and adapters do not depend on mojibake-prone Chinese column names.
- Do not fabricate revenue when all candidate months fail.

## Acceptance
- Targeted latest-month fallback tests pass.
- Generator/state-machine regression tests pass.
- Official `generate_report(dry_run=True)` returns message list without live Telegram delivery.

## Failure Specimen And Route
- Owner specimen: concern that each new month would require another code change.
- Failure layer: future-watch fundamentals collector / MOPS revenue fallback.
- Replay route: unit test simulates July run where June is missing and May is the latest official row.

## Forbidden / Blocking
- No live Telegram delivery.
- Do not hard-code a specific calendar month.
- If git completion gate fails, do not claim complete.
