# CHANGELOG: actionable_report_contract_v21_1_20260623

## Changes

- Updated `core/generator.py`
  - Holding next-step lines now use warning / stop prices for reduce, watch, washout, and new-position risk states.
  - Summary funnel label now renders `準備觀察（待確認）` instead of contradictory `可準備（不可買）`.

- Updated `presentation/report.py`
  - Added failed-breakout reclaim gap text using `retest_zone_low`, `retest_zone_high`, and current price.
  - Changed sharp overheat pullback contract from generic support / chase wording to `先不接刀` and `止跌守支撐 + 量能不失控`.
  - Let holding contract render the computed risk-price next step instead of generic `守警戒價`.
  - Collapsed unheld card repeated lines into one state line and one phase-aware trigger line.
  - Compacted low-repair cards to a support / MA / volume snapshot plus one trigger.
  - Changed user-visible prepare title to `準備觀察`.

- Updated `tests/test_generator_report.py`
  - Added regression for holding risk-price next-step wording.
  - Updated holding card expectations from generic warning text to concrete warning / stop prices.
  - Updated sharp overheat pullback expectations.
  - Added failed-breakout reclaim-zone assertions.
  - Updated prepare / low-repair / overheat expectations to the single-trigger mobile contract.

## Contract Impact

- User-visible Telegram wording changes for holding summary, failed breakout, low repair, overheat, and prepare labels.
- No payload shape change.
- No DB schema or write contract change.
- Version remains `v21.1`.

## Verification

- Focused holding / overheat / low-repair / failed-breakout tests: `5 passed, 220 deselected`.
- Related readability subset: `27 passed, 198 deselected`.
- Official dry-run:
  - `messages=4`.
  - `NO_WAIT_EFFECTIVE_DUP=True`.
  - `LOW_REPAIR_ONE_TRIGGER=True`.
  - `FAILED_BREAKOUT_COMPACT=True`.
  - `SUMMARY_RISK_PRICE=True`.

## Not Changed

- No production DB write.
- No live Telegram.
- No schema, RLS, grant, policy, role, index, or constraint change.

## Residual Risk

- Full legacy report test file remains not green and needs a dedicated test-contract cleanup task.
- `.pytest_cache` emits a local Windows permission warning; it does not affect focused test results.
