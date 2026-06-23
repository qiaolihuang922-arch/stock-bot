# CHANGELOG: actionable_report_contract_v21_1_20260623

## Changes

- Updated `core/generator.py`
  - Added `holding_risk_next_step_text`.
  - Holding next-step lines now use warning / stop prices for reduce, watch, washout, and new-position risk states.

- Updated `presentation/report.py`
  - Added failed-breakout reclaim gap text using `retest_zone_low`, `retest_zone_high`, and current price.
  - Changed sharp overheat pullback contract from generic support / chase wording to `先不接刀` and `止跌守支撐 + 量能不失控`.
  - Let holding contract render the computed risk-price next step instead of generic `守警戒價`.

- Updated `tests/test_generator_report.py`
  - Added regression for holding risk-price next-step wording.
  - Updated holding card expectations from generic warning text to concrete warning / stop prices.
  - Updated sharp overheat pullback expectations.
  - Added failed-breakout reclaim-zone assertions.

## Contract Impact

- User-visible Telegram wording changes for holding cards and failed breakout / sharp pullback unheld cards.
- No payload shape change.
- No DB schema or write contract change.
- Version remains `v21.1`.

## Verification

- Focused holding / overheat / failed-breakout tests: `6 passed, 219 deselected`.
- Holding/today-buy subset: `8 passed, 217 deselected`.
- Related report subset: `14 passed, 211 deselected`.
- Official dry-run:
  - `messages=4`.
  - `live_telegram=False`.
  - `POSITION_OK=True`.
  - `UNHELD_OK=True`.
  - `SUMMARY_OK=True`.
- Full `tests/test_generator_report.py`: `206 passed, 22 failed`.
  - Not accepted as full pass.
  - Remaining failures are legacy / broader report expectation debt, including stale v19/v20 wording, source-error wording, future-watch event wording, and old action-line assumptions.

## Not Changed

- No production DB write.
- No live Telegram.
- No schema, RLS, grant, policy, role, index, or constraint change.

## Residual Risk

- Full legacy report test file remains not green and needs a dedicated test-contract cleanup task.
- `.pytest_cache` emits a local Windows permission warning; it does not affect focused test results.
