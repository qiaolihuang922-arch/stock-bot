# CURRENT_STATE.md

## Current Task

- task_id: `strategy_rule_outcome_audit_v21_1_20260616`
- status: `implemented + QA conditional pass + full pytest passed`
- version: `v21.1`
- no live Telegram delivery.
- no DB schema/write/backfill/prune.

## Stable Context

- Owner reads Telegram on mobile; summary must answer decision, next action and risk, not repeat raw counts.
- Production dispatch model: Render web service is called every five minutes, then GitHub workflow dispatch runs `run_mode=bot`.
- Production source-of-truth is Supabase / runner data, not local cache, worktree state, runtime dict, or agent memory.
- Cross-day memory must be DB backed.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval unless explicitly authorized.
- Non-schema DB writes/backfills must use approved repo scripts or service APIs; direct hand-written production DML is forbidden.

## Current Implementation State

- Runtime report remains `v21.1`.
- Existing read-only buy-path replay:
  - `scripts/audit_strategy_buy_path_replay.py`
  - `reports/audit/strategy_buy_path_replay_v21_1_20260616.json`
- New read-only rule outcome replay:
  - `scripts/audit_strategy_rule_outcomes.py`
  - `reports/audit/strategy_rule_outcomes_v21_1_20260616.json`
- Rule outcome result:
  - events: `5798`
  - events_with_10d_outcome: `5678`
  - flags: `7`

## Verification State

- Targeted rule replay tests passed: `5 passed, 1 warning`.
- Full pytest passed: `489 passed, 8 skipped, 165 warnings, 110 subtests passed`.
- Code, tests, artifact and handoff docs pushed in commit `1c5babf`; git completion gate pending.

## Known Findings

- `等量能` is not currently the strongest over-strict signal.
- `急彈待回測` has support as a blocker on 5-day outcome.
- Hot / limit-up / low-RR / broad quality-D gates need next strategy patch:
  - `隔日確認`
  - `漲停不追`
  - `漲停反彈待確認`
  - `買點品質D`
  - `過熱觀察`
  - `wait_breakout_low_rr`
  - `HOT`
