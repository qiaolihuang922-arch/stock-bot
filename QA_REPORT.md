# QA_REPORT: setup_aware_volume_fsm_20260610

## Scope
- Unheld trade state machine.
- Volume gate semantics.
- Distance / setup interaction.
- Telegram report card and summary rendering.
- Read-only DB calibration artifact.

## Risk Scan
- Far-from-breakout low-volume names could be incorrectly marked `等量能`, hiding the real market/setup gate.
- RR or heat blockers could be overwritten by setup/distance wording.
- New states could be missing from funnel totals, card titles, or summary buckets.
- DB history calibration could accidentally imply a write/schema change.

## Semantic Consistency
- Market weak cards now show `等市場｜市場弱`.
- Near-breakout low-volume cards remain `等量能`.
- RR blocker cards show `等RR修復`.
- Overheat cards show `等冷卻`.
- Summary bucket matches visible card state.

## Failure Specimen Countercheck
- Owner specimen was a full v21 Telegram report, so QA replayed the official generator path.
- Official dry-run produced 4 messages and the unheld summary `未持倉 7｜僅追蹤 7（等市場）`.
- No live Telegram delivery was run.

## Additional Challenge
- Broad test suite covered generator, FSM, analysis, strategy evidence, and the new calibration module.
- Read-only Supabase artifact confirmed historical signal/price rows can support volume-bucket review without schema or write changes.

## Not Tested
- Live Telegram delivery.
- Production DB writes/backfill.
- Automatic adaptive volume threshold application to live decisions.

## QA Conclusion
通過
