# TASK: entry_distance_strategy_v21_0_4_20260611

## Status
- task_id: `entry_distance_strategy_v21_0_4_20260611`
- type: `risk_patch`
- status: `complete`
- version: `v21.0.4`
- QA level: `L2`

## Owner Problem
Owner pointed out that the report used `距突破 ... 需<=4%` everywhere, making all unheld stocks look like the same breakout strategy and leaving no room for pullback or trend-continuation logic.

## User Visible Result
- Version bumps to `v21.0.4`.
- Breakout/pivot entries now use a strategy-specific buy zone of `<=5%`.
- Pullback reclaim and trend-continuation setups are no longer blocked by distance from breakout alone.
- Far distance without a valid setup still stays non-actionable, but the reason is "wait for setup / approach", not a universal buy rejection.
- Report wording no longer emits the old `突破策略需<=4%` text.

## Non Goals
- No live Telegram delivery.
- No DB schema/RLS/grant/policy/role/index/constraint change.
- No production DB writes or backfill.
- No broker/order execution.

## Impacted Modules And Consumers
- `core/generator.py`
  - Consumer: official report generator and unheld funnel classification.
- `core/trade_state_machine.py`
  - Consumer: unheld trade state artifact and guard logic.
- `presentation/report.py`
  - Consumer: Telegram card gap/trigger wording.
- `tests/test_generator_report.py`
- `tests/test_trade_state_machine.py`
- `tests/test_market_theme_evidence.py`

## Output Contract
- Pivot/breakout buy-zone wording: `突破買點區需<=5%`.
- `<=4%` is not used as a universal display or action gate.
- `TOO_FAR_FROM_TRIGGER` only applies to breakout/pre-breakout/base-reversal distance policy.
- Pullback reclaim and trend continuation may be evaluated by their own setup rules even when breakout distance is above 5%.
- Structural rejection/source failure cards must not show a conflicting `交易狀態：等資料` line.

## Research Basis
- IBD/CANSLIM style buy-zone research treats 5% above a pivot as the breakout buy zone, not as a universal rule for every entry type.
- Breakout guidance distinguishes breakout entry, confirmation, retest/pullback, stop placement, and trend continuation.
- Pullback/retest strategies can enter after old resistance becomes support; they are not the same as chasing the original pivot.

## Acceptance
- Official dry-run generates `v21.0.4`.
- Dry-run does not contain old `需<=4%` / `突破策略需<=4%`.
- Dry-run does not contain old `今日盤中交易執行`.
- Related tests pass.
- Regression tests prove:
  - far breakout setup gets `TOO_FAR_FROM_TRIGGER`;
  - far pullback/trend-continuation setup does not get blocked by breakout distance alone.

## Failure Specimen And Route
- Owner failure: "距離突破怎麼都是<=4沒有策略可言".
- Failure layer: official generator + trade state machine + Telegram formatter.
- Verification route:
  - `tests/test_generator_report.py`
  - `tests/test_trade_state_machine.py`
  - `tests/test_market_theme_evidence.py`
  - official `generate_report(dry_run=True)` message list.

## Forbidden / Blocking
- Do not send live Telegram.
- Do not turn far distance into a buy signal by itself.
- Do not use local cache as cross-day strategy memory.
