# CHANGELOG: intraday_report_state_readability_v21_1_20260624

## Changes

- Updated `core/generator.py`
  - Added `LOW_REPAIR_MA5_NEAR_TOLERANCE_PCT = 0.8`.
  - Added low-repair `near_ready`, `ma5_gap`, and `ma5_gap_pct` fields.
  - Added `等站回` routing for failed breakouts that have a real reclaim anchor and are within 5% of that zone.
  - Synced `等站回` into funnel groups, ordering, summary tracking counts, and conflict checks.

- Updated `presentation/report.py`
  - Holding handling label is now phase-aware:
    - `盤中處理`
    - `盤前處理`
    - `明日處理`
  - Low-repair near-ready cards show `貼近可買｜低位修復接近成立`.
  - Low-repair near-ready trigger says exactly to reclaim the 5-day MA before a small-position trial.
  - `等站回` cards render compactly and do not show duplicate trade-state / data lines.

- Updated `core/trade_state_machine.py`
  - Added `WAIT_RECLAIM` / `等站回` state metadata.

- Updated `tests/test_generator_report.py`
  - Added regression for low-repair near-ready.
  - Updated failed-breakout near-zone regression to expect `等站回`.
  - Added phase-aware holding label regression.

## Contract Impact

- User-visible Telegram wording changes.
- No payload shape required by external callers changed.
- No DB schema or write contract change.
- Version remains `v21.1`.

## Verification

- `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -k "low_repair_near_ma5 or failed_breakout_card or warning_breached_holding"`
  - `3 passed, 223 deselected`.
- `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -k "low_repair or failed_breakout or warning_breached_holding or holding_next_step or compact"`
  - `11 passed, 215 deselected`.
- Official dry-run via `generate_report(dry_run=True)`
  - `messages=4`.
  - `HAS_NEAR_BUY=True`.
  - `HAS_WAIT_RECLAIM=True`.
  - `INTRADAY_TOMORROW_LABEL=False`.

## Full-Test Note

- Full `tests/test_generator_report.py` was run and still has legacy expectation failures from older v19/v20/v21 specimens.
- The visible failing themes include old expectations for `淘汰`, old `有效買點` lines, and old `明日處理` wording.
- Those are outside this patch's acceptance route and are listed as cleanup debt; focused current-contract tests and official dry-run pass.

## Not Changed

- No production DB write.
- No live Telegram.
- No schema, RLS, grant, policy, role, index, or constraint change.

## Residual Risk

- Full legacy report test cleanup remains needed.
- `.pytest_cache` emits a local Windows permission warning; focused tests pass despite it.
