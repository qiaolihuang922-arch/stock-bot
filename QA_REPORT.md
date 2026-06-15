# QA_REPORT: report_conflict_entry_gate_v21_0_5_20260615

## Test Scope
- Owner pasted `06/15 盤中｜v21.0.4` conflict class.
- Unheld entry blocker wording and state-machine states.
- Broad market gate versus individual stock gate.
- False data-source gate on dry-run / report-only paths.
- Official generator message list.

## Risk Scan
- `市場：中性觀察 R2` must not coexist with every unheld stock blocked by `等市場｜市場弱`.
- Missing source context in a dry-run must not create fake `等資料`.
- A stock may be blocked by heat, RR, setup, or individual weakness without calling it market-wide weakness.
- No card should expose internal English noise such as `entry quality low`.
- No change should create a valid buy when the underlying score remains non-actionable.

## Semantic Consistency
- Market gate: only true weak/bear market states block as `市場弱`.
- Stock gate: low individual grade blocks as `個股弱勢`.
- Heat gate: limit-up / overheated moves stay non-chase and wait for cooldown or retest.
- Volume gate: used as confirmation for breakout/setup quality, not a universal buy ban.
- RR gate: weak reward/risk waits for repair and is not mislabeled as source failure.

## Failure Specimen Countercheck
- Official dry-run after the patch produced `v21.0.5`.
- Counterchecks:
  - `has_R2_market_weak_conflict False`
  - `has_nextday_data_conflict False`
  - `has_english_quality_noise False`
  - `has_buyable False`
  - `liandian_rr True`

## Additional Challenge
- QA checked the final official generator path, not only helper fixtures.
- The current dry-run remains conservative: no valid new entry is emitted.
- The fix changes labels and gates, not hidden data or fake market evidence.

## Not Tested
- Live Telegram delivery.
- Production DB write/backfill.
- Broker/order execution.

## QA Conclusion
通過

Evidence:
- `246 passed, 145 warnings, 57 subtests passed`.
- Official dry-run conflict probe passed with no live Telegram delivery.
