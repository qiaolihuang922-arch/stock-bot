# CHANGELOG: strategy_axis_split_v21_1_20260615

## Changes

- Updated `services/analysis.py`:
  - Added derived fields:
    - `stock_strength_state`
    - `entry_setup_state`
    - `actionability_state`
  - These separate stock strength, setup readiness, and executable action.
  - Confirmed breakout can become `READY` / `BUYABLE`.
  - Limit-up, rebound, weak rebound, cooldown, RR, volume, and setup waits are distinct states.
- Updated `core/generator.py`:
  - Added `strategy_axis_line(...)`.
  - Added fallback derivation for older/replayed payloads.
  - Explicit behavior evidence (`LIMIT_LOCK`, `LIMIT_REBOUND`, `WEAK_REBOUND`) overrides stale derived labels.
  - Kept prior semantic cleanup: per-stock D is `個股弱勢`, and rebound/limit labels are not flattened to generic `不交易`.
- Updated `presentation/report.py`:
  - Unheld cards now render `拆解：強弱 ...｜買點 ...｜行動 ...` after the trade-state line.
- Updated tests:
  - `tests/test_analysis_engine.py`
  - `tests/test_generator_report.py`

## Contract Impact

- Telegram unheld card layout gains one new split line.
- Raw result gains derived fields for internal/report consumption.
- No DB schema change.
- No production DB write/backfill.
- No live Telegram delivery.
- No strategy threshold change.
- Version remains `v21.1`.

## Direct Consumer Sync

- Official dry-run now shows examples like:
  - `拆解：強弱 強勢鎖價｜買點 等回測確認｜行動 等待`
  - `拆解：強弱 急彈修復｜買點 等回測確認｜行動 等待`
  - `拆解：強弱 轉強中｜買點 等風險報酬｜行動 等待`
- Snapshot/raw-result consumers can inspect the three separate fields instead of inferring from one grade.

## Verification

- Related regression:
  ```powershell
  $env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -m pytest tests\test_analysis_engine.py tests\test_generator_report.py tests\test_unheld_gap_format.py tests\test_condition_engine.py tests\test_trade_state_machine.py -q --tb=short
  ```
  Result: `258 passed, 149 warnings, 44 subtests passed`.
- Official dry-run:
  ```powershell
  $env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages,_=generate_report(dry_run=True); print(messages[1])"
  ```
  Result: unheld cards show split strategy axes; no live Telegram delivery.

## Covered Layers

- Analysis/snapshot derived states: covered by `tests/test_analysis_engine.py`.
- Official generator/message list: covered by `tests/test_generator_report.py` and dry-run.
- Formatter helper compatibility: covered by `tests/test_unheld_gap_format.py`.
- Condition/state-machine compatibility: covered by `tests/test_condition_engine.py` and `tests/test_trade_state_machine.py`.
- Runner/live Telegram: not executed by design.
- Production DB: not touched.

## Residual Risk

- The split clarifies why a stock is not actionable; it does not recalibrate thresholds.
- Future calibration should use persisted outcomes and may require a separate DB-backed strategy task.
