# TASK: revenue_fallback_no_downgrade_20260610

## Status
- task_id: `revenue_fallback_no_downgrade_20260610`
- type: `normal_patch`
- status: `complete`
- version: `v21.0`
- QA level: `L2`

## Owner Problem
Owner pasted a report where revenue fallback produced misleading old months and impossible YoY values, for example older 2026/03 or 2026/02 revenue and huge percentages derived from revenue amount.

## User Visible Result
- Revenue fallback no longer downgrades an existing newer month to an older MOPS row.
- Revenue fallback no longer uses monthly revenue amount as YoY percentage.
- The report only accepts current/latest candidate month or one-month fallback; if both fail, it omits revenue instead of showing stale old months.

## Non Goals
- No live Telegram delivery.
- No DB schema/RLS/grant/policy/index change.
- No holding decision or trade state transition change.

## Impacted Modules And Consumers
- `core/future_watch.py`: MOPS monthly revenue fallback guard and YoY extraction.
- `tests/test_generator_report.py`: regressions for no downgrade, no amount-as-YoY, and no too-old fallback.
- Direct consumers: official `generate_report(dry_run=True)`, Telegram future-watch message, GitHub/Render runner artifact.

## Output Contract
- MOPS row can refresh only if `row.revenue_month > existing.revenue_month`.
- If no existing revenue month exists, fallback only checks latest completed month and the prior month.
- Do not display 2026/03 or 2026/02 in a 2026/06 run.
- Do not treat large monthly revenue amount values as revenue YoY.
- If usable official revenue is unavailable, omit revenue for that target.

## Acceptance
- Revenue regression tests pass.
- Generator/state-machine regression tests pass.
- Official `generate_report(dry_run=True)` returns message list without live Telegram delivery.
- Official dry-run has no huge fake YoY values and no too-old revenue months.

## Failure Specimen And Route
- Owner specimen: 2026-06-10 v21.0 future-watch fundamentals block.
- Failure layer: future-watch fundamentals collector / MOPS revenue fallback.
- Replay route: official dry-run and targeted revenue fallback tests.

## Forbidden / Blocking
- No live Telegram delivery.
- Do not fabricate revenue.
- Do not downgrade to older revenue months.
- If git completion gate fails, do not claim complete.
