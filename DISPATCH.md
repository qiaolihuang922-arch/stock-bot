# DISPATCH.md

## Active

- task_md_holds: `rebound_retest_anchor_wording_v21_1_20260616`
- status: `implemented + QA passed + full pytest passed`
- current_version: `v21.1`
- no live Telegram delivery in this cycle.
- no DB schema/write/backfill/prune in this cycle.

## Result Summary

- Owner challenged `等回測｜反彈修復待回測` wording:
  - `最近修復支撐 53.3` looked like a computed/confirmed support level.
  - Actual source is DB-backed `daily_price` recent closes, not a support algorithm.
- Implemented:
  - report now says `最近反彈收盤 N 附近`;
  - removed user-visible overclaim that the recent close is a confirmed support;
  - strategy gates and DB read/write paths were not changed.

## Verification

- Targeted official formatter:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py::GeneratorReportTest::test_v21_1_strong_rebound_uses_multi_window_retest_context tests\test_generator_report.py::GeneratorReportTest::test_v21_1_multi_day_weak_rebound_repairs_from_rejected_to_retest_wait tests\test_generator_report.py::GeneratorReportTest::test_v21_1_retest_anchor_says_breakout_zone_when_price_is_below_zone -q --tb=short`
  - result: `3 passed, 5 warnings`
- Official dry-run:
  - 群創:
    - `缺口：等待回測最近反彈收盤 53.3 附近不破`
    - `可買：回測最近反彈收盤 53.3 附近不破 + 非追高 + 量能有效`
  - 旺宏:
    - `缺口：等待回測最近反彈收盤 166.5 附近不破`
- Full:
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - result: `484 passed, 8 skipped, 165 warnings, 110 subtests passed`

## Current Git State

- branch: `main`
- completion: pending commit/push.

## Next Action

- Commit, push, then run git completion gate.
