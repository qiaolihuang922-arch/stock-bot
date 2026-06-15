# TASK: rr_wording_readability_v21_1_20260615

## Status
- task_id: `rr_wording_readability_v21_1_20260615`
- task_type: `tiny_patch`
- status: `implemented`
- version: `v21.1`
- QA level: `L1`

## Owner Problem
Owner reported that `理論RR 3.82僅參考` is still not understandable. The report should make the value's direction obvious: whether it is good or bad, and whether it is currently buyable.

## User Visible Result
- User-visible Telegram report wording changes:
  - `RR` -> `風險報酬`
  - `理論RR 3.82僅參考` -> `潛在報酬：好（3.82倍），買點未成立`
  - `等RR修復` -> `等風險報酬`
  - `RR不足` -> `風險報酬不足`
- Example:
  - before: `不能買：RR 還不夠`
  - after: `不能買：風險報酬還不夠`
- The meaning is unchanged: risk/reward is the expected reward divided by the risk from entry to stop. High non-actionable values are shown as good potential, while explicitly saying the buy setup has not formed.

## Non Goals
- No live Telegram delivery.
- No strategy threshold changes.
- No buy/sell decision changes.
- No DB schema / RLS / grant / policy / role / index / constraint changes.
- No backfill or production DML.
- No version bump beyond existing `v21.1`.

## Impacted Modules And Direct Consumers
- `presentation/report.py`
  - Direct consumer: official Telegram message list from `core.generator.generate_report`.
- `core/generator.py`
  - Direct consumer: summary funnel labels and helper text.
- `tests/test_unheld_gap_format.py`
  - Direct consumer: formatter-level wording regression.
- `tests/test_generator_report.py`
  - Direct consumer: official report / message-list wording regression.

## Output Contract
- User-visible report text must not require knowing the abbreviation `RR`.
- Internal state names may remain unchanged where needed for code compatibility, but final Telegram strings must render as `風險報酬`.
- Non-actionable high values must be rendered as `潛在報酬：好（x倍），買點未成立`, not as `理論RR` or `僅參考`.
- `可買條件` must remain future unlock criteria, not a current buy recommendation.

## Version Contract
- Header remains `v21.1`.
- This is a wording/readability patch within the existing v21.1 report contract.

## Acceptance Conditions
- Official generator dry-run shows `等風險報酬`, `風險報酬不足`, and `潛在報酬：好（x倍），買點未成立`.
- Official generator dry-run does not show user-facing `等RR修復` / `RR不足` in the unheld card or summary funnel.
- Existing formatter/generator tests pass.
- No live Telegram delivery.

## Fixture / Failure Specimen
- Owner sample: 06/15 v21.1 report where `RR`, `理論RR`, and `等RR修復` made the report hard to understand.
- Required replay route: official `generate_report(dry_run=True)` message list plus formatter tests.

## Forbidden And Blocking Conditions
- Do not hide the risk/reward evidence.
- Do not change the calculation formula or threshold in this task.
- Do not change DB schema or production data.
