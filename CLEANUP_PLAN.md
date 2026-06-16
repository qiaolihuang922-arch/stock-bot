# CLEANUP_PLAN.md

## Completed This Cycle

- Implemented strategy soft-gate patch:
  - HOT / EXTENDED / LIMIT_REBOUND no longer always hard-block.
  - EXTREME / AVOID / LIMIT_LOCK / failed breakout / RR<1.0 remain hard-block.
  - Soft gates can become `可準備` with supporting/confirmed evidence, not `可買`.
- Added post-patch replay artifacts:
  - `reports/audit/strategy_buy_path_replay_v21_1_soft_gates_20260616.json`
  - `reports/audit/strategy_rule_outcomes_v21_1_soft_gates_20260616.json`
- No DB write / no schema change / no live Telegram.
- Full pytest passed.

## Replay Evidence

- Buy-path replay after patch:
  - events: `5798`
  - stocks: `12`
  - `deadlock_suspected=false`
  - `has_real_buyable_path=true`
  - `has_prepare_path=true`
  - `snapshot_tradeable_blocked_by_funnel_days=0`
  - state counts:
    - `可買 700`
    - `可準備 364`
    - `等冷卻 285`
    - `等回測 155`
    - `等接近 2463`
- Rule outcome replay still flags:
  - `隔日確認`
  - `漲停不追`
  - `漲停反彈待確認`
  - `買點品質D`
  - `過熱觀察`
  - `wait_breakout_low_rr`
  - `HOT`

## Previous Cycle Summary

- Added read-only strategy rule outcome audit:
  - script: `scripts/audit_strategy_rule_outcomes.py`
  - artifact: `reports/audit/strategy_rule_outcomes_v21_1_20260616.json`
- Added read-only strategy buy-path DB replay audit:
  - script: `scripts/audit_strategy_buy_path_replay.py`
  - artifact: `reports/audit/strategy_buy_path_replay_v21_1_20260616.json`

## Cleanup Notes

- `.pytest_cache` remains inaccessible to pytest cache writes on this machine (`WinError 5`); this is a local cache warning, not product data.
- No obsolete production DB rows were touched.
- No table was deleted.
- No runtime output was added as source-of-truth.

## Pending Cleanup / Follow-ups

- Further split rule-outcome flags into sub-cases:
  - limit-up lock vs limit-up rebound follow-through.
  - HOT with supporting evidence vs pure chase.
  - quality D caused by no setup vs quality D caused by scoring too strict.
  - low RR caused by bad stop/target vs low RR caused by real poor reward.
- Improve mobile summary only after next strategy replay shows which new `可準備` cases are genuinely useful.
