# CURRENT_STATE.md

## Current Task

- task_id: `render_git_tg_db_pipeline_check_20260609`
- status: `QA passed, pending commit/push`
- version: `v21.0`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; visible wording must be decision-first and avoid internal pipeline terms.
- Current direction is v21 read-only trade state machine plus production pipeline hardening.
- Do not expand DB schema unless read-only behavior proves an actual cross-day memory gap.
- Production source-of-truth remains Supabase / runner data, not local cache.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval.

## Current Changes

- Render dispatch URL fixed from missing `stock-bot.yml` to existing `stock-bot-clean.yml`.
- Daily evidence workflow can write market-theme evidence without requiring `MARKET_THEME_APPROVED_PAYLOAD`.
- Approved freshness script backfilled and verified market-theme rows for 2026-06-04, 2026-06-05, and 2026-06-08.
- No live Telegram delivery was run.

## Verification State

- Workflow static contract: `2 passed, 1 warning`.
- Render/TG/DB/evidence package: `142 passed, 1 warning, 64 subtests passed`.
- official `generate_report(dry_run=True, return_write_results=True)`: `messages 4`, `reply_markup True`, `write_results {}`.
- Production DB read-after-write shows `daily_price`, `signal_runs`, `daily_signal_snapshot`, `market_theme_confirmed_evidence`, and `market_theme_index_daily_bars` rows through 2026-06-08.

## Known Follow-ups

- Commit/push and run git completion gate before final completion claim.
- CAO TUI automation gap remains separate from this product patch.
