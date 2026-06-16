# DISPATCH.md

## Active

- task_md_holds: `near_breakout_tracking_contract_v21_1_20260616`
- status: `implemented + QA passed + full pytest passed + pushed`
- current_version: `v21.1`
- no live Telegram delivery in this cycle.
- no DB schema/write/backfill/prune in this cycle.

## Result Summary

- Owner challenged why 聯電 `距突破 4.25%` showed `遠離突破` and `⛔ 淘汰｜觀察`.
- Root cause:
  - Display layer used `<4%` for `接近突破`.
  - Strategy distance policy already uses `<=5%` as near breakout.
  - RR hidden reason / final label still used `>4%` as遠離.
  - Funnel did not preserve the near-breakout C-quality observation middle state, so it could fall to default `淘汰`.
- Implemented:
  - `<=5%` now displays `接近突破`.
  - `>5%` is the consistent `遠離` threshold.
  - Near-breakout, non-hard-fail, C-quality observation remains tracked / confirmation, not淘汰.
  - Weak rebound and hard failure remain conservative and are not loosened.

## Verification

- Targeted:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q --tb=short -k "near_breakout_soft_blocker or breakout_distance or rejected_weak_rr or far_from_trigger_tracks"`
  - result: `6 passed, 12 subtests passed`
- Broader:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py tests\test_analysis_engine.py tests\test_trend_continuation.py -q --tb=short`
  - result: `255 passed, 46 subtests passed`
- Full:
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - result: `482 passed, 8 skipped, 110 subtests passed`

## Current Git State

- branch: `main`
- completion: git completion passed after push.

## Next Action

- Observe next scheduled `run_mode=bot` artifact.
