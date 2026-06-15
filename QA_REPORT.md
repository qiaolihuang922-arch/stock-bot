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
- Over-scoping could remove `距突破`, which Owner explicitly wanted to keep.
- Under-scoping could keep dumping volume/quality/RR into every waiting card.

## Cross-Block Semantic Consistency

- `交易狀態` remains the state-machine line; no extra `狀態` hard-concat row is emitted.
- Non-actionable entry details are split into short `進場` / `缺口` / `可買` rows.
- `距突破` remains a separate line for every unheld card.
- Normal waiting/rejected cards no longer show a generic `數據：...` metric dump.
- State-specific cards expose only the relevant blocker family:
  - retest: retest / breakout zone;
  - cooling: heat level;
  - risk-reward: risk-reward gap;
  - setup: setup / quality;
  - rejected: repair requirement.
- Summary/funnel counts are not changed.
- Holding cards are not changed.

## User Misread Risk

- Reduced: users no longer read separate `拆解`, `買點`, `不能買`, and `還差` rows that repeat each other.
- Reduced: users no longer get one wall-like `狀態` / `進場檢查` row on mobile.
- Preserved: users can still see the blocker and exact unlock condition in the same card.
- Remaining: rejected-card `原因` lines may still need future cleanup if they repeat source/status details.

## Failure Specimen Countercheck

- Owner sample: 06/16 pre-market unheld report.
- Countercheck via dry-run:
  - cards now show `進場：...｜原因：...`;
  - cards now show `缺口：...`;
  - cards now show `可買：...`;
  - cards still show `距突破：...`;
  - normal unheld cards show `data_lines=0`;
  - cards no longer show standalone `拆解`, `買點`, `不能買`, `還差`, or hard-concat `進場檢查`.

## Evidence

- Test command:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py tests\test_unheld_gap_format.py -q --tb=short`
  - result: `205 passed, 44 subtests passed`
- Dry-run:
  - `generate_report(dry_run=True)`
  - result checked locally:
    - `data_lines=0`;
    - `distance_lines=8`;
    - 旺宏 card shows only retest-zone blocker details, not the full metric package.
  - no live Telegram delivery.

## Not Tested

- Live Telegram delivery.
- Full production scheduled run after push.

## QA Conclusion

通過

Reason: the official generator path now renders readable short mobile lines and focused regression tests prevent both the old split-row pattern and the wall-like hard-concat pattern from returning.
