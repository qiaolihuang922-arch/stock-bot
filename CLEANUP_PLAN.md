# CLEANUP_PLAN.md

## Completed This Cycle

- Synced overheat-pullback summary buckets with visible card state.
- Fixed weekday 13:00 phase fallback that could render `非交易`.
- Added concrete overheat pullback triggers.
- Replaced rejected placeholder `觀察` with `型態未過` fallback.
- Converted failed-breakout positive volume wording to safer failed-breakout wording.
- Added numeric low-repair gap values.
- Added focused regression tests and official dry-run evidence.

## Cleanup Notes

- No obsolete files were deleted.
- No DB data was pruned, rewritten, or backfilled.
- No live Telegram was sent.

## Follow-Ups

- Full report test cleanup:
  - stale v19/v20 tests still assert old source-error, industry, retest, limit-card, and future-watch text.
  - separate task should decide whether to update or retire those assertions.
- Summary section still contains some operational lines that may be too verbose; handle as a separate readability task.
- Consider a durable replay artifact for 06/23 intraday reports so future QA can validate official output without relying only on helper tests.

## Post-Cycle Review

- Root cause: raw strategy state and user-visible card state diverged after recent readability changes, but summary still counted raw state.
- Risk category: repeated_pattern + mobile_readability + evidence_chain.
- QA gap addressed: added tests that compare raw state, display bucket, card title, and official dry-run output.
- Rule abstraction:
  - summary must count what the user sees, not only internal raw state.
  - card state must reflect current price behavior, not only historical blocker family.
  - rejected cards must have concrete action-blocking reasons.
