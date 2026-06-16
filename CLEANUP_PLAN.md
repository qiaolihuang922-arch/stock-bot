# CLEANUP_PLAN.md

## Completed This Cycle

- Completed state-specific Telegram card cleanup:
  - holdings: one `決策` plus one `明日處理`.
  - `等冷卻`: `狀態` plus `等待`.
  - `等回測`: `狀態` plus concrete `回測` anchor plus `有效買點`.
  - `等型態`: `狀態` plus `等待` plus `有效買點`.
  - `等接近`: one breakout zone reference plus concise wait condition.
- Preserved `距突破` on all relevant cards.
- No DB write / no schema change / no live Telegram.
- Full pytest passed.

## Replay / Test Evidence

- Targeted report/state tests:
  - `215 passed, 155 warnings, 46 subtests passed`
- Full tests:
  - `489 passed, 8 skipped, 165 warnings, 110 subtests passed`
- Official generator dry-run:
  - `4` messages generated.

## Previous Cycle Summary

- Implemented strategy soft-gate patch:
  - HOT / EXTENDED / LIMIT_REBOUND no longer always hard-block.
  - EXTREME / AVOID / LIMIT_LOCK / failed breakout / RR<1.0 remain hard-block.
  - Soft gates can become `可準備` with supporting/confirmed evidence, not `可買`.
- Added read-only replay artifacts:
  - `reports/audit/strategy_buy_path_replay_v21_1_soft_gates_20260616.json`
  - `reports/audit/strategy_rule_outcomes_v21_1_soft_gates_20260616.json`

## Cleanup Notes

- `.pytest_cache` remains inaccessible to pytest cache writes on this machine (`WinError 5`); this is a local cache warning, not product data.
- No obsolete production DB rows were touched.
- No table was deleted.
- No runtime output was added as source-of-truth.

## Follow-ups

- Further split rule-outcome flags into sub-cases in a separate strategy replay task:
  - limit-up lock vs limit-up rebound follow-through.
  - HOT with supporting evidence vs pure chase.
  - quality D caused by no setup vs quality D caused by scoring too strict.
  - low RR caused by bad stop/target vs low RR caused by real poor reward.
- Improve mobile summary only after next strategy replay shows which new `可準備` cases are genuinely useful.
