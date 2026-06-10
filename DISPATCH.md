# DISPATCH.md

## Active

- task_md_holds: `daily_market_evidence_writeback_20260610`
- status: `QA passed, pending commit/push`
- owner_request:
  - Fix daily writeback first.
  - Scan global logic and Markdown instructions.
  - Backfill whatever duration is needed through approved repo flow.
  - No live Telegram delivery.

## Current Result

- Root cause:
  - `daily_price` and `daily_signal_snapshot` were already current through `2026-06-10`.
  - `market_theme_confirmed_evidence` and `market_theme_index_daily_bars` were stale at `2026-06-08`.
  - Workflow ran evidence at `06:00 UTC` / `14:00 Asia/Taipei`, too close to the safe-write boundary.
  - Scheduled no-payload path used the confirmed-evidence writer, not the existing freshness/backfill route that verifies both market/theme tables.
- Fix:
  - Daily evidence schedule moved to `08:20 UTC` / `16:20 Asia/Taipei`.
  - Bot schedule moved to `08:25 UTC` / `16:25 Asia/Taipei`.
  - Normal scheduled evidence path now writes daily snapshot then uses freshness/backfill for market/theme tables.
  - Approved payload mode remains available.
- Production backfill:
  - Backfilled `2026-06-09..2026-06-10`.
  - `market_theme_confirmed_evidence`: wrote 18 rows, read-after-write passed.
  - `market_theme_index_daily_bars`: wrote 20 rows, read-after-write passed.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_phase3_evidence_automation.py tests/test_workflow_runtime_config.py -q --tb=short
```

Result: `20 passed, 8 skipped`.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_market_theme_source_backfill.py tests/test_app_render_preflight.py -q --tb=short
```

Result: `19 passed`.

Independent DB read:

- `daily_price` latest `2026-06-10`.
- `daily_signal_snapshot` latest `2026-06-10`.
- `market_theme_confirmed_evidence` latest `2026-06-10`.
- `market_theme_index_daily_bars` latest `2026-06-10`.

Freshness check:

- `2026-06-10`: `already-complete`.
- `2026-06-09`: `already-complete`.

Official dry-run returned `messages 4`, visible version `v21.0.2`. No live Telegram delivery.

## Fixed Commands

Backfill dry-run:

```powershell
cd D:\reserch\stock-bot
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe scripts\backfill_market_theme_sources.py --historical-range --start-date 2026-06-09 --end-date 2026-06-10 --dry-run
```

Backfill write already executed this round:

```powershell
.\.venv\Scripts\python.exe scripts\backfill_market_theme_sources.py --historical-range --start-date 2026-06-09 --end-date 2026-06-10 --write --confirm-write
```

Freshness verification:

```powershell
.\.venv\Scripts\python.exe scripts\run_phase3_evidence_automation.py --freshness-check-only --freshness-lookback-days 2 --safe-write-time 14:00 --now 2026-06-10T16:30:00+08:00
```

## Next Action

- Commit and push the workflow/script/test/MD changes, then run git completion gate.
