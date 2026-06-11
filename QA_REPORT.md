# QA_REPORT: entry_distance_strategy_v21_0_4_20260611

## Scope
- Breakout-distance strategy policy.
- Unheld state machine guard behavior.
- Telegram card distance wording.
- Official dry-run message list.

## Risk Scan
- Raising `<=4%` to `<=5%` without setup separation would still be a fake fix.
- Removing distance gates entirely would allow chasing far non-setup stocks.
- Pullback/trend continuation must not be blocked by pivot distance alone.
- Rejected/source-failed cards must not show contradictory `淘汰` + `等資料` main lines.

## Semantic Consistency
- Breakout buy zone: distance gate.
- Pullback reclaim: setup confirmation gate, not pivot-distance gate.
- Trend continuation: small-size continuation gate, not pivot-distance gate.
- No valid setup: wait for setup/approach, not buy.

## Failure Specimen Countercheck
- Owner said all reports used `<=4` and had no strategy.
- Countercheck:
  - formatter now emits `突破買點區需<=5%`;
  - old `突破策略需<=4%` is absent in dry-run;
  - state-machine tests prove far breakout is blocked but far pullback/trend continuation are not blocked by distance alone.

## Additional Challenge
- Dry-run also checked that old `今日盤中交易執行` wording remains absent and rejected/source-failed unheld cards do not show the old `淘汰` + `交易狀態：等資料` conflict.

## Not Tested
- Live Telegram delivery.
- Production DB writes/backfill.
- Live broker/order execution.

## QA Conclusion
通過

Evidence:
- `246 passed, 145 warnings, 57 subtests passed`.
- Official dry-run checks passed with no live Telegram delivery.
