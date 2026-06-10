# CHANGELOG: setup_aware_volume_fsm_20260610

## Changes
- `core/trade_state_machine.py`
  - Added `WAIT_SETUP` / `等型態` and mapped `等市場` to `WAIT_MARKET`.
  - Added setup classification: trend continuation, pullback reclaim, breakout confirm, pre-breakout, base reversal, and no setup.
  - Changed unheld guard priority so market gate and setup gate are separate, and volume only outranks RR when volume is the primary gate.
- `core/generator.py`
  - Added setup-aware volume gate logic.
  - Added `等市場` and `等型態` to unheld states, funnel groups, tracking totals, trigger copy, execution copy, and summary buckets.
  - Kept near-breakout low-volume names as `等量能`; far weak-market names now show `等市場`.
- `presentation/report.py`
  - Added `等市場` / `等型態` as visible non-actionable unheld title states.
- `services/volume_calibration.py`
  - Added a read-only volume calibration artifact over `daily_signal_snapshot + daily_price`.
  - Buckets volume by setup context and volume ratio without DB writes or schema changes.
- `tests/test_generator_report.py`, `tests/test_trade_state_machine.py`, `tests/test_volume_calibration.py`
  - Added and updated regression coverage for state/funnel consistency, report-card visibility, and calibration artifact semantics.

## Contract Impact
- Unheld report state is now gate-specific:
  - market weak -> `等市場`
  - no setup -> `等型態`
  - near-breakout low volume -> `等量能`
  - RR below threshold -> `等RR修復`
  - overheat -> `等冷卻`
- Distance from breakout is context-sensitive and no longer a universal blocker.
- No DB schema, DB write path, live Telegram delivery, or holding stop-loss logic changed.

## Verification
- Command:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py tests/test_trade_state_machine.py tests/test_analysis_engine.py tests/test_strategy_evidence.py tests/test_volume_calibration.py -q --tb=short
  ```
- Result: `258 passed, 145 warnings, 44 subtests passed`.
- Official dry-run:
  ```powershell
  $env:PYTHONIOENCODING='utf-8'
  .\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages,_=generate_report(dry_run=True); print('messages',len(messages)); print('\n--- MESSAGE ---\n'.join(messages))"
  ```
- Result: `messages 4`; no live Telegram delivery. Unheld summary: `未持倉 7｜僅追蹤 7（等市場）`.
- Read-only DB calibration:
  - source: `daily_signal_snapshot+daily_price`
  - `db_write=false`
  - `schema_change=false`
  - `source_status=available`
  - contexts include `near_breakout`, `pullback`, `far_weak_market`, `far_no_breakout_setup`.

## Coverage Layers
- Helper/FSM: unheld transition state and guard priority.
- Formatter: unheld card title, state line, trigger text, funnel summary.
- Official generator: `generate_report(dry_run=True)`.
- Production source read-only artifact: Supabase calibration query.

## Residual Risk
- Volume calibration is artifact/read-only; it is not yet wired as an automatic adaptive threshold in live decision logic.
- MOPS/TWSE external sources can still time out; those paths remain fail-closed.
