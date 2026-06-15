# QA_REPORT: entry_quality_d_semantics_v21_1_20260615

## Test Scope

- User-visible handling of `entry_quality D`.
- Unheld funnel state preservation for limit/rebound price behavior.
- Snapshot reason wording for per-stock `market_grade == D`.
- Official generator message-list replay.

## Risk Scan

- If only text is replaced, D can still mean too many things and confuse Owner.
- If D is removed entirely, true setup-quality failure may become invisible.
- If limit-up is upgraded incorrectly, the report may imply chasing a locked/overheated move.
- If state-machine override remains, `LIMIT_REBOUND` / `WEAK_REBOUND` can be hidden as generic `等型態`.
- If snapshot reason says `市場弱`, per-stock weakness can be misread as broad market weakness.

## Cross-Block Semantic Consistency

- Hot / limit-up cards still say not to chase.
- Rebound/retest cards say quality will be re-evaluated after retest / strength confirmation.
- True setup cards still require `買點品質 B 以上`.
- Summary state names remain aligned with card titles.
- No card turns a non-actionable high potential reward into a buy recommendation.

## User Misread Risk

- Reduced: `品質 D→B` is no longer used for rebound/retest cards.
- Reduced: per-stock D is no longer labeled `市場弱` in snapshot reasons.
- Remaining by design: true setup-quality cards can still show current D, but with explicit `買點品質未過`.

## Failure Specimen Countercheck

- Owner 06/15 v21.1 report concern was replayed through official dry-run.
- `旺宏`-style rebound card now reads `買點品質：回測 / 轉強後重評`.
- Weak setup cards now read `買點品質未過（目前 D，需 B 以上）`.
- Limit-up remains non-actionable because the issue is chase / heat / retest, not because the stock is generically bad.

## Evidence

- `257 passed, 149 warnings, 44 subtests passed`.
- Official dry-run generated full message list without live delivery.
- Snapshot probe confirmed:
  - limit-up can be `market_grade=A+` while `entry_quality=D`;
  - multi-day rise can be `market_grade=A+` while entry remains observation because RR/setup is not actionable;
  - actual weak rebound remains D.

## Not Tested

- Live Telegram delivery.
- Scheduled Render/GitHub runner after push.
- Production DB writes or schema changes.

## QA Conclusion

通過

Reason: formatter, official generator, snapshot, condition, and state-machine tests cover the D-semantics issue without changing thresholds or live systems.
