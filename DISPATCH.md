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
  - apply SQL migration first;
  - then backfill two years with `--lookback-days 730`;
  - script uses 120-day warmup.

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

## Git Completion

- latest commit: `3a4901b6c8aa7ac213811f16c8fe9b0113a910c4`
- branch: `main`
- upstream: `origin/main`
- local HEAD equals upstream HEAD: `yes`
- worktree: clean except unreadable local `.pytest_cache` warning from PowerShell/git status.
- bash gate: blocked by local WSL/Hyper-V unavailable; Windows-equivalent git checks passed.

## Next Action

- Production DB is not migrated/backfilled by this task.
- Owner should apply `db/sql/v21_1_strategy_feature_snapshot_columns.sql`, then run approved backfill.
