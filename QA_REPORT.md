# QA_REPORT: unheld_trade_fsm_contract_20260608

## Scope
- Unheld pre-order FSM metadata.
- Source gate fail-closed behavior for buyable candidates.
- State artifact schema for dry-run/log inspection.
- Official report regression stability.

## Risk Scan
- BUYABLE must be the only actionable unheld state.
- WAIT states must not imply an order has been submitted.
- Source error must stop a buyable candidate before order lifecycle.
- Existing report wording must not regress.

## Semantic Consistency
- `WAIT_VOLUME` is `phase=ENTRY_GATE`, `action=WAIT`, `is_actionable=false`, `next_required_event=VOLUME_CONFIRMED`.
- A buyable candidate with `source-error` becomes `BLOCKED`, `transition_event=DATA_GATE_FAILED`, and `requires_order_lifecycle=false`.
- Official dry-run still shows wait-volume/wait-pullback report states and no live delivery.

## Failure Specimen Countercheck
- Owner asked whether our FSM matches a real trading FSM. This patch makes the unheld side explicit as a pre-order decision FSM, not an order lifecycle FSM.
- Probe result included `state=WAIT_VOLUME`, `phase=ENTRY_GATE`, `transition_event=VOLUME_GATE_FAILED`, `guards=[DATA_MISSING,VOLUME_WEAK,...]`.

## Not Tested
- Live Telegram delivery was not run.
- Production DB write/state snapshot was not run.
- Broker/order lifecycle was not implemented or tested.

## QA Conclusion
pass
