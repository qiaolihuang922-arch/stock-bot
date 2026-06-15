# QA_REPORT: multi_window_strategy_v21_1_20260615

## Test Scope
- V10/V20 strategy metrics.
- 20D/60D resistance and breakout price fields.
- Retest-zone payload and Telegram rendering.
- Acute rebound no-chase wording.
- Backfill / daily snapshot compatibility.

## Risk Scan
- If V20 is only shown in Telegram, it becomes fake display evidence.
- If 60D resistance hard-blocks all setups, short-term valid breakouts may disappear.
- If price is below the breakout zone, calling it a retest zone is misleading.
- If result fields are not included in snapshot/raw_result, DB/replay evidence can diverge from live report.

## Semantic Consistency
- V10 remains the short-term volume lens.
- V20 adds swing-volume confirmation and is used in volume state.
- 20D resistance remains the fast breakout anchor.
- 60D resistance is carried as higher-timeframe context.
- Acute rebound remains wait/no-chase.
- Below-zone acute rebound says `現價未站回`, then waits for reclaim and retest.

## Failure Specimen Countercheck
- Official dry-run produced `v21.1`.
- 旺宏 card showed:
  - `突破區 175.5~176.38（現價未站回）`
  - `V10 0.52x / V20 0.26x偏弱`
  - `先站回突破區 175.5~176.38，再回測不破`
- This resolves the previous ambiguity: `等回測` is no longer a vague phrase.

## Additional Challenge
- Focused test proves raw snapshot exports V10/V20 and retest-zone fields.
- Focused test proves price below zone does not render as `區間不破`.
- Existing limit-up / overheat blockers remain covered in the report suite.

## Not Tested
- Live Telegram delivery.
- Production DB schema write.
- Broker/order execution.

## QA Conclusion
通過

Evidence:
- `3 passed` focused v21.1 specimens.
- `307 passed, 149 warnings, 57 subtests passed` targeted strategy/report/backfill suite.
- Official dry-run generated `v21.1` with no live Telegram delivery.
