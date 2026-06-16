# CURRENT_STATE.md

## Current Task

- task_id: `strategy_soft_gate_patch_v21_1_20260616`
- status: `implemented + QA pass + git closeout ready`
- version: `v21.1`
- no live Telegram delivery.
- no DB schema/write/backfill/prune.

## Stable Context

- Owner reads Telegram on mobile; summary must answer decision and next action without repeating raw counts.
- Production dispatch model: Render web service is called every five minutes, then GitHub workflow dispatch runs `run_mode=bot`.
- Production source-of-truth is Supabase / runner data, not local cache, worktree state, runtime dict, or agent memory.
- Cross-day memory must be DB backed.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval unless explicitly authorized.
- Non-schema DB writes/backfills must use approved repo scripts or service APIs; direct hand-written production DML is forbidden.

## Current Implementation State

- Runtime report remains `v21.1`.
- Strategy soft gate patch is implemented in:
  - `core/generator.py`
  - `presentation/report.py`
  - `tests/test_generator_report.py`
- Current hard gates:
  - limit-up lock / `LIMIT_LOCK`
  - `EXTREME`
  - `AVOID`
  - failed breakout / hard failure
  - `RR < 1.0`
- Current soft gates:
  - `HOT`
  - `EXTENDED`
  - `LIMIT_REBOUND`
  - `漲停反彈待確認`
  - low-RR near setup when RR is still >= 1.0
- Soft gates can only become `可準備`, not `可買`, and require supporting/confirmed evidence plus non-weak volume and acceptable quality.

## Verification State

- Full pytest passed:
  - `489 passed, 8 skipped, 165 warnings, 110 subtests passed`
- Generator report tests passed:
  - `206 passed, 153 warnings, 46 subtests passed`
- DB replay artifacts:
  - `reports/audit/strategy_buy_path_replay_v21_1_soft_gates_20260616.json`
  - `reports/audit/strategy_rule_outcomes_v21_1_soft_gates_20260616.json`

## Known Findings

- Buy-path replay after patch shows:
  - `deadlock_suspected=false`
  - `has_real_buyable_path=true`
  - `has_prepare_path=true`
  - snapshot tradeable funnel rejection days: `0`
  - `可買 700`
  - `可準備 364`
- Rule outcome audit still flags these categories for future sub-classification:
  - `隔日確認`
  - `漲停不追`
  - `漲停反彈待確認`
  - `買點品質D`
  - `過熱觀察`
  - `wait_breakout_low_rr`
  - `HOT`

## Next Action

- Push current branch, then run git completion and closeout gates.
