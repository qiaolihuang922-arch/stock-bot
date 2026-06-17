# DISPATCH.md

## Active

- task_md_holds: `report_state_sync_v21_1_20260617`
- status: `implemented + QA pass + git completion passed`
- current_version: `v21.1`
- live Telegram delivery: `not run`
- DB schema change: `none`
- DB write/backfill/delete: `none`

## Result Summary

- Fixed user-visible Telegram report-state conflicts from the Owner-pasted `06/17 收盤｜v21.1` report.
- Retest cards now compare current price with the DB-backed retest basis:
  - above basis: `尚未回測`
  - near basis: `回測中，觀察能否守住`
  - below basis: `已跌破，等待重新站回或形成新支撐`
- Holding cards now override stale `未跌破風控` wording when price is below warning.
- Non-limit overheat no longer says `漲停/過熱`; true near-limit cards can still say limit-up.
- Wait-volume cards now show current volume ratio and target threshold.
- After-hours summary no longer includes empty `今日交易 / 新增交易建議：無`, duplicate `明日計畫`, or duplicate unheld non-execution filler.

## Verification

- `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q --tb=short`
  - result: `215 passed`, `46 subtests passed`
- `.\.venv\Scripts\python.exe -m pytest tests\test_unheld_gap_format.py tests\test_trade_state_machine.py tests\test_strategy_buy_path_replay.py tests\test_strategy_rule_outcomes.py -q --tb=short`
  - result: `16 passed`
- `generate_report(dry_run=True)`
  - result: `4` messages, no live Telegram.

## Current Git State

- Implementation and verification complete for this cycle.
- Git completion gate passed by PowerShell equivalent: `main` matches `origin/main`, worktree clean.

## Next Action

- No further product action remains for this cycle.

## Recently Done

- `report_state_sync_v21_1_20260617`: report-state sync fixed, QA passed, Git completion gate passed.
