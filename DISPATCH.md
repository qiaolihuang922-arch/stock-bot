# DISPATCH.md

## Active

- task_md_holds: `strategy_rule_outcome_audit_v21_1_20260616`
- status: `implemented + QA conditional pass + full pytest passed`
- current_version: `v21.1`
- no live Telegram delivery in this cycle.
- no DB schema/write/backfill/prune in this cycle.

## Result Summary

- Owner asked to verify every strategy gate after DB replay.
- Implemented read-only outcome audit:
  - `scripts/audit_strategy_rule_outcomes.py`
  - artifact: `reports/audit/strategy_rule_outcomes_v21_1_20260616.json`
- Main result:
  - events: `5798`
  - events_with_10d_outcome: `5678`
  - audit flags: `7`
  - `等量能` and `急彈待回測` are not the main over-strict gates.
  - hot / limit-up / low-RR / broad quality-D gates need next strategy patch.

## Verification

- Targeted tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_strategy_rule_outcomes.py tests\test_strategy_buy_path_replay.py -q --tb=short`
  - result: `5 passed, 1 warning`
- Full:
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - result: `489 passed, 8 skipped, 165 warnings, 110 subtests passed`
- DB replay:
  - `.\.venv\Scripts\python.exe scripts\audit_strategy_rule_outcomes.py --lookback-days 730 --version v21.1 --output reports\audit\strategy_rule_outcomes_v21_1_20260616.json`
  - result: artifact generated.

## Current Git State

- branch: `main`
- latest pushed commit: `1c5babf`
- completion: pushed; git completion gate pending.

## Next Action

- Run git completion gate.
