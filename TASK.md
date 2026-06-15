# TASK: multi_window_strategy_v21_1_20260615

## Status
- task_id: `multi_window_strategy_v21_1_20260615`
- type: `risk_patch`
- status: `complete`
- version: `v21.1`
- QA level: `L2`

## Owner Problem
Owner asked whether V10 and 20D resistance are too narrow for buy decisions, and requested a completed v21.1 strategy treatment with evidence-backed logic rather than another dead rule or report-only patch.

## User Visible Result
- Acute rebound cards now show V10/V20, not only a single V value.
- Acute rebound cards now show the computed 20D breakout / retest zone.
- If current price is below the breakout zone, the card says the breakout zone is not reclaimed yet, instead of pretending it is already a pullback/retest.
- Version bumps to `v21.1`.

## Non Goals
- No live Telegram delivery.
- No DB schema, RLS, grant, policy, role, index, or constraint change.
- No broker/order execution.
- No hard-code of 旺宏 or a single date.
- No blanket permission to buy acute rebounds.

## Impacted Modules And Consumers
- `services/analysis.py`
  - Consumer: strategy result, volume state, RR / entry quality context.
- `core/generator.py`
  - Consumer: official Telegram report payload, dry-run artifact.
- `core/signal_snapshot.py`
  - Consumer: backfill / daily signal snapshot raw result.
- `presentation/report.py`
  - Consumer: Telegram unheld card.
- Tests:
  - `tests/test_analysis_engine.py`
  - `tests/test_generator_report.py`
  - existing report/state/backfill suites.

## Output Contract
- Strategy result / snapshot must expose:
  - `volume_ratio_10`
  - `volume_ratio_20`
  - `resistance_20`
  - `resistance_60`
  - `breakout_price_20`
  - `breakout_price_60`
  - `retest_zone_low`
  - `retest_zone_high`
- Acute rebound card must show:
  - V10/V20 combined volume context.
  - A concrete zone.
  - If price is below the zone: `突破區 X~Y（現價未站回）`.
  - Unlock: `先站回突破區 X~Y，再回測不破 + ...`.

## Acceptance
- Focused tests prove:
  - snapshot/raw_result exports V10/V20 and retest zone fields;
  - acute rebound card uses V10/V20 and concrete retest zone;
  - price below breakout zone is labeled as not reclaimed yet.
- Targeted strategy/report/backfill suites pass.
- Official dry-run generates `v21.1` and shows the new zone-aware 旺宏 card.

## Failure Specimen And Route
- Owner failure: report said `等回測` but did not say what it was waiting to retest, and V10/20D-only logic risked narrow strategy judgment.
- Failure layer: strategy metrics + official generator + Telegram formatter + snapshot.
- Verification route:
  - `tests/test_analysis_engine.py::AnalysisEngineTest::test_v21_1_snapshot_exports_multi_window_volume_and_retest_zone`
  - `tests/test_generator_report.py::GeneratorReportTest::test_v21_1_strong_rebound_uses_multi_window_retest_context`
  - `tests/test_generator_report.py::GeneratorReportTest::test_v21_1_retest_anchor_says_breakout_zone_when_price_is_below_zone`
  - official `generate_report(dry_run=True)` message list.

## Forbidden / Blocking
- Do not treat V20 or 60D resistance as display-only fake data.
- Do not loosen buyability without retest/volume/quality/RR gates.
- Do not hide source errors or missing data as valid strategy evidence.
