# CLEANUP_PLAN.md

## Cleanup Status

- Fixed 8 Markdown files are present and must be kept:
  - `AGENTS.md`, `DISPATCH.md`, `RESEARCH.md`, `CURRENT_STATE.md`, `CLEANUP_PLAN.md`, `TASK.md`, `CHANGELOG.md`, `QA_REPORT.md`.
- Active handoff files were compressed on 2026-06-15 to remove repeated backfill numbers, stale process detail, and report-output noise.
- UTF-8 reads are clean when using `Get-Content -Encoding UTF8`; default PowerShell display may still create false mojibake.

## Completed Cleanup / Consolidation

- `DISPATCH.md` now holds only active status, result summary, verification, git state, and next action.
- `CURRENT_STATE.md` now holds stable project facts, current implementation state, verification state, and known follow-ups.
- `CHANGELOG.md` and `QA_REPORT.md` keep implementation / QA evidence without duplicated runtime transcripts.
- Report artifacts and DB cleanup details were reduced to reusable facts instead of per-command logs.
- No fixed Markdown file was deleted.

## Active Follow-ups

- `runner_gap: git_completion_gate_windows`
  - Bash gates fail on this Windows machine when WSL/Hyper-V is unavailable.
  - Add a PowerShell-equivalent completion gate or normalize gate execution.
- `md_encoding_hygiene`
  - Keep using `Get-Content -Encoding UTF8` or a small encoding check script for handoff files.
- `cleanup_candidate: tracked_reports`
  - `reports/backfill/*` and `reports/research/*` are tracked artifacts.
  - Do not delete without proving no runtime / test / replay consumer.
- `strategy_calibration`
  - v21.1 persists V10/V20 and 20D/60D evidence, but thresholds remain rule-based.
  - Future work should calibrate V20 cutoffs, retest success, and heat/quality transitions from production outcomes.

## Boundaries

- Do not delete the fixed 8 Markdown files.
- Do not delete tracked reports, SQL, replay artifacts, or production data without consumer evidence.
- Do not turn one pasted report or one stock into a permanent hard-coded rule; extract reusable formatter contracts, gates, or validation routes.
- Do not use local runtime output as cross-run evidence.
