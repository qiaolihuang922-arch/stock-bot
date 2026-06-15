# CLEANUP_PLAN.md

## Cleanup Status

- Fixed 8 Markdown files are present and must be kept:
  - `AGENTS.md`, `DISPATCH.md`, `RESEARCH.md`, `CURRENT_STATE.md`, `CLEANUP_PLAN.md`, `TASK.md`, `CHANGELOG.md`, `QA_REPORT.md`.
- Active handoff files are compressed and UTF-8 readable.
- No fixed Markdown file was deleted.

## Completed Cleanup / Consolidation

- `daily_signal_snapshot` v21.1 strategy-axis memory backfill completed:
  - `5786` rows upserted from `daily_price`.
  - all `5786` rows have non-null core strategy-axis memory fields.
- Retest-memory overfill was corrected:
  - only active retest rows keep `retest_reference_price` and `retest_days_since_breakout`.
  - non-retest rows are null for those fields.
- Duplicate/version cleanup completed:
  - exact duplicates: `0`
  - multi-version extras: `0`
  - deleted rows: `0`
- DB table health audit utility added:
  - `scripts/audit_db_table_health.py`
  - read-only, no schema change, no live Telegram.
- False duplicate risk reduced:
  - duplicate checks now use table-specific keys;
  - event tables are not treated as duplicate only because stock code/name repeats.

## Active Follow-ups

- `signal_items_future_fill_check`
  - Historical `signal_items` rows were not fabricated.
  - Next real bot run should create fresh rows with strategy-memory fields.
- `market_theme_index_daily_bars_ohlcv_gap`
  - `open`, `high`, `low`, `volume`, `turnover`, `member_count` are all null in current production rows.
  - Decide whether to find a real official source, guard consumers, or hide/deprecate those placeholders.
- `signal_outcomes_metric_gap`
  - `max_high_pct` and `max_drawdown_pct` are all null.
  - Implement a real outcome metric job or remove those fields from any active strategy expectation.
- `data_quality_tightening`
  - Replace remaining source/volume fallback paths that can make missing data look normal.
  - Missing data should become `insufficient`, `source_error`, `stale`, or `missing_source`.
- `runner_gap: git_completion_gate_windows`
  - Bash gates may fail on this Windows machine when WSL/Hyper-V is unavailable.
  - Add a PowerShell-equivalent completion gate or normalize gate execution.
- `cleanup_candidate: tracked_reports`
  - `reports/backfill/*` and `reports/research/*` are tracked artifacts.
  - Do not delete without proving no runtime / test / replay consumer.

## Boundaries

- Do not delete the fixed 8 Markdown files.
- Do not delete tracked reports, SQL, replay artifacts, or production data without consumer evidence.
- Do not fabricate historical `signal_items` from daily_price.
- Do not use local runtime output as cross-run evidence.
- Do not interpret expected source/formula/version constants as broken strategy data.
