# CHANGELOG: trade_state_machine_v21_completion_20260608

## Changes
- `core/generator.py`
  - Strengthened today-buy holding wording so manual/ledger or already-executed buys are not read as current buy signals.
  - Treated helper-only contexts without a full `results_map` as source-available to avoid false source-missing failures in local formatter tests.
  - Fixed evidence maturity so production-readonly missing/conflict ledger evidence can pass the maturity dimension only when the rendered report is fail-closed.
- `presentation/report.py`
  - Fixed unheld blocker priority. Volume/market/RR/pullback blockers now beat source/sample gates when they are the visible reason.
  - Kept source/sample gates as the main blocker only when there is no clearer blocker.
  - Prevented evidence-adjusted titles from being overwritten by generic eliminate reasons.
- `tests/test_generator_report.py`
  - Reconciled v21 visible-state output with the full generator regression suite.
  - Updated old exact-message expectations that protected zero-count funnel noise.

## Contract Impact
- Visible version remains `v21.0`.
- Message list shape is unchanged.
- No live delivery path changed.
- No DB write/schema path changed.
- Unheld summary remains denoised and no longer shows empty count buckets.

## Verification
- Command:
  ```powershell
  $env:PYTHONIOENCODING='utf-8'
  .\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py tests/test_trade_state_machine.py -q --tb=short
  ```
- Result: `193 passed, 145 warnings, 44 subtests passed`.
- Command:
  ```powershell
  $env:PYTHONIOENCODING='utf-8'
  .\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages, _ = generate_report(dry_run=True); print('\\n\\n--- MESSAGE ---\\n\\n'.join(messages))"
  ```
- Result: v21.0 dry-run messages generated locally; no live Telegram delivery.

## Coverage Layers
- Helper: covered through generator/state-machine tests.
- Formatter: covered through visible report assertions.
- Official generator: covered by dry-run message list.
- Runner/live Telegram: intentionally not executed.
- Production source: read-only through the existing generator path only.

## Residual Risk
- v21 state machine remains read-only. Persisted state snapshots require a separate decision and likely a separate DB/write-path task.
- Local `.pytest_cache` has a permission warning, but tests completed successfully.
