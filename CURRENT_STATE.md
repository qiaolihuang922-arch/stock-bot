# CURRENT_STATE.md

## Current Task

- task_id: `daily_market_evidence_writeback_20260610`
- status: `complete`
- version: `v21.0.2`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; visible wording must be decision-first and avoid internal pipeline noise.
- Current direction is v21 read-only trade state machine plus production pipeline hardening.
- Production source-of-truth remains Supabase / runner data, not local cache.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval.
- Non-schema DB write/backfill must use existing approved repo scripts or service APIs; direct hand-written production DML is forbidden.

## Current Changes

- Workflow daily evidence now runs at `08:20 UTC` (`16:20 Asia/Taipei`).
- Workflow bot run now runs at `08:25 UTC` (`16:25 Asia/Taipei`).
- Scheduled evidence no-payload path now uses `run_market_theme_freshness_check()` to backfill and verify both market/theme evidence tables.
- Approved payload path remains unchanged.
- Production DB backfilled `2026-06-09..2026-06-10` for:
  - `market_theme_confirmed_evidence`
  - `market_theme_index_daily_bars`

## Verification State

- Phase3/workflow contract: `20 passed, 8 skipped`.
- Backfill/preflight tests: `19 passed`.
- Independent DB latest dates:
  - `daily_price`: `2026-06-10`
  - `daily_signal_snapshot`: `2026-06-10`
  - `market_theme_confirmed_evidence`: `2026-06-10`
  - `market_theme_index_daily_bars`: `2026-06-10`
- Freshness check for `2026-06-10` and `2026-06-09`: `already-complete`.
- Official dry-run: `messages 4`, visible `v21.0.2`.

## Known Follow-ups

- GitHub Actions live run after push is not yet proven.
- Local bash workflow execution tests skipped because this machine's `bash` points to unavailable WSL/Hyper-V.
- `sector_theme_members` historical membership remains blocked: available source is latest profile mapping, not dated membership history.
