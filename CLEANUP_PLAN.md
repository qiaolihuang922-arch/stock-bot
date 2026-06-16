# CLEANUP_PLAN.md

## Completed This Cycle

- Compressed current handoff files for `holding_card_contract_v21_1_20260616`.
- Holding-card report rows were reduced by moving from verbose state/stat/history rows to a decision contract.
- No runtime output, SQL draft, or temporary artifact was added for this cycle.
- No DB rows/tables were changed.

## Previous Cycle Summary

- Compressed current handoff files for `approach_distance_gap_v21_1_20260616`.
- No runtime output, SQL draft, or temporary artifact was added.
- No DB rows/tables were changed.

## Cleanup Notes

- `.pytest_cache` remains inaccessible to pytest cache writes on this machine (`WinError 5`); this is a local cache warning, not product data. No cleanup action taken.
- Fixed active task docs are now UTF-8 readable:
  - `TASK.md`
  - `CHANGELOG.md`
  - `QA_REPORT.md`
  - `DISPATCH.md`
  - `CURRENT_STATE.md`

## Pending Cleanup / Follow-ups

- Observe next production `run_mode=bot` artifact for the new holding-card decision contract.
- Observe next production `run_mode=bot` artifact for the new unheld-card priority ordering.
- Review older mojibake in long-lived docs only in a dedicated documentation hygiene cycle; avoid mixing with product strategy patches.
- Prior DB cleanup follow-ups:
  - `market_theme_index_daily_bars`: decide whether placeholder OHLCV/member columns should be populated or hidden.
  - `signal_outcomes`: implement or retire max-high/drawdown metrics.
