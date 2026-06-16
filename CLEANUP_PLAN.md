# CLEANUP_PLAN.md

## Completed This Cycle

- Compressed current handoff files for `cross_day_source_truth_v21_1_20260616`.
- Fixed the multi-day rebound source contract:
  - no DB `daily_price` context means no multi-day rebound upgrade;
  - report payload `closes` remains same-run technical data only.
- Added tests that fail if payload closes are again used as fake cross-day memory.
- No runtime output, SQL draft, or temporary artifact was added.
- No DB rows/tables were changed.

## Previous Cycle Summary

- Compressed current handoff files for `multi_day_rebound_retest_v21_1_20260616`.
- Added a reusable multi-day rebound repair rule instead of hard-coding 旺宏.
- Follow-up from that cycle is now closed by this cycle: the repair rule is DB source-gated.

## Earlier Cycle Summary

- Compressed current handoff files for `holding_card_contract_v21_1_20260616`.
- Holding-card report rows were reduced by moving from verbose state/stat/history rows to a decision contract.
- No DB rows/tables were changed.

## Cleanup Notes

- `.pytest_cache` remains inaccessible to pytest cache writes on this machine (`WinError 5`); this is a local cache warning, not product data. No cleanup action taken.
- Fixed active task docs are UTF-8 readable:
  - `TASK.md`
  - `CHANGELOG.md`
  - `QA_REPORT.md`
  - `DISPATCH.md`
  - `CURRENT_STATE.md`
- Global source scan notes:
  - DB-backed cross-day memory: `services/cross_day_context.py`, `load_backtest_context`, market/theme evidence.
  - Same-run technical indicators: `services/analysis.py`, `core/signal_snapshot.py`, `load_report_daily_kline`.
  - Trend continuation uses a fixed research artifact plus OHLCV rows; existing tests ensure missing OHLCV source rows fail closed. Treat deeper refactor as separate research task if needed.

## Pending Cleanup / Follow-ups

- Observe next production `run_mode=bot` artifact for the DB-gated multi-day rebound repair wording.
- Observe next production `run_mode=bot` artifact for the new holding-card decision contract.
- Review older mojibake in long-lived docs only in a dedicated documentation hygiene cycle; avoid mixing with product strategy patches.
- Prior DB cleanup follow-ups:
  - `market_theme_index_daily_bars`: decide whether placeholder OHLCV/member columns should be populated or hidden.
  - `signal_outcomes`: implement or retire max-high/drawdown metrics.
