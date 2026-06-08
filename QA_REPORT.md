# QA_REPORT: trade_state_machine_v21_completion_20260608

## Scope
- v21 visible trade state in official report cards.
- Unheld wait-state and blocker attribution.
- Holding today-buy wording and existing-holding RR hiding.
- Source missing/source error fail-closed paths.
- Evidence maturity fail-closed scoring.

## Risk Scan
- Source missing/error must not become buyable.
- Holding cards must not show new-entry RR/composite score as a holding decision score.
- Card title and main blocker must not contradict each other.
- Zero-count funnel noise must not return.

## Semantic Consistency
- Holding summary and cards stay aligned on one primary action per holding.
- Dry-run unheld summary is `unheld 7 / tracking 7 / wait pullback 1 / wait volume 6`, and cards show matching wait states.
- Source missing remains visible under decision evidence but does not override volume/market blocker when those are clearer.

## Failure Specimen Countercheck
- Prior owner samples showed confusing unheld reject/eliminate output and odd funnel counts.
- Current dry-run shows wait states such as `WAIT_VOLUME` and `WAIT_PULLBACK`, and blocker text follows the visible state.

## Questions And Counter Evidence
- Could source errors become buys? No: source-missing/source-error tests still assert not actionable.
- Could fail-closed maturity fake complete data? No: low-level artifact verifier state is preserved; only the report-level maturity dimension passes when the visible report is fail-closed.

## Not Tested
- Live Telegram delivery was not run.
- Production DB write/state snapshot was not run.
- GitHub Actions runner was not manually triggered in this local round.

## QA Conclusion
pass
