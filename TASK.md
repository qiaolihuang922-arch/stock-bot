# TASK: report_noise_conflict_v21_0_3_20260611

## Status
- task_id: `report_noise_conflict_v21_0_3_20260611`
- type: `normal_patch`
- status: `complete`
- version: `v21.0.3`
- QA level: `L2`

## Owner Problem
Owner pasted the `06/11` intraday Telegram report and asked to analyze and fix visible conflicts/noise. Main issues:
- Summary used `今日盤中交易執行`, which can be misread as actual executed orders.
- Stop-loss cards repeated low-value `條件` / `數據：不適用` lines.
- Unheld card could show `淘汰` while the trade state said `等資料`.
- Historical analogy showed `量能 0` without explaining reliability limits.

## User Visible Result
- Visible report version bumps to `v21.0.3`.
- Intraday summary and detail index use `風控建議`, not `交易執行`.
- Direct risk cards (`停損` / `減碼` / `停利`) keep decision, reason, next step, price, and suppress low-signal condition/data lines.
- Data-source-wait cards only show `等資料` when the state machine itself says data recovery is the blocker; normal wait states remain `等接近` / `等回測` / `等量能`.
- Historical analogy now states when confidence is medium because volume is unavailable and the match is based mainly on price/position.

## Non Goals
- No live Telegram delivery.
- No DB schema/RLS/grant/policy/role/index/constraint change.
- No production DB writes or backfill.
- No strategy core rewrite in this patch.

## Impacted Modules And Consumers
- `core/generator.py`
  - Consumer: official report generator, Telegram message list, report integrity probe.
- `presentation/report.py`
  - Consumer: Telegram card formatter and summary formatter.
- `core/future_watch.py`
  - Consumer: future-watch fourth Telegram message.
- `tests/test_generator_report.py`
- `tests/test_trade_state_machine.py`
- `tests/test_market_theme_evidence.py`

## Output Contract
- Header version: `v21.0.3`.
- Intraday execution heading: `今日盤中風控建議`.
- Intraday detail index count: `風控建議 N`.
- Non-execution text: `不列入今日盤中風控建議`.
- No old `✅ 今日盤中交易執行` wording.
- Stop-loss / reduce / profit direct action cards do not render the old low-signal `條件：...` or `數據：不適用...` lines.
- Source/data wait state must not conflict with title/funnel wording.

## Acceptance
- Official dry-run generates `v21.0.3`.
- Dry-run contains `今日盤中風控建議`.
- Dry-run does not contain `今日盤中交易執行` or `✅ 今日盤中交易執行`.
- Stop-loss cards are shorter and still keep `決策` / `原因` / `下一步` / `價格`.
- Historical analogy includes `可信度中等：本次以價格/位置為主` when volume is missing.
- Related report/state/evidence tests pass.

## Failure Specimen And Route
- Owner failure specimen: full `06/11 盤中 v21.0.2` report pasted in chat.
- Failure layer: official generator + Telegram formatter + future-watch formatter.
- Verification route:
  - `tests/test_generator_report.py`
  - `tests/test_trade_state_machine.py`
  - `tests/test_market_theme_evidence.py`
  - official `generate_report(dry_run=True)` message list.

## Forbidden / Blocking
- Do not send live Telegram.
- Do not hide source/data failures by making them look actionable.
- Do not turn every strategy-source-missing case into `等資料`; only do so when the state machine already classifies the card as data recovery.
