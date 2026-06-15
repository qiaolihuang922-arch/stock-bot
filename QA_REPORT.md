# QA_REPORT: unheld_card_mobile_denoise_20260616

## Test Scope

- Telegram unheld-card presentation.
- Rebound/retest failure specimen.
- Non-actionable blocker preservation.
- Existing unheld gap helper behavior.

## Risk Scan

- Compacting rows could hide why a stock cannot be bought.
- Compacting rows could accidentally make waiting/淘汰 cards look actionable.
- Existing tests might pass while mobile output still repeats standalone rows.

## Cross-Block Semantic Consistency

- `狀態` line combines strategy-axis state and market-line state.
- `進場檢查` line combines buy line, blocker, gap, and unlock.
- Summary/funnel counts are not changed.
- Holding cards are not changed.

## User Misread Risk

- Reduced: users no longer read separate `拆解`, `買點`, `不能買`, and `還差` rows that repeat each other.
- Preserved: users can still see the blocker and exact unlock condition in the same card.
- Remaining: rejected-card `原因` lines may still need future cleanup if they repeat source/status details.

## Failure Specimen Countercheck

- Owner sample: 06/16 pre-market unheld report.
- Countercheck via dry-run:
  - cards now show `狀態：...`;
  - cards now show `進場檢查：買點：...｜不能買：...｜還差：...｜可買條件：...`.

## Evidence

- Test command:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py tests\test_unheld_gap_format.py -q --tb=short`
  - result: `205 passed, 44 subtests passed`
- Dry-run:
  - `generate_report(dry_run=True)`
  - result checked locally, no live Telegram delivery.

## Not Tested

- Live Telegram delivery.
- Full production scheduled run after push.

## QA Conclusion

通過

Reason: the official generator path now renders merged mobile lines and focused regression tests prevent the old split-row pattern from returning.
