# QA_REPORT: report_state_denoise_followup_20260610

## Scope
- Official Telegram report route for v21.0.1 unheld state wording.
- State-machine visible label consistency.
- Future-watch low-similarity historical analogy wording.
- Fundamentals block spacing.

## Risk Scan
- `等接近` could accidentally be counted as actionable.
- Market weakness could hide the stock-specific blocker again.
- Distance wording could still imply all strategies are blocked by 4%.
- Historical analogy could overstate a 51% match.
- Formatter-only tests could pass while official generator output stays wrong.

## Semantic Consistency
- `等接近` remains non-actionable and counted under `僅追蹤`.
- Card title, state line, `買點`, `卡關主因`, `解鎖`, `明日觸發`, and summary bucket align on the same route.
- Market weakness is visible but no longer replaces the primary distance/setup gate.
- Low-similarity TWSE history is explicitly not a main conclusion.

## Failure Specimen Countercheck
- Owner pasted an official v21.0.1 report where unheld cards were noisy and the state machine looked unhelpful.
- Official dry-run now shows:
  - `【緯創 3231】⏳ 等接近｜市場弱`
  - `交易狀態：等接近｜動作：等待｜主因：市場弱｜還差：市場轉強 + 接近觸發`
  - `買點：不買，等接近觸發區`
  - `未持倉 7｜僅追蹤 7（等接近）`
  - `歷史類比：低相似，不作主結論｜source=TWSE`

## Additional Challenge
- Ran generator/state-machine tests plus separate analysis/evidence/volume/theme tests.
- Official dry-run checked final message route instead of helper-only fixture.

## Not Tested
- Live Telegram delivery.
- DB writes/backfill.
- GitHub Actions live run.

## QA Conclusion
通過
