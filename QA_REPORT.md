# QA_REPORT: rr_wording_readability_v21_1_20260615

## Test Scope

- User-visible risk/reward terminology in unheld cards.
- Summary funnel display label for `等RR修復`.
- Official generator message-list replay.
- Regression coverage for existing unheld readability paths.

## Risk Scan

- Replacing `RR` too shallowly could leave old shorthand in summary or data lines.
- Replacing it too broadly could change internal state compatibility.
- Potential reward could be misread as buy evidence if `買點未成立` is removed.

## Cross-Block Semantic Consistency

- Summary still says `新增有效進場：無`.
- Unheld cards still say `買點：不買...` or `不可買...`.
- `等風險報酬` in the title matches `風險報酬修復` in the card body and summary funnel.
- `潛在報酬：好（x倍），買點未成立` keeps the value direction clear while remaining non-actionable.

## User Misread Risk

- Reduced: `RR` no longer appears as unexplained shorthand in the checked unheld report and summary.
- Reduced: `等RR修復` is no longer exposed as a state label.
- Checked: wording still does not imply current buy when the card is non-actionable.

## Failure Specimen Countercheck

- Owner 06/15 v21.1 sample was replayed through official dry-run.
- `聯電` now reads `等風險報酬` and `不能買：風險報酬還不夠`.
- Weak setup cards now show `潛在報酬：好（x倍），買點未成立`.

## Evidence

- `205 passed, 147 warnings, 44 subtests passed`.
- Official dry-run printed the updated unheld message and summary.
- No live Telegram delivery.

## Not Tested

- Live Telegram delivery.
- Scheduled Render/GitHub runner artifact after push.
- Production DB writes, because this task is display-only.

## QA Conclusion

通過

Reason: formatter, official generator, and Owner-style dry-run evidence cover the visible terminology problem without strategy or DB changes.
