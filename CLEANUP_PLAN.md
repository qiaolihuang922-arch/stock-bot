# CLEANUP_PLAN.md

## Completed This Cycle

- Added read-only strategy buy-path DB replay audit:
  - script: `scripts/audit_strategy_buy_path_replay.py`;
  - artifact: `reports/audit/strategy_buy_path_replay_v21_1_20260616.json`;
  - no DB write / no schema change / no live Telegram.

## Previous Cycle Summary

- Compressed current handoff files for `rebound_retest_anchor_wording_v21_1_20260616`.
- Fixed overclaimed rebound retest wording:
  - `最近修復支撐` replaced by `最近反彈收盤`;
  - cross-day memory remains DB `daily_price` gated;
  - no strategy threshold / DB write / live Telegram change.

## Earlier Cycle Summary

- Compressed current handoff files for `explicit_approach_zone_wording_v21_1_20260616`.
- Fixed vague `等接近` wording:
  - `買點區 / 觸發區` replaced with concrete `突破區 low~high` when data exists;
  - no strategy threshold / DB write / live Telegram change.

## Earlier Cycle Summary

- Compressed current handoff files for `afterhours_summary_trade_plan_v21_1_20260616`.
- Fixed afterhours summary noise:
  - removed market/count line and duplicate today-buy status line;
  - removed empty `新增有效進場：無` placeholder;
  - hides no-action `未持倉狀態` funnel;
  - summary now keeps conclusion, tomorrow plan and holding risk checklist.
- No DB rows/tables were changed.

## Earlier Cycle Summary

- Compressed current handoff files for `dry_run_strategy_evidence_near_breakout_v21_1_20260616`.
- Fixed local dry-run false source-missing:
  - dry-run now read-only loads strategy evidence;
  - no DB write/live Telegram added;
  - near-breakout C-quality tracking no longer falls through to `淘汰`.

## Earlier Cycle Summary

- Compressed current handoff files for `rebound_retest_source_gate_v21_1_20260616`.
- Fixed rebound / source-gate report contract:
  - multi-day rebound repair now waits for DB-backed recent support retest;
  - source-only missing/error no longer displays as strategy淘汰;
  - source-unavailable cards no longer show actionable RR;
  - no DB rows/tables were changed.

## Older Cycle Summary

- Compressed current handoff files for `near_breakout_tracking_contract_v21_1_20260616`.
- Fixed near-breakout contract mismatch:
  - `<=5%` is now consistently `接近突破`;
  - `>5%` is the consistent遠離 threshold;
  - near-breakout C-quality observation no longer falls through to `淘汰`;
  - weak rebound / hard failure paths remain conservative.
- Added official message-list regression for the Owner-style 聯電 `4.25%` failure specimen.
- No DB rows/tables were changed.

## Archived Cycle Summary

- Compressed current handoff files for `cross_day_source_truth_v21_1_20260616`.
- Fixed the multi-day rebound source contract:
  - no DB `daily_price` context means no multi-day rebound upgrade;
  - report payload `closes` remains same-run technical data only.
- Added tests that fail if payload closes are again used as fake cross-day memory.
- No runtime output, SQL draft, or temporary artifact was added.
- No DB rows/tables were changed.

## Archived Cycle Summary 2

- Compressed current handoff files for `multi_day_rebound_retest_v21_1_20260616`.
- Added a reusable multi-day rebound repair rule instead of hard-coding 旺宏.
- Follow-up from that cycle is now closed by this cycle: the repair rule is DB source-gated.

## Archived Cycle Summary 3

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
