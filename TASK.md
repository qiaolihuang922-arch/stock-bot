# TASK: unheld_transition_table_replay_20260608

## Status
- task_id: `unheld_transition_table_replay_20260608`
- type: `risk_patch`
- status: `QA passed, pending commit/push`
- version: `v21.0`
- QA level: `L3`

## Owner Problem
Owner said adding fields alone is not useful and asked whether the logic learned from real trading state machines. The unheld side must be more than labels: it needs explicit transition events, allowed next states, and local replay proof before Owner reviews the report.

## User Visible Result
- Unheld cards remain decision-first: wait-volume, wait-pullback, wait-RR, ready, buyable, or wait-data.
- Waiting cards no longer show conflicting internal source-warning text such as `資料來源缺失，停止新倉` when the visible state is only waiting for volume/pullback.
- Buyable remains the only actionable unheld state; ready is armed but not an order.

## Non Goals
- No live Telegram delivery.
- No DB schema/write change.
- No broker/order lifecycle implementation.
- No holding-side FSM rewrite in this round.

## Impacted Modules And Consumers
- `core/trade_state_machine.py`: unheld transition table, guard-to-event routing, artifact fields.
- `presentation/report.py`: suppresses internal decision-source noise on non-actionable waiting cards while preserving visible source block reasons for true source-blocked buy candidates.
- `tests/test_trade_state_machine.py`: transition-table replay and guard fallback coverage.
- `tests/test_generator_report.py`: updated source-error expected state from broad blocked text to wait-data.
- Direct consumers: official generator dry-run report, runner/log/artifact inspection.

## Output Contract
- Unheld transition table must route events such as `VOLUME_GATE_FAILED`, `RR_GATE_FAILED`, `PULLBACK_GATE_FAILED`, `DATA_GATE_FAILED`, `SETUP_READY`, and `BUY_SIGNAL_CONFIRMED`.
- `WAIT_*` states are non-actionable and require a repair event.
- `READY` is armed and non-actionable; it requires open/confirmation.
- `BUYABLE` is actionable and requires `SUBMIT_ORDER`.
- Source errors on ready/buyable candidates fail closed to `WAIT_DATA` before any order lifecycle.
- Artifacts expose `transition_from`, `transition_to`, `allowed_transition`, `transition_table`, and `target_state`.

## Acceptance
- State-machine tests pass.
- Full generator/state-machine regression passes.
- Official dry-run generates v21.0 messages without live Telegram delivery.
- Local replay proves at least these routes: volume wait, volume-to-ready, ready-to-buyable, ready-source-error-to-wait-data, RR repair, pullback repair.
- Dry-run unheld cards do not contain the old conflicting `決策依據：資料來源缺失，停止新倉` line for wait-volume/wait-pullback cards.

## Failure Specimen And Route
- Owner specimen: unheld cards looked like static elimination labels and did not explain how a stock can later become buyable.
- Route: `evaluate_unheld_state` -> transition table replay -> `build_state_artifact` -> official dry-run report text.

## Forbidden / Blocking
- No live Telegram delivery.
- No production DB write or schema change.
- If full generator regression fails, do not claim complete.
