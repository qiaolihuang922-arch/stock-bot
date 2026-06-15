# TASK: premarket_phase_report_v21_0_6_20260615

## Status
- task_id: `premarket_phase_report_v21_0_6_20260615`
- type: `normal_patch`
- status: `complete`
- version: `v21.0.6`
- QA level: `L2`

## Owner Problem
Owner pasted a `06/15 非交易｜v21.0.5` report that still contained today buy records, today trade wording, live price changes, and tomorrow-plan wording. The visible conflict is that a trading-day report before market open was labeled as non-trading and then mixed today/tomorrow semantics.

## User Visible Result
- Trading weekdays before 09:00 are labeled `盤前`, not `非交易`.
- `盤前` report summaries use today-action semantics.
- `盤前` reports do not append `明日計畫`.
- Existing `盤中` wording remains unchanged.
- Version bumps to `v21.0.6`.

## Non Goals
- No live Telegram delivery.
- No DB schema or production DB writes.
- No strategy threshold change.
- No broker/order execution.

## Impacted Modules And Consumers
- `core/generator.py`
  - Consumer: report phase, official generator, Telegram header, summary helpers.
- `presentation/report.py`
  - Consumer: Telegram summary and unheld card trigger labels.
- `tests/test_generator_report.py`
- `tests/test_trade_state_machine.py`
- `tests/test_market_theme_evidence.py`

## Output Contract
- Weekday before open: header must use `盤前`, not `非交易`.
- `盤前` is a today-action phase, like `盤中` for summary routing.
- `盤前` trigger label is `盤前觀察`.
- `盤中` keeps `今日盤中風控建議`.
- `盤後` / `收盤` keep tomorrow/open-confirmation semantics.

## Acceptance
- Unit test proves 2026-06-15 08:00 resolves to `盤前`.
- Report summary test proves `盤前` header has no `非交易` and no `明日計畫`.
- Existing targeted report suites pass.

## Failure Specimen And Route
- Owner failure: pasted `06/15 非交易｜v21.0.5` report.
- Failure layer: `get_market_phase()` + Telegram summary formatter.
- Verification route:
  - `tests/test_generator_report.py`
  - `tests/test_trade_state_machine.py`
  - `tests/test_market_theme_evidence.py`
  - official `generate_report(dry_run=True)` with patched 2026-06-15 08:00 time.

## Forbidden / Blocking
- Do not treat a trading-day pre-open report as holiday/non-trading.
- Do not change `盤中` wording while fixing `盤前`.
- Do not live-send Telegram.
