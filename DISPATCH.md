# DISPATCH.md

## Active

- task_md_holds: `strategy_feature_persistence_v21_1_20260615`
- status: `complete`
- owner_request:
  - Re-check from scratch whether v21.1 strategy features need DB fields / more recording.
  - Add fields if needed.
  - Decide historical backfill length.
  - No live Telegram delivery.

## Current Result

- Decision: yes, v21.1 strategy features should be persisted as typed DB columns.
- Production schema was checked after Owner applied the SQL migration:
  - `daily_signal_snapshot` has all v21.1 typed feature columns.
  - `signal_items` has all v21.1 typed feature columns.
- Root cause found for market/theme evidence stale rows:
  - `daily_price` is written inside normal `run_mode=bot` after-close generator path.
  - market/theme evidence was only wired to `run_mode=daily_evidence`.
  - GitHub workflow had `workflow_dispatch` only, so `daily_evidence` did not run daily unless manually dispatched.
- Reworked workflow so normal `run_mode=bot` also runs market/theme freshness after the bot step.
- `daily_evidence` remains as a manual-only recovery mode, not the daily primary path.
- Added migration artifact:
  - `db/sql/v21_1_strategy_feature_snapshot_columns.sql`
- Target tables:
  - `daily_signal_snapshot`
  - `signal_items`
- Persisted strategy features:
  - `volume_ratio_10`, `volume_ratio_20`
  - `resistance_20`, `resistance_60`
  - `breakout_price_20`, `breakout_price_60`
  - `breakout_distance_20`, `breakout_distance_60`
  - `retest_zone_low`, `retest_zone_high`, `retest_zone_label`
  - compact `raw_result` on `daily_signal_snapshot`
- Daily writer, signal item writer, and guarded backfill now include these fields.
- Writer paths fall back to legacy columns if production schema has not been applied yet.
- Backfill recommendation:
  - SQL migration has been applied by Owner and verified read-only;
  - two-year v21.1 strategy snapshot backfill has been executed with `--lookback-days 730`;
  - script uses 120-day warmup.
- Backfill completed:
  - `daily_signal_snapshot` v21.1: 5112 rows across 12 tracked stocks.
  - All 12 tracked stocks have v21.1 snapshots through `2026-06-15`.
  - All persisted v21.1 feature fields are non-null on those 5112 rows.
  - market/theme evidence gaps for `2026-06-11`, `2026-06-12`, `2026-06-15` were filled by approved script.
- Cleanup completed:
  - Added approved cleanup script `scripts/prune_daily_signal_snapshot_versions.py`.
  - Added approved recovery script `scripts/backfill_snapshots_from_daily_price.py`.
  - Removed 1670 old `daily_signal_snapshot` rows whose same `stock_id` / `trade_date` already had `v21.1`.
  - Investigated the remaining 118 old-version rows:
    - `2303` 2026/04 had `daily_price` rows but no v21.1 snapshot.
    - `2301` 2026/05 had `daily_price` rows but no v21.1 snapshot.
    - Root cause: TWSE historical backfill source missed those stock/month segments; existing DB `daily_price` had the truth.
  - Rebuilt missing v21.1 snapshots from existing `daily_price` with full 12-stock context:
    - `2303` 2026/04: 20 rows.
    - `2301` 2026/05: 20 rows.
  - Removed the remaining 118 old-version rows after v21.1 replacements existed.
  - Post-cleanup `daily_signal_snapshot` versions: only `v21.1`.
- Report readability fix completed:
  - Root cause: only the `急彈待回測` formatter branch printed retest zone, V10/V20, quality, and RR details; `等型態` / `等RR修復` branches fell back to generic text.
  - Non-actionable unheld cards now share compact setup context in `量化差距`.
  - Redundant after-hours `盤面：證據不足｜待確認` and `數據：...風控不適用` lines are suppressed for waiting / rejected tracking cards when the gap line already carries the decision data.
- Breakout distance display follow-up completed:
  - `距突破` is now a standalone line on holding and unheld stock cards whenever the value exists.
  - The line is display-only and does not depend on strategy branch selection.
  - `盤面` no longer embeds `遠離突破（x%）` / `接近突破（x%）`; it keeps only structure / strength / volume context.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_daily_snapshot_store.py tests/test_backfill_signals.py tests/test_volume_calibration.py tests/test_analysis_engine.py::AnalysisEngineTest::test_v21_1_snapshot_exports_multi_window_volume_and_retest_zone -q --tb=short
```

Result: `19 passed`.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_analysis_engine.py tests/test_signal_validator.py tests/test_trade_state_machine.py tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_backfill_signals.py tests/test_backfill_daily_price_history.py tests/test_daily_snapshot_store.py tests/test_volume_calibration.py tests/test_strategy_evidence.py -q --tb=short
```

Result: `334 passed, 149 warnings, 57 subtests passed`.

Official dry-run:
- `VERSION v21.1`
- `messages 4`
- `write_results None`
- no live Telegram delivery.

TWSE backfill dry-run:
- `daily_price rows: 3`
- `daily_signal_snapshot rows: 3`
- `VALIDATION OK`
- `DRY RUN ONLY: no database writes`

Market/theme evidence freshness / backfill check:
- `2026-06-10`: complete (`market_theme_confirmed_evidence=9`, `market_theme_index_daily_bars=10`)
- `2026-06-11`: complete after backfill (`market_theme_confirmed_evidence=9`, `market_theme_index_daily_bars=10`)
- `2026-06-12`: complete after backfill (`market_theme_confirmed_evidence=9`, `market_theme_index_daily_bars=10`)
- `2026-06-13`: weekend / no rows expected
- `2026-06-14`: weekend / no rows expected
- `2026-06-15`: complete after backfill (`market_theme_confirmed_evidence=8`, `market_theme_index_daily_bars=9`)

Production v21.1 strategy snapshot read-back:
- 12 tracked stocks covered through `2026-06-15`.
- Total v21.1 rows: `5112`.
- Non-null counts for each v21.1 feature column: `5112`.

Duplicate cleanup read-back:
- `daily_signal_snapshot` total rows after cleanup: `5152`.
- `v21.1` rows preserved: `5152`.
- old rows overlapping `v21.1` stock/date keys: `0`.
- exact duplicate stock/date/version rows: `0`.
- preserved old-version rows without v21.1 replacement: `0`.

Cleanup script tests:
- `tests/test_prune_daily_signal_snapshot_versions.py`: `2 passed`.

Report readability tests:
- `tests/test_unheld_gap_format.py tests/test_generator_report.py`: `205 passed`.
- Breakout distance standalone-line regression is covered in the same suite: `205 passed, 147 warnings, 44 subtests passed`.

Workflow evidence automation tests:
- `71 passed, 13 subtests passed`

## Git Completion

- branch: `main`
- upstream: `origin/main`
- local HEAD equals upstream HEAD: `yes`
- worktree: clean except unreadable local `.pytest_cache` warning from PowerShell/git status.
- bash gate: blocked by local WSL/Hyper-V unavailable; Windows-equivalent git checks passed.

## Next Action

- No live Telegram delivery was performed.
- Normal `run_mode=bot` should fill market/theme evidence going forward after the bot run reaches the after-close safe-write window.
- Optional cleanup remains: Owner will delete the abandoned `trades` table manually, or it can be handled by a dedicated DB cleanup task.
