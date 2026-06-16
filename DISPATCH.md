# DISPATCH.md

## Active

- task_md_holds: `rebound_retest_source_gate_v21_1_20260616`
- status: `implemented + QA passed + full pytest passed + pushed`
- current_version: `v21.1`
- no live Telegram delivery in this cycle.
- no DB schema/write/backfill/prune in this cycle.

## Result Summary

- Owner challenged whether the current per-stock feedback still matches common trading practice, because:
  - 旺宏 / 群創 had multi-day repair but previously still read like淘汰;
  - 聯電 near-breakout / source-missing could still become淘汰;
  - report wording made 回測 look like every stock must first reclaim the old breakout high.
- Implemented:
  - `can_buy` distance policy now rejects only `>5%`, consistent with the displayed near-breakout zone.
  - multi-day rebound repair now waits for a DB-backed recent repair support retest, not a mandatory old-high reclaim.
  - source-only missing / source-error is fail-closed as `等資料` / `不可行動`, not strategy淘汰.
  - source/strategy unavailable cards no longer show actionable RR numbers.
  - 等資料 card noise reduced for mobile reading.

## Verification

- Focused report / strategy:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py tests\test_analysis_engine.py tests\test_trade_state_machine.py tests\test_unheld_gap_format.py tests\test_trend_continuation.py -q --tb=short`
  - result: `268 passed, 46 subtests passed`
- Full:
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - result: `484 passed, 8 skipped, 110 subtests passed`
- Official dry-run:
  - `generate_report(dry_run=True)`
  - result: 聯電=`等資料`; 旺宏/群創=`等回測｜反彈修復待回測`.

## Current Git State

- branch: `main`
- completion: git completion passed after push.

## Next Action

- Observe next scheduled `run_mode=bot` artifact.
