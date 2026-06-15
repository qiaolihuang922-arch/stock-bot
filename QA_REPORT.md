# QA_REPORT: acute_rebound_retest_anchor_v21_0_9_20260615

## Test Scope
- Acute rebound unheld card wording.
- Buy-condition checklist visibility.
- RR display conflict on wait cards.
- Limit-up / overheat no-chase regressions.
- Official generator dry-run output.

## Risk Scan
- Showing RR on a wait card could be misread as a buy signal.
- Hiding RR as `-（不可行動）` while another line says `RR 達標` creates a visible contradiction.
- Loosening all `等回測` RR display would regress limit-up / overheat hard blockers.
- Adding too many lines would worsen mobile noise.

## Semantic Consistency
- Acute rebound:
  - title remains `等回測｜急彈待回測`;
  - action remains wait;
  - reason says it is a chase-risk zone and has not retested;
  - unlock says what must happen before buyability can be reconsidered.
- Limit-up / overheat:
  - remains no-chase;
  - RR remains hidden as overheat where existing contracts require it.

## Failure Specimen Countercheck
- Owner wanted:
  - current state: cannot buy because it is acute rebound / chase zone;
  - buy conditions: retest hold, non-limit-up chasing, valid volume, B+ quality, RR >= 1.5.
- Countercheck from official dry-run:
  - 旺宏 card contains `量化差距：急彈追價區，尚未回測｜V 0.5x偏弱｜品質 D 未達B｜RR 2.21達標`.
  - 旺宏 card contains `解鎖：回測前高/突破區不破 + 非漲停追價 + 量能有效 + 品質B以上 + RR>=1.5`.
  - 旺宏 card remains `買點：不買，等回測`.
  - 旺宏 card data line shows `RR 2.21` without turning the card into buyable.

## Additional Challenge
- Focused limit-up hard-blocker tests still pass:
  - confirmed limit-lock chase remains overheat-blocked;
  - low-volume limit-up remains overheat-blocked.
- Full targeted suite passed after narrowing RR display to acute rebound only.

## Not Tested
- Live Telegram delivery.
- Production DB write/backfill.
- Broker/order execution.

## QA Conclusion
通過

Evidence:
- `3 passed` focused acute/limit-up specimens.
- `249 passed, 149 warnings, 57 subtests passed` targeted report/state/evidence suite.
- Official dry-run generated `v21.0.9` and showed the new 旺宏 retest-anchor condition line with no live Telegram delivery.


