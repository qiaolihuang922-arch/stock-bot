# DISPATCH.md

## Active

- task_md_holds: `entry_quality_priority_v21_1_20260616`
- status: `implemented + QA passed + pushed`
- current_version: `v21.1`
- no live Telegram delivery in this cycle.
- no DB schema/write/backfill in this cycle.

## Result Summary

- Owner reported that 06/16 pre-market unheld cards still looked like `market/quality D` was the main blocker, making the system appear unable to find any buy timing.
- Implemented strategy-priority ordering:
  - heat / limit-up / overheat before quality;
  - rebound before quality;
  - RR before quality;
  - distance / approach before stock weakness where applicable;
  - quality D only remains as setup-quality detail or fallback when no clearer blocker exists.
- Official dry-run now shows:
  - `華邦電`: `等回測｜漲停不追`;
  - `南亞科`: `等冷卻｜過熱觀察`;
  - `聯電`: `等風險報酬｜觀察`;
  - `緯創 / 仁寶 / 技嘉`: `等接近｜遠離觸發`;
  - `旺宏`: `等回測｜急彈待回測`;
  - `群創`: `淘汰｜弱反彈待確認`.
- `距突破` remains independently displayed.

## Verification

- Dry-run:
  - `generate_report(dry_run=True)`
  - checked unheld official message.
- Targeted tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_analysis_engine.py tests\test_trade_state_machine.py tests\test_unheld_gap_format.py tests\test_generator_report.py -q --tb=short`
  - result: `257 passed, 44 subtests passed`
- Full tests:
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - result: `479 passed, 8 skipped, 108 subtests passed`
- No live Telegram delivery.
- No DB schema/write/backfill.

## Current Git State

- branch: `main`
- upstream: `origin/main`
- latest commit: `cae33d3 Prioritize actionable unheld blockers`
- HEAD equals upstream: true after push
- worktree/index: clean after closeout push

## Next Action

- Observe next scheduled `run_mode=bot` report and confirm production Telegram artifact matches dry-run priority ordering.
