# QA_REPORT: report_revenue_noise_fsm_20260610

## Scope
- Future-watch target fundamentals freshness.
- Closing/after-hours unheld card noise.
- v21 unheld trade state-machine visible line.
- Official dry-run message-list behavior.

## Risk Scan
- Bulk TWSE/TPEX OpenAPI monthly revenue can lag behind MOPS company monthly revenue.
- A fallback could silently fabricate data or overwrite good values with failed requests.
- Report-phase drift could make `收盤` cards still render intraday history noise.
- FSM lines could still be redundant if they display the same full trigger as the next action.

## Semantic Consistency
- May revenue is only used when an official MOPS row for the target is parsed.
- Targets that MOPS cannot refresh keep the existing official value, so the report remains conservative.
- `收盤` and `盤後` are both treated as mobile after-hours reading contexts.
- Unheld FSM line now separates state/action from missing confirmation event.

## Failure Specimen Countercheck
- Owner specimen showed `營收 2026/04` while May revenue existed for several targets.
- Official dry-run now shows 2026/05 revenue for available MOPS rows.
- Owner specimen showed `歷史：前次 observe｜連續觀察 1 天` in each unheld card.
- Official dry-run now reports `has_unheld_history_noise=False`.

## Additional Challenge
- Ran the full generator report suite plus state-machine suite rather than only the new tests.
- Ran official `generate_report(dry_run=True)` and inspected the actual message list.
- Directly probed MOPS monthly revenue fetch for `3481`, `3231`, and `2337`; all can parse May rows when MOPS responds quickly.
- Timed official dry-run completed in about 55-59 seconds after the latency cap.

## Not Tested
- Live Telegram delivery was not run.
- Render/GitHub live dispatch was not run.
- Production DB writes were not run or changed.

## QA Conclusion
通過
