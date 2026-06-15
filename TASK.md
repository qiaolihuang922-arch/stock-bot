# TASK: acute_rebound_retest_anchor_v21_0_9_20260615

## Status
- task_id: `acute_rebound_retest_anchor_v21_0_9_20260615`
- type: `risk_patch`
- status: `complete`
- version: `v21.0.9`
- QA level: `L2`

## Owner Problem
Owner asked why a stock such as 旺宏 can be up strongly but still read like a weak rebound, and why the report does not plainly say: current state is a chase-risk zone, and buyability needs retest hold, non-limit-up chasing, volume confirmation, quality B+, and RR >= 1.5.

## User Visible Result
- `急彈待回測` cards now show a compact not-buy reason and buy-condition line.
- The card says the issue is `急彈追價區，尚未回測`, and lists live blockers such as weak volume, D quality, and current RR.
- The unlock line is explicit: `回測前高/突破區不破 + 非漲停追價 + 量能有效 + 品質B以上 + RR>=1.5`.
- RR is no longer hidden as `-（不可行動）` on acute rebound wait cards when a real RR exists.
- Limit-up / locked-overheat cards still hide RR as overheat and remain hard blocked.

## Non Goals
- No live Telegram delivery.
- No DB schema or production DB writes.
- No broker/order execution.
- No blanket permission to buy sharp rebound, limit-up, or near-limit-up stocks.
- No hard-code of 旺宏 or a single date.

## Impacted Modules And Consumers
- `presentation/report.py`
  - Consumer: Telegram unheld card reason / gap / unlock / data line.
- `core/generator.py`
  - Consumer: visible report version.
- `tests/test_generator_report.py`
  - Consumer: owner-style replay specimens and conflict guards.

## Output Contract
- For `急彈待回測`, the unheld card must remain a wait state.
- It must show:
  - `卡關主因：急彈未回測`
  - `量化差距：急彈追價區，尚未回測...`
  - `解鎖：回測前高/突破區不破 + 非漲停追價 + 量能有效 + 品質B以上 + RR>=1.5`
- If a real RR exists for acute rebound wait, the data line may show that RR while still saying the card is not actionable.
- For true limit-up / locked-overheat cards, existing `RR -（過熱）` hard blocker behavior must remain.

## Acceptance
- Focused owner specimen proves 旺宏-style +8% acute rebound is `等回測｜急彈待回測`, not weak rebound.
- Focused negative cases prove limit-up and low-volume limit-up still remain overheat / no-chase.
- Targeted report/state/evidence suites pass.
- Official dry-run generates `v21.0.9` with no live Telegram delivery and contains the new condition line.

## Failure Specimen And Route
- Owner failure: pasted report where 旺宏 near limit-up / sharp rebound still looked like weak rebound and did not say what conditions would make it buyable.
- Failure layer: official generator + Telegram formatter.
- Verification route:
  - `tests/test_generator_report.py::GeneratorReportTest::test_v21_0_9_strong_rebound_is_not_labeled_weak_rebound`
  - limit-up / low-volume limit-up regression tests
  - official `generate_report(dry_run=True)` message list.

## Forbidden / Blocking
- Do not change DB schema, RLS, grants, policies, roles, index, or constraints.
- Do not live-send Telegram.
- Do not loosen the trade state machine into buying acute rebounds without retest and confirmation.
- Do not remove existing overheat / limit-up hard blockers.



