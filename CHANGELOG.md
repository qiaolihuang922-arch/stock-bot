# CHANGELOG: unheld_card_mobile_denoise_20260616

## Changes

- Replaced the prior hard-concat mobile layout with `_entry_check_lines` in `presentation/report.py`.
- Unheld waiting / rejected cards now render short decision rows:
  - `進場：...｜原因：...`
  - `缺口：...`
  - `可買：...`
- Removed standalone display rows for unheld-card `拆解`, `買點`, `不能買`, `還差`, and `可買條件` when they belong to the same entry-check block.
- Updated `tests/test_generator_report.py` to verify the new compact layout and prevent the old split rows from returning.

## Contract Impact

- Telegram unheld-card message layout changes.
- Strategy calculation, trade state machine, blockers, RR, volume, retest, and unlock logic are unchanged.
- Runtime report version remains `v21.1`.
- No DB write/schema/backfill.
- No live Telegram delivery.

## Direct Consumer Sync

- Owner mobile reading:
  - state machine remains in `交易狀態`;
  - market detail remains in `盤面` only when useful;
  - entry decision is read from `進場`;
  - missing condition is read from `缺口`;
  - unlock condition is read from `可買`.
- Existing blocker semantics remain visible without repeating four separate labels.

## Verification

- Local dry-run:
  - `generate_report(dry_run=True)`
  - confirmed unheld cards render `進場` / `缺口` / `可買` and no longer render wall-like `狀態` / `進場檢查`.
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
