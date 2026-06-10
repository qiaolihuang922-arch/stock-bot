# TASK: report_state_denoise_followup_20260610

## Status
- task_id: `report_state_denoise_followup_20260610`
- type: `risk_patch`
- status: `complete`
- version: `v21.0.1`
- QA level: `L2`

## Owner Problem
Owner pasted the official v21.0.1 report and asked to analyze/fix the remaining problems:

- Unheld cards all collapsed into `等型態` / market wording, making the v21 state machine look useless.
- Distance wording looked like `>4%` always means never buy, even though trend continuation or pullback setups can still become valid later.
- Card lines conflicted: state/title could say one blocker while `買點` said another.
- Historical analogy looked overconfident at low similarity.
- Future-watch fundamentals needed readable per-stock spacing.

## User Visible Result
- Far unheld names now enter `等接近` instead of generic `等型態`.
- Unheld state line can show market weakness as background plus the next stock-specific gate.
- `買點`, title, state, gap, unlock, and summary bucket use the same `等接近` route.
- Distance text says the 4% limit is for breakout strategy; trend-continuation/pullback setups require separate valid setup evidence.
- TWSE historical analogy below 60% is downgraded to `低相似，不作主結論`.
- Fundamentals block leaves a blank line between stocks.

## Non Goals
- No live Telegram delivery.
- No DB write, schema, RLS, grant, policy, role, index, or constraint change.
- No fabricated EPS, revenue, OHLCV, or cross-day memory.
- No change from non-actionable watchlist to buyable recommendation.

## Impacted Modules And Consumers
- `core/trade_state_machine.py`: visible unheld state labels and transition event for `WAIT_APPROACH`.
- `core/generator.py`: unheld funnel state/bucket/summary trigger routing.
- `presentation/report.py`: Telegram card wording and gap attribution.
- `core/future_watch.py`: historical analogy confidence wording and fundamentals spacing.
- `tests/test_generator_report.py`, `tests/test_trade_state_machine.py`: official report and state-machine regression coverage.
- Direct consumers: official `generate_report(dry_run=True)`, GitHub runner generated Telegram message artifact.

## Output Contract
- For far unheld targets with no valid setup:
  - title: `等接近`
  - state line includes `交易狀態：等接近`
  - `買點：不買，等接近觸發區`
  - summary bucket: `未持倉 ...（等接近）`
- If market is weak but stock-specific distance/setup gate is primary, market appears as background, not a replacement for the stock gate.
- Historical analogy with similarity `<60%` must not render as a main market conclusion.
- Fundamentals rows keep:
  - `code name`
  - `EPS ...`
  - `營收 ...`
  - blank line before the next stock.

## Acceptance
- Official dry-run returns 4 messages and no live delivery.
- Official dry-run unheld card contains `等接近`, aligned `買點`, and no `等型態` fallback for the pasted specimen route.
- Official dry-run future-watch block shows low-similarity historical analogy as non-main conclusion.
- Generator/state-machine tests and strategy/volume/evidence tests pass.

## Failure Specimen And Route
- Owner specimen: pasted v21.0.1 official Telegram report.
- Failure layer: official generator/report formatter, not helper-only fixture.
- Replay route: `generate_report(dry_run=True)` plus generator/state-machine tests.

## Forbidden / Blocking
- Do not send live Telegram.
- Do not directly write production DB.
- Do not mark the task complete without git commit/push and completion evidence.
