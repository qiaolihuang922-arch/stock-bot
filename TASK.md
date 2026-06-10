# TASK: future_watch_source_and_card_denoise_20260610

## Status
- task_id: `future_watch_source_and_card_denoise_20260610`
- type: `normal_patch`
- status: `complete`
- version: `v21.0.2`
- QA level: `L2`

## Owner Problem
Owner pasted the v21.0.1 official report and asked for analysis. The visible problems were:

- `歷史類比` sometimes fell to `source-error` and misleadingly looked like no high-similarity sample, rather than a source failure.
- Some listed-stock fundamentals had EPS but no revenue.
- Unheld `等接近` cards still repeated low-value diagnostic lines, making the report noisy on mobile.

## User Visible Result
- Report version is bumped to `v21.0.2`.
- TWSE historical source gets a same-run retry before fail-closed.
- Historical source failure now says TWSE official source is temporarily unreadable, not false no-similarity.
- TWSE listed monthly revenue OpenAPI is included in fundamentals loading, so listed stocks no longer rely only on MOPS refresh for revenue.
- Compact non-actionable wait cards hide low-signal `盤面：證據不足`, RR data rows, and RR/backtest basis lines.

## Non Goals
- No live Telegram delivery.
- No DB write, schema, RLS, grant, policy, role, index, or constraint change.
- No fabricated revenue/EPS/historical analogy.
- No change from watchlist to buyable signal.

## Impacted Modules And Consumers
- `core/future_watch.py`: TWSE retry, source-error wording, TWSE revenue endpoint.
- `presentation/report.py`: compact wait-card denoise.
- `core/generator.py`: visible report version.
- `tests/test_generator_report.py`, `tests/test_trade_state_machine.py`, `tests/test_market_theme_evidence.py`: regression and version expectations.
- Direct consumers: official `generate_report(dry_run=True)` and runner-generated Telegram text.

## Output Contract
- Historical source available: keep normal low-similarity / analogy wording.
- Historical source error: `歷史類比：TWSE 官方來源暫時不可讀，本次不列未確認類比｜source=TWSE source-error`.
- Fundamentals include TWSE and TPEX monthly revenue OpenAPI rows, plus existing MOPS refresh.
- Compact unheld wait card keeps title, state, buy line, blocker/gap/unlock, tomorrow trigger, and price.

## Acceptance
- Official dry-run returns 4 messages with `v21.0.2`.
- Official dry-run future-watch shows 2303 and 2301 with 2026/05 revenue when sources are available.
- Official dry-run first unheld `等接近` card is visibly shorter and still non-actionable.
- Generator/state-machine and adjacent strategy/source tests pass.

## Failure Specimen And Route
- Owner specimen: pasted v21.0.1 official report.
- Failure layer: official generator and future-watch source loading.
- Replay route: `generate_report(dry_run=True)` plus source unit tests.

## Forbidden / Blocking
- Do not send live Telegram.
- Do not write production DB.
- Do not convert fail-closed source errors into invented data.
