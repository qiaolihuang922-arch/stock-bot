# CHANGELOG: low_repair_ready_state_v21_1_20260622

## Changes

- Updated `core/generator.py`
  - Added `daily_price_low_repair_status`.
  - Low-repair readiness now uses persistent DB-backed daily price context plus current report price.
  - Checks support, 5-day MA, volume ratio, and risk/reward from one shared helper.
  - `等低位修復` promotes to `可準備` when all low-repair conditions are satisfied.
  - `僅追蹤` count no longer includes `隔日確認`.

- Updated `presentation/report.py`
  - Low-repair-ready cards render as `可準備｜低位修復成立`.
  - Low-repair-ready cards use a compact dedicated card body:
    - status
    - support/5-day/volume observation
    - satisfied checklist
    - next-session buy condition
  - Summary first line no longer renders empty parentheses.
  - Low-repair-ready cards suppress duplicate generic source/data lines.

- Updated `tests/test_generator_report.py`
  - Added regression for `3231 緯創` style all-met low-repair conflict.
  - Updated funnel count tests so `隔日確認` is not double-counted as `僅追蹤`.

## Contract Impact

- User-visible Telegram report wording and state classification changed for low-repair-ready candidates.
- Runtime report version remains `v21.1`.
- No DB schema change.
- No DB write/backfill/delete.
- No live Telegram delivery.

## Verification

- Low-repair / summary targeted tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q -k "low_repair or unheld_funnel or next_day_confirmation or cooling_and_next_day or b5_tracking or postmarket_unheld_gate" --tb=short`
  - result: `12 passed`
- Adjacent state/replay tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_unheld_gap_format.py tests\test_trade_state_machine.py tests\test_strategy_buy_path_replay.py tests\test_strategy_rule_outcomes.py -q --tb=short`
  - result: `16 passed`
- Full report tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q --tb=short`
  - result: `215 passed`, `1 failed`
  - remaining failure: `test_v20_4_47_generate_report_appends_live_readonly_future_watch_sources`, global future-watch lines count is `0`; this is outside the low-repair state/display path.
- Official dry-run:
  - `generate_report(dry_run=True)`
  - result: `top_messages=2`, `flat_messages=5`, no live Telegram.

## Official Dry-Run Rechecks

- `3231 緯創` now renders `👀 可準備｜低位修復成立`.
- `3231 緯創` shows all low-repair conditions satisfied and next-session confirmation wording.
- `2324 仁寶` remains `等低位修復` and shows `還差 站回5日均 37.54`.
- Summary now renders `未持倉 9｜可準備 1（不可買）｜隔日確認 1｜僅追蹤 7...`, avoiding double-counting `隔日確認` inside `僅追蹤`.

## Residual Risk

- The live readonly future-watch source test still fails and should be tracked separately.
- `.pytest_cache` remains unwritable on this machine due local `WinError 5`; test execution itself succeeds.
