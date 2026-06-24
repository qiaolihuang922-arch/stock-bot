# CLEANUP_PLAN.md

## Completed This Cycle

- Added phase-aware holding handling labels so intraday reports do not say `明日處理`.
- Added low-repair near-ready display for cases that only miss the 5-day MA by a small gap.
- Added `等站回` for failed-breakout cards that have a real reclaim zone and are close enough to watch.
- Compacted `等站回` cards so they do not show duplicate trade-state / data lines.
- Compacted actionable low-repair buy cards so the first readable action is small-position test / support / 5-day MA / no chase.
- Hid no-edge summary backtest lines (`無明顯優勢`) because they do not change the action.
- Replaced generic holding next-step wording with concrete warning / stop price actions.
- Reworked sharp overheat pullback wording to wait for stop / support confirmation.
- Added failed-breakout reclaim-zone gap display.
- Removed repeated unheld card lines by using one trigger line for overheat, low repair, and failed breakout.
- Replaced `可準備（不可買）` user-facing wording with `準備觀察（待確認）`.
- Added / updated focused regression tests for the above contracts.
- Ran official dry-run without live Telegram delivery.

## Cleanup Notes

- No obsolete files were deleted.
- No DB data was pruned, rewritten, or backfilled.
- No live Telegram was sent.

## Follow-Ups

- Full report test cleanup:
  - stale v19/v20/v21 tests still assert old source-error, industry, retest, limit-card, `有效買點`, `明日處理`, and terminal `淘汰` text.
  - separate task should decide whether to update or retire those assertions.
- Consider a durable replay artifact for 06/23 reports so future QA can validate official output without relying only on helper tests.

## Post-Cycle Review

- 2026-06-24 addendum:
  - Root cause: actionable buy cards were not routed through the same compact mobile contract as wait cards, so the first real buy signal carried legacy duplicate lines.
  - Risk category: repeated_pattern + mobile_readability.
  - Guard added: low-repair actionable regression now rejects duplicate trade-state / buy-point / reason / data lines and requires the compact small-position line.
- 2026-06-24 addendum:
  - Root cause: the formatter collapsed distinct states into generic wait / reject wording, so near-ready low repair and near reclaim failed breakouts looked either too bearish or too vague.
  - Risk category: repeated_pattern + mobile_readability + state_contract.
  - Guard added: low-repair near-ready, failed-breakout reclaim, and phase-aware holding labels now have focused regressions and official dry-run checks.
- Root cause: prior readability cleanup changed labels but did not consistently bind them to actionable prices / support conditions, and did not enforce a single-trigger card contract.
- Risk category: repeated_pattern + mobile_readability + evidence_chain.
- QA gap addressed: tests now cover official card text for holding risk prices, overheat / low-repair one-trigger output, failed-breakout reclaim gaps, and prepare-label consistency.
- Rule abstraction:
  - holding next action should name warning / stop prices when available.
  - unheld card should not repeat the same buy condition as `等待`, `有效買點`, and `明日觸發`; one trigger line is enough.
  - failed breakout must say which zone must be reclaimed and how far price is from it.
