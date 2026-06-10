# CHANGELOG: daily_market_evidence_writeback_20260610

## Changes
- `.github/workflows/stock-bot-clean.yml`
  - Moved scheduled `daily_evidence` from `0 6 * * 1-5` UTC to `20 8 * * 1-5` UTC.
  - Moved scheduled `bot` from `10 6 * * 1-5` UTC to `25 8 * * 1-5` UTC.
  - Kept the five-minute gap between evidence write and bot delivery.
  - Updated all schedule-to-`RUN_MODE` mappings.
- `scripts/run_phase3_evidence_automation.py`
  - Normal scheduled path now writes `daily_signal_snapshot` and, when no approved payload is provided, runs `run_market_theme_freshness_check()`.
  - The freshness path backfills and verifies `market_theme_confirmed_evidence` and `market_theme_index_daily_bars`.
  - Approved payload mode still uses `run_market_theme_confirmed_evidence()`.
- `tests/test_phase3_evidence_automation.py`
  - Updated scheduled main-path expectation to daily write plus freshness/backfill.
  - Added regression for approved payload preserving the old writer path.
- `tests/test_workflow_runtime_config.py`
  - Updated cron expectations.
  - Local bash execution tests now skip when local WSL/bash is unavailable; static workflow contract checks still run.

## Contract Impact
- GitHub scheduled runtime changes only; visible report version remains `v21.0.2`.
- No Telegram payload shape change.
- No DB schema change.
- Production writeback now uses existing approved `scripts/backfill_market_theme_sources.py` for missing market/theme rows.

## Production Backfill
- Dry-run:
  ```powershell
  .\.venv\Scripts\python.exe scripts\backfill_market_theme_sources.py --historical-range --start-date 2026-06-09 --end-date 2026-06-10 --dry-run
  ```
  Result: `market_theme_confirmed_evidence` ready with 18 rows; `market_theme_index_daily_bars` ready with 20 rows.
- Executed:
  ```powershell
  .\.venv\Scripts\python.exe scripts\backfill_market_theme_sources.py --historical-range --start-date 2026-06-09 --end-date 2026-06-10 --write --confirm-write
  ```
  Result: wrote 18 confirmed evidence rows and 20 index daily bar rows; both read-after-write passed.

## Verification
- Phase3 + workflow contract:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_phase3_evidence_automation.py tests/test_workflow_runtime_config.py -q --tb=short
  ```
  Result: `20 passed, 8 skipped`.
- Backfill/preflight:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_market_theme_source_backfill.py tests/test_app_render_preflight.py -q --tb=short
  ```
  Result: `19 passed`.
- Independent DB read:
  - `daily_price` latest `2026-06-10`; `2026-06-09` rows 12, `2026-06-10` rows 12.
  - `daily_signal_snapshot` latest `2026-06-10`; `2026-06-09` rows 12, `2026-06-10` rows 12.
  - `market_theme_confirmed_evidence` latest `2026-06-10`; `2026-06-09` rows 9, `2026-06-10` rows 9.
  - `market_theme_index_daily_bars` latest `2026-06-10`; `2026-06-09` rows 10, `2026-06-10` rows 10.
- Freshness check:
  ```powershell
  .\.venv\Scripts\python.exe scripts\run_phase3_evidence_automation.py --freshness-check-only --freshness-lookback-days 2 --safe-write-time 14:00 --now 2026-06-10T16:30:00+08:00
  ```
  Result: `2026-06-10` and `2026-06-09` both `already-complete`.
- Official dry-run:
  - `messages 4`
  - first header `【06/10 盤後｜v21.0.2】`
  - last header `【06/10 未來30日關注｜v21.0.2】`

## Coverage Layers
- Workflow schedule and mode mapping.
- Scheduled evidence main path.
- Approved market/theme backfill interface.
- Production DB read-after-write.
- Official generator smoke.

## Residual Risk
- Local workflow shell execution tests skipped because this machine's `bash` points to unavailable WSL/Hyper-V. Static workflow contract checks still passed.
- `sector_theme_members` remains blocked for historical backfill because only latest company profile membership is available; this task does not claim dated membership history.
