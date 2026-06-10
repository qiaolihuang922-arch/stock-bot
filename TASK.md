# TASK: unheld_market_overlay_version_20260610

## Status
- task_id: `unheld_market_overlay_version_20260610`
- type: `normal_patch`
- status: `complete`
- version: `v21.0.1`
- QA level: `L2`

## Owner Problem
Owner pasted a v21.0 report where all unheld candidates were shown as `等市場｜市場弱`, and asked:
- where is the analysis,
- version should be bumped to `21.0.1`.

The user-visible issue is not fake data. The issue is state attribution: market weakness was treated as every stock card's primary state, hiding the stock-specific next missing gate.

## User Visible Result
- Telegram report header and summary now show `v21.0.1`.
- Weak market remains visible as the reason/background.
- Unheld card primary state no longer short-circuits at `等市場` when a more specific stock gate exists.
- Current dry-run shows far / weak candidates as `等型態｜市場弱`, with state line `還差：出現 setup`.

## Non Goals
- No live Telegram delivery.
- No DB schema/RLS/grant/policy/index change.
- No production DB write/backfill.
- No holding stop-loss / sell logic change.

## Impacted Modules And Consumers
- `core/generator.py`: visible version and unheld state priority.
- `core/trade_state_machine.py`: schema version aligned to `v21.0.1`.
- Tests: report header/version expectations and failure specimen regression.
- Direct consumers: official `generate_report(dry_run=True)`, Telegram message list, runner artifact.

## Output Contract
- Market weak can block buying globally but should not always become the card's primary wait state.
- If no setup exists, card state is `等型態` even under market weakness.
- If volume/RR/heat are primary, they keep `等量能` / `等RR修復` / `等冷卻`.
- Header uses `v21.0.1`.

## Acceptance
- Targeted failure specimen tests pass.
- Broad generator/FSM/analysis/evidence tests pass.
- Official `generate_report(dry_run=True)` returns `v21.0.1` messages and no live Telegram delivery.

## Failure Specimen And Route
- Owner specimen: 2026-06-10 v21.0 report with all unheld cards `等市場｜市場弱`.
- Failure layer: official generator report and unheld formatter.
- Replay route: official dry-run plus generator/FSM regression tests.

## Forbidden / Blocking
- Do not fabricate market/volume/setup data.
- Do not turn weak-market candidates into buyable names.
- Do not live deliver Telegram without separate Owner approval.
