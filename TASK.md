# TASK: strategy_readability_audit_v21_1_20260615

## Status
- task_id: `strategy_readability_audit_v21_1_20260615`
- task_type: `normal_patch`
- status: `implemented`
- version: `v21.1`
- QA level: `L1`

## Owner Problem
Owner challenged whether the previous change only hard-replaced wording. The report must show evidence according to strategy state, not just rename `RR`. The full visible unheld card should be checked for jargon and misleading generic text.

## User Visible Result
- User-visible Telegram report wording changes:
  - `RR` -> `風險報酬`
  - non-actionable high RR now depends on strategy state:
    - `等型態`: `潛在報酬：好（x倍），但型態/品質未過`
    - `等回測`: `潛在報酬：好（x倍），但尚未回測確認`
    - `淘汰 / 弱反彈`: `潛在報酬：好（x倍），但反彈未轉強`
    - `可準備`: `潛在報酬好（x倍），但需開盤確認`
  - `等RR修復` -> `等風險報酬`
  - `RR不足` -> `風險報酬不足`
- Other visible details are also normalized:
  - `setup` -> `買點型態` in strategy explanation lines.
  - `V10 / V20` -> `10日量 / 20日量`.
  - `風險報酬>=1.5` -> `風險報酬 >= 1.5`.
  - `品質B以上` -> `品質 B 以上`.
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
- Non-actionable high values must be rendered with the active blocker reason, not a generic fixed phrase.
- Visible strategy explanation should avoid raw English/internal shorthand such as `setup`, `V10`, and `V20`.
- `可買條件` must remain future unlock criteria, not a current buy recommendation.

## Version Contract
- Header remains `v21.1`.
- This is a wording/readability patch within the existing v21.1 report contract.

## Acceptance Conditions
- Official generator dry-run shows state-aware potential reward wording for at least `等型態`, `等回測`, and `淘汰 / 弱反彈`.
- Official generator dry-run does not show user-facing `setup`, `V10`, `V20`, `理論RR`, `理論風險報酬`, or unspaced `風險報酬>=`.
- Official generator dry-run does not show user-facing `等RR修復` / `RR不足` in the unheld card or summary funnel.
- Existing formatter/generator tests pass.
- No live Telegram delivery.

## Fixture / Failure Specimen
- Owner sample: 06/15 v21.1 report where RR-related wording, setup wording, and volume shorthand made the card feel like a hard text replacement rather than strategy-aware explanation.
- Required replay route: official `generate_report(dry_run=True)` message list plus formatter tests.

## Forbidden And Blocking Conditions
- Do not hide the risk/reward evidence.
- Do not change the calculation formula or threshold in this task.
- Do not change DB schema or production data.
