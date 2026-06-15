# TASK: unheld_readability_v21_1_20260615

## Status
- task_id: `unheld_readability_v21_1_20260615`
- task_type: `normal_patch`
- status: `implemented`
- version: `v21.1`
- QA level: `L2`

## Owner Problem
Owner reported the v21.1 unheld Telegram cards are technically richer but still hard to understand on mobile. The cards expose strategy diagnostics (`卡關主因`, `量化差距`, `解鎖`, `補充`) instead of answering the trading question plainly: why can I not buy now, what is missing, and exactly what would make it buyable.

## User Visible Result
- Unheld blocker cards now use decision-first language:
  - `不能買：...`
  - `還差：...`
  - `可買條件：...`
- Long diagnostic chains are compacted:
  - RR不足 becomes `RR 1.32→1.5（差0.18）`.
  - Quality becomes `品質 D→B以上`.
  - Volume becomes `量能偏弱（V10 ... / V20 ...）`.
  - Retest/breakout context becomes `站回突破區 ...` or `回測區 ...不破`.
- Theoretical RR remains visibly non-actionable: `理論RR ...僅參考`.
- No buy/sell strategy thresholds, DB schema, or live Telegram delivery are changed.

## Non Goals
- No live Telegram delivery.
- No DB schema / RLS / grant / policy / role / index / constraint changes.
- No backfill or production DML.
- No loosening of buy rules, RR thresholds, heat gates, volume gates, or state-machine decisions.
- No version bump beyond existing `v21.1`.

## Impacted Modules And Direct Consumers
- `presentation/report.py`
  - Direct consumer: official Telegram message list from `core.generator.generate_report`.
- `tests/test_unheld_gap_format.py`
  - Direct consumer: formatter-level regression for compact blocker text.
- `tests/test_generator_report.py`
  - Direct consumer: official report / message-list regression for mobile readability and no-buy semantics.

## Output Contract
- Non-actionable unheld cards must not display old diagnostic labels:
  - avoid `卡關主因：`, `量化差距：`, `解鎖：`, and repeated `補充：` lines as the main explanation.
- Required order for blocker evidence:
  1. `不能買：<human reason>`
  2. `還差：<compact measurable gap>`
  3. `可買條件：<specific actionable condition>`
- `可買條件` must describe future conditions, not imply a current buy recommendation.
- Actionable cards must not gain `不能買` / `還差` noise.

## Version Contract
- Header remains `v21.1`.
- This is a report readability patch within the v21.1 strategy-evidence contract.

## Acceptance Conditions
- Official generator dry-run must show the Owner-style unheld cards with the new three-line structure.
- Tests must cover RR不足, overheat, sharp rebound/retest, weak setup/quality, source-error, and post-market prepare paths.
- Report must still avoid `可立即買` / `建議買入` wording for non-actionable cards.
- No live Telegram delivery.

## Fixture / Failure Specimen
- Owner sample: 06/15 v21.1 unheld report where `旺宏`, `緯創`, `仁寶`, `技嘉`, `聯電`, `華邦電`, `南亞科`, and `群創` were understandable only by reading internal diagnostics.
- Required replay route: official `generate_report(dry_run=True)` message list plus formatter tests.

## Forbidden And Blocking Conditions
- Do not change strategy decisions to make cards look better.
- Do not hide blockers that explain why a stock is not buyable.
- Do not present theoretical RR as buy evidence.
- Do not add DB fields or write production data for this readability-only task.
