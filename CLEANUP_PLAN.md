# CLEANUP_PLAN.md

## Cleanup Status

- Fixed 8 Markdown files are present and must be kept:
  - `AGENTS.md`, `DISPATCH.md`, `RESEARCH.md`, `CURRENT_STATE.md`, `CLEANUP_PLAN.md`, `TASK.md`, `CHANGELOG.md`, `QA_REPORT.md`.
- Active handoff files are compressed and UTF-8 readable.
- No fixed Markdown file was deleted.

## Completed Cleanup / Consolidation

- `DISPATCH.md` holds active task status, result summary, verification, git state, and next action.
- `CURRENT_STATE.md` holds stable project facts, current implementation state, verification state, and known follow-ups.
- `TASK.md`, `CHANGELOG.md`, and `QA_REPORT.md` describe the current v21.3 schema artifact task without terminal transcripts.
- Strategy-axis memory is now a DB schema concern, not a report-text convention.

## Active Follow-ups

- `db_schema_review: strategy_axis_memory_columns`
  - SQL artifact ready: `db/sql/v21_3_strategy_axis_memory_columns.sql`.
  - Owner must execute manually before production can persist the new fields.
- `backfill_after_v21_3_schema`
  - After schema is applied, run a repo-script backfill for the new memory fields.
  - Do not hand-write production DML.
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
- Do not turn one pasted report or one stock into a permanent hard-coded rule; extract reusable formatter contracts, gates, or validation routes.
- Do not use local runtime output as cross-run evidence.
