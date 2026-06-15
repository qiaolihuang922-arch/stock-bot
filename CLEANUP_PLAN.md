# CLEANUP_PLAN.md

## Cleanup Status

- Fixed 8 Markdown files are present and must be kept:
  - `AGENTS.md`, `DISPATCH.md`, `RESEARCH.md`, `CURRENT_STATE.md`, `CLEANUP_PLAN.md`, `TASK.md`, `CHANGELOG.md`, `QA_REPORT.md`.
- Active handoff files are compressed and UTF-8 readable.
- No fixed Markdown file was deleted.

## Completed Cleanup / Consolidation

- `DISPATCH.md` holds active task status, result summary, verification, git state, and next action.
- `CURRENT_STATE.md` holds stable project facts, current implementation state, verification state, and known follow-ups.
- `TASK.md`, `CHANGELOG.md`, and `QA_REPORT.md` describe the current strategy-axis split task without terminal transcripts.
- Prior D-semantics and RR wording details were folded into the broader reusable rule: do not flatten stock strength, setup readiness, and actionability into one visible grade.

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
  - v21.1 now separates visible strength/setup/actionability.
  - Future work should calibrate V20 cutoffs, retest success, heat/quality transitions, entry-quality thresholds, and RR target-basis choices from production outcomes.
- `signal_items_history`
  - Old `signal_items` rows were not reconstructed after RR fields were added.
  - This is acceptable unless a future task specifically needs historical report-run item analytics; new bot runs will write the fields.

## Boundaries

- Do not delete the fixed 8 Markdown files.
- Do not delete tracked reports, SQL, replay artifacts, or production data without consumer evidence.
- Do not turn one pasted report or one stock into a permanent hard-coded rule; extract reusable formatter contracts, gates, or validation routes.
- Do not use local runtime output as cross-run evidence.
