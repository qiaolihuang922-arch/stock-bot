# CLEANUP_PLAN.md

## Cleanup Status

- Fixed 8 Markdown files are present and must be kept:
  - `AGENTS.md`, `DISPATCH.md`, `RESEARCH.md`, `CURRENT_STATE.md`, `CLEANUP_PLAN.md`, `TASK.md`, `CHANGELOG.md`, `QA_REPORT.md`.
- Active handoff files were compressed on 2026-06-15 to remove repeated backfill numbers, stale process detail, and report-output noise.
- UTF-8 reads are clean when using `Get-Content -Encoding UTF8`; default PowerShell display may still create false mojibake.

## Completed Cleanup / Consolidation

- `DISPATCH.md` holds active status, result summary, verification, git state, and next action.
- `CURRENT_STATE.md` holds stable project facts, implementation state, verification state, and known follow-ups.
- `TASK.md`, `CHANGELOG.md`, and `QA_REPORT.md` describe the current RR context task without terminal transcripts.
- No fixed Markdown file was deleted.

## Active Follow-ups

- `db_schema_review: rr_context_columns`
  - Owner applied `db/sql/v21_2_rr_context_columns.sql`.
  - Production read/backfill verified RR component columns on `daily_signal_snapshot`.
- `runner_gap: git_completion_gate_windows`
  - Bash gates fail on this Windows machine when WSL/Hyper-V is unavailable.
  - Add a PowerShell-equivalent completion gate or normalize gate execution.
- `md_encoding_hygiene`
  - Keep using `Get-Content -Encoding UTF8` or a small encoding check script for handoff files.
- `cleanup_candidate: tracked_reports`
  - `reports/backfill/*` and `reports/research/*` are tracked artifacts.
  - Do not delete without proving no runtime / test / replay consumer.
- `strategy_calibration`
  - v21.1 persists V10/V20, 20D/60D evidence, and now has a prepared RR component schema.
  - 2026-06-15 D-semantics patch clarified that `entry_quality` is an entry setup grade, not a general stock grade.
  - Future work should calibrate V20 cutoffs, retest success, heat/quality transitions, entry-quality thresholds, and RR target-basis choices from production outcomes.
- `signal_items_history`
  - Old `signal_items` rows were not reconstructed after RR fields were added.
  - This is acceptable unless a future task specifically needs historical report-run item analytics; new bot runs will write the fields.

## Boundaries

- Do not delete the fixed 8 Markdown files.
- Do not delete tracked reports, SQL, replay artifacts, or production data without consumer evidence.
- Do not turn one pasted report or one stock into a permanent hard-coded rule; extract reusable formatter contracts, gates, or validation routes.
- Do not use local runtime output as cross-run evidence.
