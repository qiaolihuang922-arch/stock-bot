# CHANGELOG: report_state_sync_v21_1_20260617

## Changes

- Updated `presentation/report.py`
  - Added data-aware retest wording for rebound/retest cards.
  - Retest cards now distinguish:
    - current price above basis: `尚未回測`
    - current price near basis: `回測中，觀察能否守住`
    - current price below basis: `已跌破，等待重新站回或形成新支撐`
  - Added holding warning-breach guard so holding cards cannot say `未跌破風控` when current price is already below warning.
  - Split overheat wording:
    - near/at limit-up: `漲停/過熱，不追價`
    - non-limit overheat: `短線過熱，先等冷卻`
  - Split breakout-distance wording so non-limit overheat does not render `已突破，但漲停/過熱不追`.
  - Added concrete volume-wait gap text: `目前量能 Xx，需至少 0.8x`.
  - Removed after-hours summary filler:
    - empty `今日交易 / 新增交易建議：無`
    - duplicate `明日計畫`
    - duplicate `未持倉僅追蹤，不列入明日計畫`
- Updated `tests/test_generator_report.py`
  - Added/updated regression specimens for the Owner-pasted conflicts.

## Contract Impact

- User-visible Telegram report wording changes only.
- Runtime report version remains `v21.1`.
- No DB schema change.
- No DB write/backfill/delete.
- No live Telegram delivery.
- No change to persisted production data.

## Direct Consumer Sync

- Official consumer covered: `generate_report(dry_run=True)` message list.
- Mobile readability covered by generator report snapshots and absence checks.

## Verification

- Targeted report tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q -k "retest_basis or warning_breached or non_limit_overheat or wait_volume_card or db_backed_rebound_pullback" --tb=short`
  - result: `5 passed`
- Full generator report tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q --tb=short`
  - result: `215 passed`, `46 subtests passed`
- Adjacent state/replay tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_unheld_gap_format.py tests\test_trade_state_machine.py tests\test_strategy_buy_path_replay.py tests\test_strategy_rule_outcomes.py -q --tb=short`
  - result: `16 passed`
- Official generator dry-run:
  - `generate_report(dry_run=True)`
  - result: `4` messages, no live Telegram.

## Official Dry-Run Rechecks

- `2337 旺宏` no longer renders `回測基準 ... 尚未回測` when current price is below the retest basis.
- `2421 建準` renders `已跌破警戒，未到停損` and warning-first handling.
- `2344 華邦電` / `2408 南亞科` non-limit overheat renders `短線過熱，先等冷卻`, not limit-up wording.
- `2303 聯電` wait-volume card renders `目前量能 0.53x，需至少 0.8x`.
- Summary no longer renders empty `新增交易建議：無`, duplicate `明日計畫`, or duplicate unheld non-execution filler.

## Residual Risk

- This cycle corrects report-state/display conflicts; it does not redesign the underlying strategy gates.
- Official dry-run may change state as live/realtime data changes during the day; the added guards are data-aware and should remain valid across those changes.
- `.pytest_cache` still cannot be written on this machine because of local `WinError 5`; tests execute and pass despite the cache warning.
