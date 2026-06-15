# CHANGELOG: unheld_card_mobile_denoise_20260616

## Changes

- Added presentation helpers in `presentation/report.py`:
  - `_combined_status_line`
  - `_combined_buy_check_line`
- Unheld cards now render:
  - `狀態：...`
  - `進場檢查：...`
- Removed separate display rows for unheld-card `拆解`, `買點`, `不能買`, and `還差` when they are part of the same entry-check block.
- Updated `tests/test_generator_report.py` to verify the new compact layout and prevent the old split rows from returning.

## Contract Impact

- Telegram unheld-card message layout changes.
- Strategy calculation, trade state machine, blockers, RR, volume, retest, and unlock logic are unchanged.
- Runtime report version remains `v21.1`.
- No DB write/schema/backfill.
- No live Telegram delivery.

## Direct Consumer Sync

- Owner mobile reading:
  - state is read from `狀態`;
  - entry decision is read from `進場檢查`.
- Existing keyword-based tests still see the core phrases inside the combined line.

## Verification

- Local dry-run:
  - `generate_report(dry_run=True)`
  - confirmed unheld cards render `狀態` and `進場檢查`.
- Test command:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py tests\test_unheld_gap_format.py -q --tb=short`
  - result: `205 passed, 44 subtests passed`

## Covered Layers

- Presentation helper.
- Official Telegram generator formatting.
- User-visible replay via dry-run.

## Residual Risk

- Some old `原因` lines for rejected cards can still be verbose; this task intentionally focused on the duplicated state/entry-check block.
- Holding cards keep the previous layout.
