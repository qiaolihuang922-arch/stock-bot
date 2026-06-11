# QA_REPORT: report_noise_conflict_v21_0_3_20260611

## Scope
- Telegram visible wording for intraday report.
- Holding direct-risk card denoise.
- Unheld title/state/funnel consistency.
- Historical analogy reliability wording.
- Version synchronization to `v21.0.3`.

## Risk Scan
- Rewording `交易執行` could break integrity checks or detail index tests.
- Hiding low-signal lines could accidentally remove required stop-loss reason/next-step lines.
- Treating source issues as `等資料` too broadly could swallow valid wait states like `等回測`, `等量能`, or `隔日確認`.
- Future-watch date filtering must not reintroduce past single-day events as future events.

## Semantic Consistency
- Intraday summary now says `風控建議`, matching the fact that no live broker/TG execution is performed.
- Stop-loss cards still show the actionable decision and reason, but not repetitive condition/data filler.
- `等資料` appears only when the state machine says data recovery is the blocker.
- Missing volume in historical analogy is explicitly called out as a confidence limitation.

## Failure Specimen Countercheck
- Owner specimen conflict: `今日盤中交易執行` sounded like execution.
  - Countercheck: dry-run has `今日盤中風控建議`; old wording absent.
- Owner specimen conflict: stop cards had repetitive `條件` / `數據`.
  - Countercheck: direct stop-loss cards keep `決策` / `原因` / `下一步` / `價格`, and omit the old low-signal lines.
- Owner specimen conflict: unheld `淘汰` vs `等資料`.
  - Countercheck: state/funnel logic no longer globally forces data issues into `淘汰`; narrow `等資料` handling is tested.

## Additional Challenge
- After an over-broad first fix made many wait states become `等資料`, tests caught the regression. The final fix narrows `等資料` to state-machine-confirmed data recovery only.

## Not Tested
- Live Telegram delivery.
- Production DB writes/backfill.

## QA Conclusion
通過

Evidence:
- `244 passed, 145 warnings, 57 subtests passed`.
- Official dry-run message list checked with no live Telegram delivery.
