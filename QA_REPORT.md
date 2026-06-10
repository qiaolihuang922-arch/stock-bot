# QA_REPORT: revenue_fallback_no_downgrade_20260610

## Scope
- MOPS monthly revenue fallback.
- Revenue month downgrade prevention.
- Revenue YoY extraction.
- Official generator dry-run.

## Risk Scan
- Latest-month fallback can accidentally overwrite a newer official row with an older row.
- Parser fallback can confuse monthly revenue amount with YoY percentage.
- Over-aggressive fallback can show too-old months and mislead the user.

## Semantic Consistency
- A newer month may replace an older month.
- An older month may not replace a newer month.
- Latest month and one-month fallback are acceptable; older rows are omitted.
- Missing official data remains missing rather than being fabricated.

## Failure Specimen Countercheck
- Owner specimen showed:
  - older fallback months like 2026/03 and 2026/02,
  - impossible percentages such as using revenue amount as YoY.
- Official dry-run now reports `bad_large_pct False` and `too_old False`.

## Additional Challenge
- Added negative tests for downgrade, amount-as-YoY, and too-old fallback.
- Ran the full generator/state-machine suite.

## Not Tested
- Live Telegram delivery was not run.
- Production DB writes were not run or changed.

## QA Conclusion
通過
