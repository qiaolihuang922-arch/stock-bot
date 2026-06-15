# CHANGELOG: entry_quality_d_semantics_v21_1_20260615

## Changes

- Updated `presentation/report.py`:
  - Added strategy-aware quality gap wording.
  - Rebound / retest cards now show `買點品質：回測 / 轉強後重評`.
  - True setup-quality gaps now show `買點品質未過（目前 D，需 B 以上）`.
  - Unlock criteria now render `買點品質 B 以上`.
- Updated `core/generator.py`:
  - `隔日確認` for recognized price behaviors (`LIMIT_LOCK`, `LIMIT_REBOUND`, `WEAK_REBOUND`) is no longer overwritten to `等型態` solely because `entry_quality` is below B.
- Updated `core/signal_snapshot.py`:
  - Per-stock `market_grade == D` reason now renders as `個股弱勢` instead of `市場弱`.
- Updated tests:
  - `tests/test_unheld_gap_format.py`
  - `tests/test_generator_report.py`

## Contract Impact

- Telegram wording and unheld funnel routing changed for readability / semantics.
- No payload shape change.
- No DB schema or persistence change.
- No live Telegram delivery.
- No strategy threshold change.
- Version remains `v21.1`.

## Direct Consumer Sync

- `core.generator.generate_report(dry_run=True)` now prints:
  - rebound card: `買點品質：回測 / 轉強後重評`
  - setup card: `買點品質未過（目前 D，需 B 以上）`
  - unlock: `買點品質 B 以上`
- `core.signal_snapshot.analyze_ohlcv_snapshot` keeps internal `market_grade` / `entry_quality`, but reason labels no longer call per-stock D "market weak".

## Verification

- Related regression:
  ```powershell
  $env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -m pytest tests\test_unheld_gap_format.py tests\test_generator_report.py tests\test_analysis_engine.py tests\test_condition_engine.py tests\test_trade_state_machine.py -q --tb=short
  ```
  Result: `257 passed, 149 warnings, 44 subtests passed`.
- Official dry-run:
  ```powershell
  $env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages,_=generate_report(dry_run=True); print('\n\n--- MESSAGE ---\n\n'.join(messages))"
  ```
  Result: unheld cards distinguish setup-quality D from rebound/retest re-evaluation; no live Telegram delivery.
- Snapshot probe:
  - `LIMIT_LOCK`: `market_grade=A+`, `entry_quality=D`, reason `漲停鎖價 / 不追高`.
  - multi-day rise sample: `market_grade=A+`, `entry_quality=C`, blocked by low RR / observation.
  - weak rebound sample: `market_grade=D`, `entry_quality=D`, reason `弱勢反彈 / 隔日確認`.
  - limit rebound after decline: `market_grade=D`, `entry_quality=D`, reason `漲停反彈 / 隔日確認`.

## Covered Layers

- Formatter helper: covered by `tests/test_unheld_gap_format.py`.
- Official generator / message list: covered by `tests/test_generator_report.py` and dry-run.
- Snapshot / analysis semantics: covered by `tests/test_analysis_engine.py` and targeted probe.
- Condition/state-machine compatibility: covered by `tests/test_condition_engine.py` and `tests/test_trade_state_machine.py`.
- Runner/live Telegram: not executed by design.
- Production DB: not touched.

## Residual Risk

- `entry_quality` remains an internal entry setup grade. It is intentionally not a general stock grade.
- Further calibration of quality thresholds should be a separate strategy task, not a display patch.
