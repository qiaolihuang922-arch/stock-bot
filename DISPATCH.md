# DISPATCH.md

## Active

- task_md_holds: `cross_day_source_truth_v21_1_20260616`
- status: `implemented + QA passed, pending commit/push`
- current_version: `v21.1`
- no live Telegram delivery in this cycle.
- no DB schema/write/backfill/prune in this cycle.
- DB access: read-only `daily_price` verification only.

## Result Summary

- Owner challenged the source of "recent four price points".
- Root cause: previous multi-day rebound repair used report payload `closes` / `price`, which are Yahoo/TWSE loader values, not production DB cross-day source-of-truth.
- Implemented source gate:
  - `daily_price` is now part of cross-day persistent sources.
  - `build_cross_day_contexts` reads recent `daily_price` close points.
  - `multi_day_rebound_needs_retest` uses only `cross_day_context.recent_daily_price_points`.
  - Without DB `daily_price` points, payload `closes` cannot trigger `反彈修復待回測`.
- Technical indicators may still use Yahoo/TWSE payload for same-run MA/volume/distance calculations, but not for cross-day memory claims.

## Verification

- Targeted:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_cross_day_context.py tests\test_generator_report.py -q --tb=short -k "multi_day_weak_rebound or daily_price_points or weak_rebound or rebound"`
  - result: `3 passed`
- Broader:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_cross_day_context.py tests\test_generator_report.py tests\test_analysis_engine.py tests\test_trend_continuation.py -q --tb=short`
  - result: `260 passed, 44 subtests passed`
- Evidence tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_strategy_evidence.py tests\test_market_theme_evidence.py tests\test_volume_calibration.py -q --tb=short`
  - result: `53 passed, 13 subtests passed`
- Full:
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - result: `481 passed, 8 skipped, 108 subtests passed`
- Dry-run:
  - `generate_report(dry_run=True)`
  - 旺宏 shows `等回測｜反彈修復待回測`; `淘汰｜弱反彈待確認` absent.
- Production read-only:
  - `daily_price` 2337 recent close points include 135.0 -> 140.0 -> 146.5 -> 159.0.

## Current Git State

- pending final git completion:
  - commit current code/docs changes.
  - push to upstream.
  - run git completion gate.

## Next Action

- Commit/push this source-of-truth fix, then observe next scheduled `run_mode=bot` artifact.
