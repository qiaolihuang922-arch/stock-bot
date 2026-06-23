# CLEANUP_PLAN.md

## Completed This Cycle

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
  - stale v19/v20 tests still assert old source-error, industry, retest, limit-card, and future-watch text.
  - separate task should decide whether to update or retire those assertions.
- Consider a durable replay artifact for 06/23 reports so future QA can validate official output without relying only on helper tests.

## Post-Cycle Review

- Root cause: prior readability cleanup changed labels but did not consistently bind them to actionable prices / support conditions, and did not enforce a single-trigger card contract.
- Risk category: repeated_pattern + mobile_readability + evidence_chain.
- QA gap addressed: tests now cover official card text for holding risk prices, overheat / low-repair one-trigger output, failed-breakout reclaim gaps, and prepare-label consistency.
- Rule abstraction:
  - holding next action should name warning / stop prices when available.
  - unheld card should not repeat the same buy condition as `等待`, `有效買點`, and `明日觸發`; one trigger line is enough.
  - failed breakout must say which zone must be reclaimed and how far price is from it.
