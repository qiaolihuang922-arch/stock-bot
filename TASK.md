# TASK: unheld_trade_fsm_contract_20260608

## Status
- task_id: `unheld_trade_fsm_contract_20260608`
- type: `risk_patch`
- status: `QA passed, pending git completion`
- version: `v21.0`
- QA level: `L3`

## Owner Problem
Owner asked to start with unheld stocks because they are easier to judge and do not require buy-time/order timing. The previous v21 state machine improved visible report states, but the unheld side was still closer to a label mapper than a formal trading FSM.

## User Visible Result
- Official dry-run report remains visually stable.
- Unheld state line still shows readable wait states such as wait-volume and wait-pullback.
- Internally, every unheld state now carries FSM metadata: `phase`, `is_actionable`, `is_terminal`, `transition_event`, `next_required_event`, `guards`, `blocked_by`, and `requires_order_lifecycle=false`.
- Source gaps are represented as guards without turning wait-volume/wait-pullback into order states.

## Non Goals
- No live Telegram delivery.
- No DB schema/write change.
- No holding/order lifecycle implementation in this round.
- No broker/order status states such as submitted/accepted/filled/canceled.

## Impacted Modules And Consumers
- `core/trade_state_machine.py`: formal unheld FSM metadata and artifact fields.
- `tests/test_trade_state_machine.py`: FSM metadata and fail-closed source gate coverage.
- Direct consumers: dry-run/log/artifact inspection and existing official report path.

## Output Contract
- Unheld `BUYABLE` is the only actionable unheld state.
- Wait states are non-actionable and non-terminal.
- Buyable/ready candidates with bad source status fail closed before any order lifecycle is required.
- Unheld FSM artifacts must include `phase`, `transition_event`, `next_required_event`, `guards`, `blocked_by`, and `requires_order_lifecycle`.

## Acceptance
- State-machine unit tests pass.
- Full generator/state-machine regression passes.
- Official dry-run still generates v21.0 messages without live Telegram delivery.
- Local artifact/probe proves unheld wait-volume includes phase/guards/next event.

## Failure Specimen And Route
- Prior issue: unheld v21 was useful in the report but not yet comparable to a formal FSM.
- Route: `evaluate_unheld_state` -> `build_state_artifact` -> official dry-run report remains stable.

## Forbidden / Blocking
- No live Telegram delivery.
- No production DB write or schema change.
- If full generator regression fails, do not claim complete.
