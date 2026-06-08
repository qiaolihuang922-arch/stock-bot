# CHANGELOG: unheld_transition_table_replay_20260608

## Changes
- `core/trade_state_machine.py`
  - Added `UNHELD_TRANSITION_TABLE`.
  - Added target-state, guard-to-event, and transition-application helpers.
  - Routed unheld states through events instead of direct label mapping.
  - Added artifact fields: `transition_from`, `transition_to`, `allowed_transition`, `transition_table`, and `target_state`.
- `presentation/report.py`
  - Suppressed internal decision-source warning text on wait-state unheld cards.
  - Preserved visible source block reasons for true source-blocked buy candidates and preserved buy-card evidence lines.
- `tests/test_trade_state_machine.py`
  - Added transition-table replay tests for wait-volume -> ready -> buyable.
  - Added fallback guard routing test when labels are missing.
  - Updated source-error expectation to `WAIT_DATA`.
- `tests/test_generator_report.py`
  - Updated two source-error report expectations from broad `不可行動` to `等資料`.

## Contract Impact
- Unheld FSM is now transition-table driven for pre-order decision states.
- `BUYABLE` is the only actionable unheld state.
- Source-error ready/buyable candidates fail closed to `WAIT_DATA`.
- Waiting report cards are cleaner and no longer show contradictory internal source warning text.
- No live delivery path changed.
- No DB write/schema path changed.

## Verification
- Command:
  ```powershell
  $env:PYTHONIOENCODING='utf-8'
  .\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py tests/test_trade_state_machine.py -q --tb=short
  ```
- Result: `196 passed, 145 warnings, 44 subtests passed`.
- Command:
  ```powershell
  $env:PYTHONIOENCODING='utf-8'
  .\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages, _ = generate_report(dry_run=True); print('\\n--- MESSAGE ---\\n'.join(messages))"
  ```
- Result: v21.0 dry-run messages generated locally; no live Telegram delivery.
- Local transition replay result:
  - `volume_missing_label`: `UNKNOWN -> WAIT_VOLUME`, event `VOLUME_GATE_FAILED`, non-actionable.
  - `volume_to_ready`: `WAIT_VOLUME -> READY`, event `SETUP_READY`, non-actionable.
  - `ready_to_buyable`: `READY -> BUYABLE`, event `BUY_SIGNAL_CONFIRMED`, actionable.
  - `ready_source_error`: `READY -> WAIT_DATA`, event `DATA_GATE_FAILED`, non-actionable.
  - `rr_repair_needed`: `WATCH -> WAIT_RR`, event `RR_GATE_FAILED`, non-actionable.
  - `pullback_needed`: `WATCH -> WAIT_PULLBACK`, event `PULLBACK_GATE_FAILED`, non-actionable.

## Coverage Layers
- Helper: `evaluate_unheld_state` transition-table events and fail-closed source gate.
- Artifact: FSM fields include transition table and allowed transition metadata.
- Formatter: unheld wait-state source-warning conflict removed.
- Official generator: regression and dry-run report generated.
- Runner/live Telegram: intentionally not executed.

## Residual Risk
- This remains a pre-order unheld FSM. Broker/order lifecycle states such as submitted/accepted/filled/canceled are out of scope.
- State persistence remains read-only; no DB state snapshot write was added.
