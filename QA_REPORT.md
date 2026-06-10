# QA_REPORT: latest_revenue_month_fallback_20260610

## Scope
- Latest available MOPS monthly revenue search.
- Normalized revenue row merge.
- Official generator dry-run.

## Risk Scan
- A fixed expected month would require monthly code changes.
- If the latest theoretical month is not published yet, the report could incorrectly drop usable prior-month revenue.
- Mojibake-prone source keys can make tests pass in one encoding and fail in another.

## Semantic Consistency
- The search starts from the latest plausible completed month and walks backward.
- The first official MOPS row wins.
- Missing rows remain missing; the system does not invent monthly revenue.
- Normalized keys make internal tests/adapters stable while preserving legacy source-key handling.

## Failure Specimen Countercheck
- Simulated 2026-07-10:
  - MOPS `11506` returns no row.
  - MOPS `11505` returns official revenue.
  - Report shows 2026/05 revenue and does not require code changes.

## Additional Challenge
- Ran full generator report tests and trade state-machine tests after the collector change.
- Ran official `generate_report(dry_run=True)` to verify the final message-list route still works without live Telegram delivery.

## Not Tested
- Live Telegram delivery was not run.
- Production DB writes were not run or changed.

## QA Conclusion
通過
