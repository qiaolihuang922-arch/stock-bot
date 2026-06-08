# TASK: trade_state_machine_v21_completion_20260608

## Status
- task_id: `trade_state_machine_v21_completion_20260608`
- type: `risk_patch`
- status: `complete`
- version: `v21.0`
- QA level: `L3`

## Owner Problem
v21 trade state machine was visible in the report, but the previous round was still conditional because full generator regression was not clean. The report also still had a visible conflict: an unheld card could say `WAIT_VOLUME` in the title but show strategy sample/source as the main blocker. Owner asked to finish the next round so the dry-run output can be judged as a complete effect, not a half product.

## User Visible Result
- Official dry-run report stays on `v21.0`.
- Holding cards show `trade state / action / trigger` on the official generator path.
- Today-buy holdings explicitly say they are not current strategy buy points and cannot be treated as continuation buys.
- Unheld cards are no longer collapsed into only reject/eliminate; they can show wait states such as `WAIT_VOLUME`, `WAIT_PULLBACK`, `WAIT_RR`, and next-day confirmation.
- Main blocker attribution now prefers visible hard blockers such as volume, market weakness, RR, and pullback distance. Source gaps remain visible as decision evidence but do not override the card title blocker.

## Non Goals
- No live Telegram delivery.
- No DB schema/RLS/grant/policy/role/index change.
- No production state snapshot write.
- No broker/order automation.

## Impacted Modules And Consumers
- `core/generator.py`: today-buy wording, source status helper, ledger fail-closed maturity handling.
- `presentation/report.py`: unheld blocker priority and evidence-adjusted rejected title behavior.
- `tests/test_generator_report.py`: v21 visible state and denoised report contract.
- Direct consumer: official `generate_report(dry_run=True)` message list.

## Output Contract
- Do not restore the old first-read preface.
- Do not show empty zero-count funnel parts.
- Holding cards must not use new-entry RR/composite score as if it were a holding decision score.
- Unheld blocker priority: hard blocker first; source gate primary only when no clearer blocker exists.
- Source missing/error must still fail closed and never become buyable.

## Acceptance
- `tests/test_generator_report.py tests/test_trade_state_machine.py` full pass.
- Official `generate_report(dry_run=True)` produces v21.0 messages without live delivery.
- Dry-run unheld cards must not show a mismatch like title `WAIT_VOLUME` but blocker `sample missing`.

## Failure Specimen And Route
- Owner samples before v21 completion showed unheld items as noisy reject/eliminate lists and an odd funnel summary.
- Route: formatter helper -> official generator -> dry-run message list.

## Forbidden / Blocking
- No live Telegram delivery.
- No production DB write or schema change.
- If full generator regression is not clean, do not claim complete.
