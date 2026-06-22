# DISPATCH.md

## Active

- task_md_holds: `low_repair_ready_state_v21_1_20260622`
- status: `implemented + QA conditional pass + pending commit/push`
- current_version: `v21.1`
- live Telegram delivery: `not run`
- DB schema change: `none`
- DB write/backfill/delete: `none`

## Result Summary

- Fixed the Owner-pasted `06/22 盤後｜v21.1` conflict where `3231 緯創` displayed all low-repair conditions as satisfied but still stayed in `等低位修復`.
- Added DB-backed low-repair readiness status:
  - support not broken
  - price above 5-day MA
  - volume effective
  - risk/reward >= 1.5
- Low-repair-ready candidates now promote to `可準備｜低位修復成立`, not immediate `可買` in after-hours.
- Incomplete low-repair cards continue to show missing conditions, e.g. `2324 仁寶` still missing `站回5日均 37.54`.
- Summary funnel count no longer double-counts `隔日確認` as `僅追蹤`.

## Verification

- Targeted report tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q -k "low_repair or unheld_funnel or next_day_confirmation or cooling_and_next_day or b5_tracking or postmarket_unheld_gate" --tb=short`
  - result: `12 passed`
- Adjacent state/replay tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_unheld_gap_format.py tests\test_trade_state_machine.py tests\test_strategy_buy_path_replay.py tests\test_strategy_rule_outcomes.py -q --tb=short`
  - result: `16 passed`
- Full report tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q --tb=short`
  - result: `215 passed`, `1 failed`
  - remaining unrelated failure: `test_v20_4_47_generate_report_appends_live_readonly_future_watch_sources`
- Official dry-run:
  - `generate_report(dry_run=True)`
  - result: `top_messages=2`, `flat_messages=5`, no live Telegram.

## Current Git State

- Worktree has uncommitted implementation and documentation changes.
- Git completion gate not yet run for this cycle.

## Next Action

- Commit and push this cycle, then run git completion gate.
- Track the unrelated future-watch source test separately; do not mix it into this low-repair fix.

## Recently Done

- `report_state_sync_v21_1_20260617`: report-state sync fixed, QA passed, Git completion gate passed.
- `low_repair_ready_state_v21_1_20260622`: low-repair-ready state/display conflict fixed; QA conditional pass pending git closeout.
