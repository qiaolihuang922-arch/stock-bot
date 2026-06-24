# CHANGELOG: report_actionability_readability_v21_1_20260624

## Changes

- Updated `presentation/report.py`
  - Renamed low-repair near-ready title from `貼近可買` to `貼近條件｜等站回5日均`.
  - Changed low-repair trigger text to list only missing gates.
  - Added volume quality wording: `不足`, `剛好`, `有效`, `攻擊量`.
  - Translated / suppressed engineering history terms such as `前次 eliminated`.
  - Changed already-broken but near-reclaim breakout distance label to `站回觀察`.
  - Removed zero-count summary noise such as `執行動作 0` and `今日新建倉 0`.
  - Changed already-breakout low-RR title to `追價不划算` where applicable.

- Updated `core/generator.py`
  - Expanded failed-breakout reclaim watch distance from 5% to 7% when a real reclaim zone exists.
  - Stopped summary backtest lines from showing for non-actionable `可準備` / prepare-only cards.

- Updated `tests/test_generator_report.py`
  - Updated low-repair regressions for missing-only triggers and volume quality labels.
  - Added failed-breakout reclaim buffer regression.
  - Added history-line translation regression.

## Contract Impact

- User-visible Telegram wording changes only.
- No DB schema, DB write, backfill, prune, dedupe, or live Telegram delivery.
- Version remains `v21.1`.
- `貼近條件` and `準備觀察` remain non-actionable; only `可買` is actionable.

## Verification

- Focused current-contract tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -k "low_repair_near_ma5 or low_repair_compact_lines or failed_breakout_card or failed_breakout_within_reclaim_buffer or rejected_card_suppresses_positive_repair_history"`
  - Result: `5 passed, 222 deselected`.
- Broader related subset:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -k "low_repair or failed_breakout or rejected_card_suppresses_positive_repair_history or holding_next_step or compact_market"`
  - Result: `10 passed, 217 deselected`.
- Official dry-run via `generate_report(dry_run=True)`:
  - `messages=4`.
  - `HAS_NEAR_BUY=False`.
  - `HAS_NEAR_CONDITION=True`.
  - `HAS_WAIT_RECLAIM=True`.
  - `HAS_ELIMINATED=False`.
  - `INTRADAY_TOMORROW_LABEL=False`.
  - `HAS_BACKTEST_STANDALONE=False`.
  - `HAS_ZERO_ACTION=False`.

## Coverage Layer

- Helper / formatter: covered.
- Official generator message list: covered by dry-run artifact.
- Production source / live Telegram: not run by design.

## Not Changed

- No production DB writes or reads beyond normal dry-run reads.
- No schema, RLS, grant, policy, role, index, or constraint change.
- No live Telegram delivery.

## Residual Risk

- Full `tests/test_generator_report.py` still contains older legacy wording expectations and remains a separate cleanup task.
- `.pytest_cache` may still emit a local Windows permission warning; it did not block focused tests.
