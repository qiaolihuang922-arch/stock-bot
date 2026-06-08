# QA_REPORT: unheld_transition_table_replay_20260608

## Scope
- Unheld transition-table FSM.
- Guard-to-event routing for data, volume, RR, and pullback repair.
- User-visible unheld report wording after source-warning suppression.
- Official generator regression and dry-run message path.

## Risk Scan
- BUYABLE must be the only actionable unheld state.
- READY must not imply an order.
- Source-error must stop ready/buyable candidates before order lifecycle.
- Wait cards must not mix `等量能` with `資料來源缺失，停止新倉`.
- Real source-blocked buy candidates must still show source-blocked text.

## Semantic Consistency
- `WAIT_VOLUME` is `phase=ENTRY_GATE`, `action=WAIT`, `is_actionable=false`, `next_required_event=VOLUME_CONFIRMED`.
- `READY` is `phase=ARMED`, `is_actionable=false`, `next_required_event=OPEN_CONFIRMATION`.
- `BUYABLE` is `phase=ACTIONABLE`, `is_actionable=true`, `next_required_event=SUBMIT_ORDER`.
- Source-error from `READY/BUYABLE` routes to `WAIT_DATA`, not order lifecycle.
- Official dry-run unheld section shows only tracking states: `等量能` or `等回測`; no valid new entry.

## Failure Specimen Countercheck
- Owner concern: the prior system could not explain when an unheld stock can become buyable.
- Countercheck: local replay proves explicit progression `WAIT_VOLUME -> READY -> BUYABLE`, and separate repair paths for RR/pullback/source error.

## Additional Challenge
- QA checked the phone-facing dry-run text after regression passed.
- Found and fixed a conflict where wait-state cards inherited `決策依據：資料來源缺失，停止新倉`.
- Re-ran full regression after the fix.

## Not Tested
- Live Telegram delivery was not run.
- Production DB write/state snapshot was not run.
- Broker/order lifecycle was not implemented or tested.

## QA Conclusion
通過
