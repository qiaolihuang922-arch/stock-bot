# CLEANUP_PLAN.md

## Completed This Cycle

- Split overheat display by current price behavior:
  - still rising / locked -> cooling no-chase.
  - already pulling back -> retest confirmation.
  - sharp pullback -> support-focused retest.
- Compacted low-repair cards to show support / 5-day MA / volume and only the missing condition.
- Suppressed positive repair history on rejected cards.
- Added focused regression tests for the above.

## Cleanup Notes

- No obsolete files were deleted.
- No DB data was pruned, rewritten, or backfilled.
- No live Telegram was sent.

## Follow-Ups

- Full report test cleanup:
  - several legacy tests still assert older long-form source / industry / retest text.
  - separate task should decide whether to update or delete stale assertions.
- Summary section still has some repeated operational lines; handle as a separate readability task.
- Consider a replay artifact for 06/23 intraday report so future QA can compare official output without relying only on helper tests.

## Post-Cycle Review

- Root cause: display logic treated `heat_state` as a single state and ignored whether price had already pulled back.
- Risk category: repeated_pattern + mobile_readability.
- QA gap prevented: added tests at formatter level plus official dry-run evidence.
- Rule abstraction:
  - primary card state must reflect current price behavior, not only the historical blocker family.
  - when all routes are non-actionable, display the concrete missing condition rather than repeating route names.
  - rejected cards must not show positive recovery history unless it is actual execution memory.
