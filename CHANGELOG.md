# CHANGELOG: rr_context_standardization_v21_1_20260615

## Changes

- Added auditable RR components in `services/analysis.py`:
  - formula: `(target-entry)/(entry-stop)`;
  - entry, stop, target, reward, risk, risk percentage;
  - target-basis label;
  - RR usability context: `actionable`, `setup_pending`, `theoretical`, `blocked`.
- Extended shared strategy feature persistence in `core/signal_snapshot.py` so daily snapshot, signal items, and backfill paths can carry RR components.
- Added Owner-reviewed SQL artifact `db/sql/v21_2_rr_context_columns.sql`.
  - It only adds typed RR columns to existing `daily_signal_snapshot` and `signal_items`.
  - It does not write data and does not alter RLS, grants, policies, roles, indexes, or constraints.
- Updated `presentation/report.py`:
  - actionable RR remains `RR x達標`;
  - non-actionable high RR becomes `理論RR x（setup未成立）` / `理論RR x僅參考`;
  - RR不足 stays normal RR instead of being mislabeled theoretical.
- Updated regression tests for the new contract and added persistence assertions for RR fields.

## Research Alignment

- Common RR calculation uses entry, stop-loss, and take-profit/target.
- Breakout trading requires support/resistance, volume confirmation, predefined stops, and targets.
- Therefore this patch separates formula correctness from setup usability: a mathematically high RR is not a buy signal until the setup is actionable.

## Contract Impact

- Report wording changes for non-actionable high RR cards.
- Strategy payload shape expands with RR component fields.
- Existing schema fallback remains; runner does not crash if Owner has not applied the new SQL artifact.
- Buy/sell thresholds are not loosened.
- No live Telegram delivery and no production DB schema execution were performed.

## Verification

- Strategy, persistence, backfill, formatter, and generator regression:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_analysis_engine.py tests/test_daily_snapshot_store.py tests/test_backfill_signals.py tests/test_unheld_gap_format.py tests/test_generator_report.py -q --tb=short
  ```
  Result: `263 passed, 147 warnings, 44 subtests passed`.
- Official generator dry-run:
  ```powershell
  $env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -c "from core.generator import generate_report, VERSION; messages, write_results = generate_report(dry_run=True); print('VERSION', VERSION); print('messages', len(messages)); print('write_results', write_results); print('\n--- MESSAGE ---\n'.join(messages))"
  ```
  Result: `VERSION v21.1`, `messages 4`, no live Telegram delivery.
- Dry-run report confirmed:
  - `緯創 / 仁寶 / 技嘉` show `理論RR ...（setup未成立）`;
  - `旺宏` shows `理論RR 2.21僅參考` while waiting for retest;
  - `聯電` RR不足 remains `RR 1.32｜需>=1.5`.

## Residual Risk

- SQL artifact still needs Owner review/execution before production DB typed RR columns exist.
- Existing RR target basis is now explicit and auditable; future calibration can compare target-basis choices against persisted outcomes.
- Live production runner artifact after next scheduled `run_mode=bot` was not observed in this cycle.
