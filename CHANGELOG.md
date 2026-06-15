# CHANGELOG: unheld_card_mobile_denoise_20260616

## Changes

- Replaced the prior hard-concat mobile layout with structured entry evidence in `presentation/report.py`.
- Added `_unheld_entry_contract` so the official generator selects the state-specific blocker before formatting.
- Kept `_unheld_buy_gap_line` as a compatibility wrapper, but it now returns the same scoped contract text instead of the former full metric package.
- Unheld waiting / rejected cards now render short decision rows:
  - `進場：...｜原因：...`
  - `缺口：...`
  - `可買：...`
- `距突破：...` is explicitly retained as a standalone line and is not folded into the blocker text.
- `_entry_check_lines` now consumes structured `缺口` / `可買` evidence instead of parsing old multiline blocker text on the official path:
  - retest cards focus on the retest / breakout zone;
  - cooling cards focus on heat;
  - risk-reward cards focus on the risk-reward gap;
  - setup cards focus on setup / quality;
  - rejected cards focus on the repair requirement.
- Normal waiting / rejected unheld cards no longer print the broad `數據：...` metric dump; source/data failure cards still keep fail-closed evidence.
- Normal waiting / rejected unheld cards no longer repeat `交易狀態：...` when title and `進場` already carry the same state.
- Unheld `歷史：...` rows are now gated: repair / positive weight / high-signal prior execution remains visible; ordinary repeated failure history is suppressed.
- Removed the previous post-format state-scoping parser so there is only one active rule source for unheld entry evidence.
- Removed standalone display rows for unheld-card `拆解`, `買點`, `不能買`, `還差`, and `可買條件` when they belong to the same entry-check block.
- Updated `tests/test_generator_report.py` and `tests/test_unheld_gap_format.py` to verify the new compact layout, state-scoped helper contract, and prevent old split rows / full metric packages from returning.

## Contract Impact

- Telegram unheld-card message layout changes.
- Strategy calculation, trade state machine, blockers, RR, volume, retest, and unlock logic are unchanged.
- This is not a hard text-only rename: the displayed blocker details are selected in a structured contract before formatting.
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
  - confirmed unheld cards render `進場` / `缺口` / `可買` without repeated `交易狀態`.
  - latest dry-run line counts: `trade_state=0`, `history=0`, `data=0` in current unheld output.
  - 旺宏 example keeps `距突破：10.93%｜遠離突破` and narrows `缺口` to `站回突破區 175.5~176.38`.
  - `legacy_split_rows=0`; `data_lines_total=0`.
- Test command:
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - result: `479 passed, 8 skipped, 108 subtests passed`

## Covered Layers

- Presentation helper.
- Official Telegram generator formatting.
- User-visible replay via dry-run.

## Residual Risk

- Some old `原因` lines for rejected cards can still be verbose; this task intentionally focused on the duplicated state/entry-check block.
- Holding cards keep the previous layout.
