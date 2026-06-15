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
- Duplicate/version cleanup completed:
  - exact duplicates: `0`
  - multi-version extras: `0`
  - deleted rows: `0`
- `AGENTS.md` now requires DB backfill/prune tasks to automatically update MD and cleanup evidence.

## Active Follow-ups

- `signal_items_future_fill_check`
  - Historical `signal_items` rows were not fabricated.
  - Check the next real bot run to confirm new report items fill strategy-axis fields.
- `data_quality_tightening`
  - Replace remaining source/volume fallback paths that can make missing data look normal.
  - Missing data should become `insufficient`, `source_error`, `stale`, or `missing_source`.
- `runner_gap: git_completion_gate_windows`
  - Bash gates fail on this Windows machine when WSL/Hyper-V is unavailable.
  - Add a PowerShell-equivalent completion gate or normalize gate execution.
- `cleanup_candidate: tracked_reports`
  - `reports/backfill/*` and `reports/research/*` are tracked artifacts.
  - Do not delete without proving no runtime / test / replay consumer.

## Boundaries

- Do not delete the fixed 8 Markdown files.
- Do not delete tracked reports, SQL, replay artifacts, or production data without consumer evidence.
- Do not fabricate historical `signal_items` from daily_price.
- Do not use local runtime output as cross-run evidence.
