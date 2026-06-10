# QA_REPORT: future_watch_fundamental_layout_20260610

## Scope
- Future-watch fundamentals block layout.
- Removal of `關注原因` from the fundamentals block only.

## Risk Scan
- Removing `關注原因` too broadly could affect MOPS event rows.
- Splitting labels could drop EPS or revenue.
- Formatter could still pass tests but fail official report path.

## Semantic Consistency
- MOPS events can still show their own `關注原因`.
- Fundamentals block no longer shows `關注原因`.
- EPS and revenue values are unchanged; only line layout changed.

## Failure Specimen Countercheck
- Owner requested:
  ```text
  3481 群創
  EPS 2026Q1 0.2
  營收 2026/05 +10.3%
  ```
- Official dry-run produced the requested format for `3481 群創` and the rest of the fundamentals block.

## Additional Challenge
- Ran full generator report tests after targeted formatter tests.

## Not Tested
- Live Telegram delivery.
- DB writes/backfill.

## QA Conclusion
通過
