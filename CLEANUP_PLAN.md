# CLEANUP_PLAN.md

## Completed This Cycle

- Confirmed existing DB support for low-repair judgment:
  - `daily_price` contains OHLCV.
  - No schema expansion was required.
- Added DB-backed `等低位修復` route for far-from-breakout pullback/reclaim cases.
- Preserved fail-closed behavior:
  - if DB daily_price is missing / insufficient, low-repair route is not shown.
- Updated Telegram card display:
  - low-repair cards show route, recent support, 5-day MA, volume ratio, and effective buy conditions.
  - `距突破` remains visible.
- No DB write / no schema change / no live Telegram.
- Full pytest passed.

## Replay / Test Evidence

- DB read probe:
  - 2324 / 3231 / 2376 / 2337 / 3481 all had `daily_price` source and 8 OHLCV points.
- Targeted report/state/cross-day tests:
  - `223 passed, 159 warnings, 46 subtests passed`
- Full tests:
  - `491 passed, 8 skipped, 169 warnings, 110 subtests passed`
- Official generator dry-run:
  - `4` messages generated.

## Previous Cycle Summary

- Implemented state-specific Telegram card cleanup:
  - holdings: one `決策` plus one `明日處理`.
  - `等冷卻`: `狀態` plus `等待`.
  - `等回測`: `狀態` plus concrete `回測` anchor plus `有效買點`.
  - `等型態`: `狀態` plus `等待` plus `有效買點`.
  - `等接近`: one breakout zone reference plus concise wait condition.

## Cleanup Notes

- `.pytest_cache` remains inaccessible to pytest cache writes on this machine (`WinError 5`); this is a local cache warning, not product data.
- No obsolete production DB rows were touched.
- No table was deleted.
- No runtime output was added as source-of-truth.

## Follow-ups

- Further calibrate low-repair buyability in a separate replay task:
  - support definition: recent low vs close support vs MA support.
  - volume repair threshold by strategy type.
  - when low-repair can become `可準備` rather than only `等低位修復`.
