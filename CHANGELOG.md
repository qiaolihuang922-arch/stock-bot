# CHANGELOG: unheld_trade_fsm_contract_20260608

## Changes
- `core/trade_state_machine.py`
  - Added formal unheld state metadata for phase, actionability, terminal flag, and next required event.
  - Added unheld guard extraction for data, market, volume, RR, heat, structure, distance, and entry-quality gates.
  - Added transition events such as `VOLUME_GATE_FAILED`, `RR_GATE_FAILED`, `DATA_GATE_FAILED`, and `BUY_SIGNAL_CONFIRMED`.
  - Extended state artifacts with `phase`, `is_actionable`, `is_terminal`, `transition_event`, `next_required_event`, `guards`, `blocked_by`, and `requires_order_lifecycle`.
- `tests/test_trade_state_machine.py`
  - Added assertions for wait-volume FSM metadata.
  - Added fail-closed source-error test for a buyable unheld candidate before order lifecycle.

## Contract Impact
- Existing visible report text remains stable.
- Unheld FSM is now inspectable as a formal pre-order decision FSM.
- No live delivery path changed.
- No DB write/schema path changed.

## Verification
- Command:
  ```powershell
  $env:PYTHONIOENCODING='utf-8'
  .\.venv\Scripts\python.exe -m pytest tests/test_trade_state_machine.py -q --tb=short
  ```
- Result: `5 passed, 3 warnings`.
- Command:
  ```powershell
  $env:PYTHONIOENCODING='utf-8'
  .\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py tests/test_trade_state_machine.py -q --tb=short
  ```
- Result: `194 passed, 145 warnings, 44 subtests passed`.
- Command:
  ```powershell
  $env:PYTHONIOENCODING='utf-8'
  .\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages, _ = generate_report(dry_run=True); print('\\n\\n--- MESSAGE ---\\n\\n'.join(messages))"
  ```
- Result: v21.0 dry-run messages generated locally; no live Telegram delivery.

## Coverage Layers
- Helper: `evaluate_unheld_state` metadata and fail-closed source gate.
- Artifact: `build_state_artifact` includes formal FSM fields.
- Formatter/official generator: full regression plus dry-run report.
- Runner/live Telegram: intentionally not executed.

## Residual Risk
- This is still a pre-order unheld FSM. Real order states such as submitted/accepted/filled/canceled are explicitly out of scope.
- State persistence is still read-only and not written to DB.
