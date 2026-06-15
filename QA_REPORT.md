# QA_REPORT: strong_rebound_not_weak_v21_0_7_20260615

## Test Scope
- Strong intraday rebound display semantics.
- Weak rebound regression path.
- Unheld funnel state.
- Trade state machine visible reason.
- Telegram unheld card gap/unlock text.
- Official dry-run path.

## Risk Scan
- If every `WEAK_REBOUND` is upgraded, true weak rebounds stop being filtered.
- If strong rebound becomes buyable, the system starts chasing near-limit-up moves.
- If only the title changes, card reason could still say weak rebound and confuse Owner.
- If trade-state guards are not updated, the line can still say `主因：個股弱勢`.

## Semantic Consistency
- Low-change weak rebound: reject as weak / structure not repaired.
- High-change weak rebound: acknowledge strength as `急彈待回測`.
- Action remains wait/retest: no buy, no chase.
- Retest confirmation remains the next condition.

## Failure Specimen Countercheck
- Owner failure: 旺宏 near limit-up labeled `弱反彈待確認`.
- Countercheck:
  - +8.19% synthetic 旺宏-style case becomes `等回測｜急彈待回測`.
  - card says `卡關主因：急彈未回測`.
  - card says `買點：不買，等回測`.
  - card does not include `弱反彈待確認`.
  - summary does not list it as `淘汰｜弱反彈待確認`.

## Additional Challenge
- Original low-change weak rebound test still passes and remains rejected as weak.
- Full targeted suite confirms existing overheat / limit-up / weak-rebound contracts did not regress.

## Not Tested
- Live Telegram delivery.
- Production DB write/backfill.
- Broker/order execution.

## QA Conclusion
通過

Evidence:
- `2 passed` focused strong/weak rebound tests.
- `249 passed, 149 warnings, 57 subtests passed` targeted report/state/evidence suite.
- Official dry-run generated `v21.0.7` with no live Telegram delivery.
