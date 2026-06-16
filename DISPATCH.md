# DISPATCH.md

## Active

- task_md_holds: `explicit_approach_zone_wording_v21_1_20260616`
- status: `implemented + QA passed + full pytest passed`
- current_version: `v21.1`
- no live Telegram delivery in this cycle.
- no DB schema/write/backfill/prune in this cycle.

## Result Summary

- Owner challenged `等接近` card wording: `還沒到買點區` was too vague and did not say which zone.
- Implemented:
  - `等接近` now names the concrete breakout zone when available.
  - fallback is `突破區/回測支撐`, not `買點區`.
  - strategy thresholds and DB were not changed.

## Verification

- Targeted:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py tests\test_trade_state_machine.py -q --tb=short -k "far_low_volume or breakout_distance_gate or unheld_far_from_trigger or 等接近"`
  - result: `3 passed, 212 deselected, 5 warnings`
- Full:
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - result: `484 passed, 8 skipped, 165 warnings, 110 subtests passed`
- Official dry-run:
  - 技嘉:
    - `進場：不買，等接近突破區 399~400.99｜原因：尚未接近突破區`
    - `缺口：距突破 15.23%，尚未接近突破區 399~400.99`

## Current Git State

- branch: `main`
- completion: git completion passed after push.

## Next Action

- Observe next production `run_mode=bot` artifact.
