# TASK: setup_aware_volume_fsm_20260610

## Status
- task_id: `setup_aware_volume_fsm_20260610`
- type: `major`
- status: `complete`
- version: `v21.0`
- QA level: `L3`

## Owner Problem
Owner asked for a global code scan and best fix for:
- volume handling being too strict,
- the v21 trade state machine not helping enough,
- stocks far from breakout still sometimes being valid candidates.

The pasted v21 report showed far / weak-market stocks being classified mostly as volume wait states, making the system look unable to distinguish market, setup, volume, RR, and distance gates.

## User Visible Result
- Unheld cards now separate `等市場`, `等型態`, `等量能`, `等回測`, `等RR修復`, and `等冷卻`.
- Low volume is a primary blocker only for breakout / pre-breakout style setups where volume confirmation matters.
- Far-from-breakout is no longer treated as a universal no-buy reason; trend continuation, pullback reclaim, and valid setup contexts can bypass the old hard distance interpretation.
- Current dry-run weak-market candidates now show `等市場｜市場弱`, not `等量能` noise.

## Non Goals
- No live Telegram delivery.
- No DB schema/RLS/grant/policy/index change.
- No production DB write/backfill.
- No automatic live order lifecycle.

## Impacted Modules And Consumers
- `core/trade_state_machine.py`: unheld FSM guard/event ordering and setup-aware volume gate.
- `core/generator.py`: Telegram unheld state, funnel grouping, summary buckets, and trigger copy.
- `presentation/report.py`: visible unheld title/status rendering.
- `services/volume_calibration.py`: read-only DB artifact for volume bucket outcome review.
- Direct consumers: official `generate_report(dry_run=True)`, Telegram report message list, runner artifact, QA probes.

## Output Contract
- `WAIT_MARKET` / `等市場`: market gate first; trigger says market must turn stronger before setup review.
- `WAIT_SETUP` / `等型態`: no valid setup formed, but not a volume-only rejection.
- `WAIT_VOLUME` / `等量能`: only when volume is primary gate, mainly near-breakout / breakout-confirm contexts.
- `WAIT_RR` / `等RR修復`: RR blocker remains primary when volume is not the primary gate.
- Overheat cards show `等冷卻`, not misleading `等回測`.
- Read-only volume calibration artifact must include `db_write=false` and `schema_change=false`.

## Acceptance
- Targeted FSM / report regression tests pass.
- Broad generator / FSM / analysis / evidence / calibration tests pass.
- Official `generate_report(dry_run=True)` produces messages without live Telegram delivery.
- Read-only Supabase calibration artifact can group DB history by setup context and volume bucket.

## Failure Specimen And Route
- Owner specimen: 2026-06-10 v21.0 unheld report where every far/weak candidate looked like `等量能` or an unhelpful wait state.
- Failure layer: official generator report and unheld formatter, not only helper fixture.
- Replay route: `generate_report(dry_run=True)` plus generator/FSM regression tests.

## Forbidden / Blocking
- Do not weaken hard stop / holding sell logic.
- Do not claim buyable if market/setup/RR/volume gates are still closed.
- Do not use synthetic helper-only evidence as final proof.
- No live Telegram delivery without separate Owner approval.
