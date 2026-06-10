# CLEANUP_PLAN.md

## Completed In This Round

- Removed `.cao_agent_context/` stale runtime output. It is ignored by git and not a source-of-truth.
- Rewrote `tools/cao_agent/DEPLOYMENT.md` to document the current Windows + WSL deployment path.
- Rewrote `tools/cao_agent/README.md` to point to the deployment source-of-truth and daily runner commands.
- Compressed active handoff Markdown files to remove stale preface task state and mojibake-heavy old sections.

## Active Cleanup Follow-ups

- `market_theme_membership_history_gap`
  - Backfill can safely write `market_theme_confirmed_evidence` and `market_theme_index_daily_bars` from official historical TWSE sources.
  - `sector_theme_members` cannot be called historical coverage because current source only proves latest company profile membership.
  - Needed fix: find an official dated membership source or keep this table as mapping-only in future audits.
- `runner_gap: cao_codex_tui_send`
  - CAO API/UI and WSL Codex auth are available, but TUI automation can hang after prompt send.
  - Needed fix: noninteractive fallback or stable `codex exec` runner path.
- `runner_gap: git_completion_gate_wsl_windows`
  - Bash gate under WSL/Windows path can misread line endings and report many false modified files.
  - Needed fix: Windows-aware equivalent gate or normalize runner execution path.
- `report_suite_baseline`
  - Full historical `tests/test_generator_report.py` is not a clean baseline.
  - Needed fix: separate PM/Tech/QA task to classify existing strategy/funnel expectation failures.
- `md_encoding_hygiene`
  - Older Markdown sections had mojibake when read in PowerShell.
  - Current active handoff files were compressed, but `AGENTS.md` still contains mojibake in local display.

## Boundaries

- Do not delete fixed 8 Markdown files.
- Do not delete production data, reports, or SQL unless a cleanup task proves no consumer.
- Do not use local runtime output as cross-run evidence.
