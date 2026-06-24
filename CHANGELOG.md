# CHANGELOG: compact_actionable_buy_card_v21_1_20260624

## Changes

- Updated `presentation/report.py`
  - Added `_low_repair_actionable_lines`.
  - Low-repair actionable cards now use a compact small-position instruction, the existing low-repair support / MA / volume snapshot, and one trigger line.
  - Suppressed duplicate trade-state, buy-point, reason, and risk/reward data lines for low-repair actionable buy cards.

- Updated `core/generator.py`
  - `format_backtest_groups` no longer emits summary backtest lines with `無明顯優勢`.
  - Directional or risk-relevant backtest lines such as `略優` / `偏弱` can still surface.

- Updated `tests/test_generator_report.py`
  - The low-repair actionable regression now asserts the compact buy-card contract.
  - The test guards against old noisy lines returning.

## Contract Impact

- User-visible Telegram wording changes for low-repair actionable buy cards.
- Summary backtest display is less noisy when the backtest has no clear edge.
- No payload shape change.
- No DB schema or write contract change.
- Version remains `v21.1`.

## Verification

- `.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py -k "low_repair"`
  - `5 passed, 220 deselected`.
- `.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py -k "low_repair or backtest_groups or direct_actions or prepare"`
  - `21 passed, 204 deselected`.
- `.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py -k "overheat or low_repair or failed_breakout or holding_next_step or risk_precedes or direct_actions or prepare"`
  - `27 passed, 198 deselected`.
- Official dry-run via `generate_report(dry_run=True)`
  - `messages=4`.
  - `LOW_BUY_OLD_NOISE_ABSENT=True`.
  - `LOW_BUY_COMPACT_PRESENT=True`.
  - `NO_NO_EDGE_BACKTEST_SUMMARY=True`.

## Not Changed

- No production DB write.
- No live Telegram.
- No schema, RLS, grant, policy, role, index, or constraint change.

## Residual Risk

- Full legacy report test cleanup remains a separate task.
- `.pytest_cache` emits a local Windows permission warning; focused tests pass despite it.
