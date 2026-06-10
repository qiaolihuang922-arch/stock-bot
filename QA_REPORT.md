# QA_REPORT: unheld_market_overlay_version_20260610

## Scope
- v21.0.1 visible report version.
- Unheld state priority under weak market.
- Telegram card and summary consistency.

## Risk Scan
- Market weakness could be hidden too much and accidentally imply buyability.
- Version bump could miss some report headers or summary titles.
- Existing RR/volume/heat gates could be displaced by setup wording.

## Semantic Consistency
- Header and summary use `v21.0.1`.
- Market weakness remains visible in the card subtitle/reason.
- Primary card state shows stock-specific next gate when present.
- Current weak-market dry-run remains non-actionable: no unheld buy signal is introduced.

## Failure Specimen Countercheck
- Owner specimen: all unheld cards showed `等市場｜市場弱`.
- Replay dry-run now shows `等型態｜市場弱` for the same weak/far/no-setup shape.
- Summary bucket now says `未持倉 7｜僅追蹤 7（等型態）`.

## Additional Challenge
- Broad suite included generator, FSM, analysis, strategy evidence, volume calibration, and market theme evidence.

## Not Tested
- Live Telegram delivery.
- Production DB write/backfill.

## QA Conclusion
通過
