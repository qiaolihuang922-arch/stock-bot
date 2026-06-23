# CHANGELOG: intraday_display_state_sync_v21_1_20260623

## Changes

- Updated `core/generator.py`
  - Treat 13:00-13:19 on weekdays as `盤中` instead of falling to `非交易`.
  - Added `unheld_display_funnel_state` so summary uses the same user-visible state as cards for overheat pullbacks.
  - Prevented `觀察` from becoming the visible rejection reason; falls back to `型態未過`.

- Updated `presentation/report.py`
  - Low-repair missing MA/support conditions now include numeric gap from current price.
  - Breakout failure market line converts positive volume terms to `放量回落` / `待確認`.
  - Overheat pullback trigger now uses concrete retest conditions instead of generic cooling text.

- Updated `tests/test_generator_report.py`
  - Added regressions for display-bucket sync, pullback triggers, rejection placeholder, failed-breakout volume wording, and 13:00 market phase.
  - Updated expected low-repair wording to include numeric gap.
  - Updated summary expectations for overheat pullback display buckets.

## Contract Impact

- User-visible Telegram wording changes for unheld cards and summary counts.
- No payload shape change.
- No DB schema or write contract change.
- Version remains `v21.1`.

## Verification

- Focused tests: `7 passed, 217 deselected`.
- Related report subset: `26 passed, 198 deselected`.
- Official dry-run: `messages=4`, no live Telegram delivery.
- Full report test file: `215 passed, 12 failed`.
  - failures are legacy / broader expectations outside this focused fix: stale v19/v20 wording, source-error wording, old limit-card wording, future-watch live-source count, and one old attack-volume expectation.

## Not Changed

- No production DB write.
- No live Telegram.
- No schema, RLS, grant, policy, role, index, or constraint change.

## Residual Risk

- Full legacy test file remains not green and should be handled by a separate test-contract cleanup task.
- `.pytest_cache` emits a local Windows permission warning; it does not affect focused test results.
