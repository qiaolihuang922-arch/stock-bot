# CLEANUP_PLAN.md

## Completed This Cycle

- Added read-only strategy rule outcome audit:
  - script: `scripts/audit_strategy_rule_outcomes.py`;
  - artifact: `reports/audit/strategy_rule_outcomes_v21_1_20260616.json`;
  - no DB write / no schema change / no live Telegram.
- Outcome audit now validates strategy gates by real forward DB daily-price outcomes.
- Recorded flags for next strategy patch instead of pretending the current strategy is complete.

## Previous Cycle Summary

- Added read-only strategy buy-path DB replay audit:
  - script: `scripts/audit_strategy_buy_path_replay.py`;
  - artifact: `reports/audit/strategy_buy_path_replay_v21_1_20260616.json`;
  - no DB write / no schema change / no live Telegram.

## Earlier Cycle Summary

- Fixed overclaimed rebound retest wording:
  - `最近修復支撐` replaced by `最近反彈收盤`;
  - cross-day memory remains DB `daily_price` gated;
  - no strategy threshold / DB write / live Telegram change.

## Earlier Cycle Summary

- Fixed vague `等接近` wording:
  - `買點區 / 觸發區` replaced with concrete `突破區 low~high` when data exists;
  - no strategy threshold / DB write / live Telegram change.

## Earlier Cycle Summary

- Fixed afterhours summary noise:
  - removed market/count line and duplicate today-buy status line;
  - removed empty `新增有效進場：無` placeholder;
  - hides no-action `未持倉狀態` funnel;
  - summary now keeps conclusion, tomorrow plan and holding risk checklist.

## Earlier Cycle Summary

- Fixed local dry-run false source-missing:
  - dry-run now read-only loads strategy evidence;
  - no DB write/live Telegram added;
  - near-breakout C-quality tracking no longer falls through to `淘汰`.

## Earlier Cycle Summary

- Fixed rebound / source-gate report contract:
  - multi-day rebound repair now waits for DB-backed recent support retest;
  - source-only missing/error no longer displays as strategy淘汰;
  - source-unavailable cards no longer show actionable RR;
  - no DB rows/tables were changed.

## Older Cycle Summary

- Fixed near-breakout contract mismatch:
  - `<=5%` is now consistently `接近突破`;
  - `>5%` is the consistent遠離 threshold;
  - near-breakout C-quality observation no longer falls through to `淘汰`;
  - weak rebound / hard failure paths remain conservative.

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
  - Trend continuation uses a fixed research artifact plus OHLCV rows; existing tests ensure missing OHLCV source rows fail closed.

## Pending Cleanup / Follow-ups

- Next strategy patch should address outcome-audit flags:
  - split hot / limit-up follow-through from pure chase risk;
  - split quality D into weak-D vs repair-D;
  - re-check low-RR target/stop anchors.
- Observe next production `run_mode=bot` artifact for DB-gated multi-day rebound repair wording.
- Review older mojibake in long-lived docs only in a dedicated documentation hygiene cycle; avoid mixing with product strategy patches.
- Prior DB cleanup follow-ups:
  - `market_theme_index_daily_bars`: decide whether placeholder OHLCV/member columns should be populated or hidden.
  - `signal_outcomes`: implement or retire max-high/drawdown metrics.
