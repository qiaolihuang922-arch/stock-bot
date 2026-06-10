# TASK: daily_market_evidence_writeback_20260610

## Status
- task_id: `daily_market_evidence_writeback_20260610`
- type: `risk_patch`
- status: `complete`
- version: `v21.0.2`
- QA level: `L2`

## Owner Problem
Owner asked to fix daily DB writeback first, scan the global logic and Markdown instructions, then backfill whatever duration is needed through approved project flow.

Observed production state:
- `daily_price` latest: `2026-06-10`.
- `daily_signal_snapshot` latest: `2026-06-10`.
- `market_theme_confirmed_evidence` latest before fix: `2026-06-08`.
- `market_theme_index_daily_bars` latest before fix: `2026-06-08`.

## User Visible Result
- GitHub scheduled daily evidence now runs at `08:20 UTC` (`16:20 Asia/Taipei`).
- Scheduled bot runs five minutes later at `08:25 UTC` (`16:25 Asia/Taipei`).
- Normal `daily_evidence` path writes daily signal snapshots and uses the market/theme freshness backfill route when no approved payload secret is supplied.
- The freshness route checks recent confirmed trading days, backfills missing market/theme sources, and verifies read-after-write.
- Production DB was backfilled for `2026-06-09` through `2026-06-10` using `scripts/backfill_market_theme_sources.py`.

## Non Goals
- No live Telegram delivery.
- No DB schema, RLS, grant, policy, role, index, or constraint change.
- No direct hand-written production DML.
- No rewrite of `daily_price` or `daily_signal_snapshot` as the primary result.

## Impacted Modules And Consumers
- `.github/workflows/stock-bot-clean.yml`
  - Consumer: GitHub Actions scheduled `daily_evidence` and scheduled `bot`.
- `scripts/run_phase3_evidence_automation.py`
  - Consumer: GitHub Actions daily evidence job and local evidence probes.
- `scripts/backfill_market_theme_sources.py`
  - Used as existing approved DB write/backfill interface.
- `tests/test_phase3_evidence_automation.py`
- `tests/test_workflow_runtime_config.py`

## Output Contract
- `daily_evidence` must not require Telegram secrets and must not run live bot delivery.
- Without `MARKET_THEME_APPROVED_PAYLOAD`, scheduled evidence uses freshness/backfill for market/theme tables.
- With `MARKET_THEME_APPROVED_PAYLOAD`, the existing approved payload writer path remains available.
- Missing or failed market/theme source must fail closed.
- Backfill must report no schema change, no live Telegram, row counts, duplicate conflicts, and read-after-write status.

## Acceptance
- Unit tests for phase3 evidence and workflow contract pass or clearly skip local bash-only execution when WSL/bash is unavailable.
- Market/theme backfill dry-run for the missing date range reports the two target tables ready.
- Approved backfill write for `2026-06-09..2026-06-10` executes and read-after-write passes.
- Independent DB read confirms all four daily evidence tables latest `trade_date` is `2026-06-10`.
- Freshness check for the latest two trading days returns `already-complete`.
- Official generator dry-run still returns 4 messages at `v21.0.2`.

## Failure Specimen And Route
- Owner complaint: daily market evidence should have been written every day, but report logic still behaved as if market evidence was missing/weak.
- Failure layer: GitHub scheduled evidence path and production DB market/theme sources.
- Verification route: read-only DB latest-date check, approved backfill script, freshness check, official generator dry-run.

## Forbidden / Blocking
- Do not send live Telegram.
- Do not edit DB schema or policies without Owner approval.
- Do not use direct SQL/DML to patch production rows.
- Do not claim full historical membership backfill: `sector_theme_members` has no dated membership source in this task.
