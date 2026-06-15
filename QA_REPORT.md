# QA_REPORT: unheld_readability_v21_1_20260615

## Test Scope

- Unheld blocker wording and ordering.
- Mobile misread risk for non-actionable cards.
- Official generator message-list replay.
- Regression coverage for RR不足, heat, retest, quality/setup, source-error, sample-error, and prepare states.

## Risk Scan

- `可買條件` could be mistaken as a current buy signal if paired with buy-like wording.
- Removing diagnostics could hide why a stock is blocked.
- Helper-level formatting could pass while official report still contains old labels.

## Cross-Block Semantic Consistency

- Summary still says `新增有效進場：無`.
- Unheld cards still say `買點：不買...` or `不可買...`.
- `不能買` explains the current blocker.
- `可買條件` explains future unlock criteria only.
- Theoretical RR remains `理論RR ...僅參考`.

## User Misread Risk

- Reduced: cards no longer lead with internal diagnostic labels.
- Reduced: long pipes are converted into semicolon clauses.
- Checked: non-actionable cards do not contain `可立即買` or `建議買入`.

## Failure Specimen Countercheck

- Owner 06/15 v21.1 unheld sample was replayed through official dry-run.
- `旺宏` now reads:
  - cannot buy because sharp rebound has not retested;
  - missing retest / breakout-zone reclaim / volume / quality;
  - buyable only after reclaim + retest hold + non-chase + volume + quality + RR.
- Weak setup names now show high RR as theoretical reference, not buy evidence.

## Evidence

- `205 passed, 147 warnings, 44 subtests passed`.
- Official dry-run printed the unheld message with the new three-line blocker structure.
- No live Telegram delivery.

## Not Tested

- Live Telegram delivery.
- Scheduled Render/GitHub runner artifact after push.
- Production DB writes, because this task is display-only.

## QA Conclusion

通過

Reason: formatter, official generator, and Owner-style dry-run evidence all cover the visible readability problem without strategy or DB changes.
