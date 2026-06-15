# CLEANUP_PLAN.md

## Completed In Current Review

- Confirmed the fixed 8 Markdown files still exist and must be kept.
- Rechecked active handoff files with UTF-8 reading:
  - `AGENTS.md`
  - `DISPATCH.md`
  - `CURRENT_STATE.md`
  - `TASK.md`
  - `CHANGELOG.md`
  - `QA_REPORT.md`
- Confirmed `AGENTS.md` content is valid UTF-8; earlier mojibake was caused by default PowerShell decoding, not a broken file.
- Confirmed `reports/backfill/*` and `reports/research/*` are tracked repo artifacts, not disposable runtime output.
- Added an abstract handoff hygiene rule to `AGENTS.md`: active handoff files must be UTF-8 readable, free of mojibake / stale task state / broken commands, and post-cycle review must not hard-code one-off incidents.

## Current Post-cycle Review

- Root cause category: `證據鏈`, `文件不足`, `手機閱讀`, `runner/worktree`.
- What went wrong:
  - Product logic was fixed and tested before the process documents were fully audited.
  - The previous closeout over-focused on code/test/git completion and under-checked handoff hygiene.
  - Windows shell display created false mojibake noise unless files were read with explicit UTF-8.
  - The bash-based git gates cannot run on this machine because WSL/Hyper-V is unavailable, so Windows-equivalent gate evidence must be recorded.
- QA did catch core report conflicts, but did not independently enforce Markdown hygiene.
- Tech did not change DB schema, live Telegram, or production write paths.
- No single-date or single-stock dead rule was added. The new rule is an abstract handoff hygiene invariant.

## Active Cleanup Follow-ups

- `runner_gap: git_completion_gate_wsl_windows`
  - Current fact: `tools/cao_agent/*.sh` gates fail on this Windows machine when WSL/Hyper-V is unavailable.
  - Needed fix: add a PowerShell-equivalent gate or normalize runner execution path so closeout does not depend on WSL.
- `md_encoding_hygiene`
  - Current fact: UTF-8 reads are clean, but default PowerShell output can display mojibake.
  - Needed fix: document standard read command as `Get-Content -Encoding UTF8` or add a small encoding check script.
- `cleanup_candidate: tracked_reports`
  - Current fact: `reports/backfill/*` and `reports/research/*` are tracked artifacts.
  - Needed fix: do not delete without a dedicated cleanup task proving no runtime / test / replay consumer.
- `report_suite_baseline`
  - Current fact: report tests pass for the current targeted suite, but broader strategy behavior remains rule-based.
  - Needed fix: future PM task should separate "report wording conflict" from "strategy quality / bottom-buying model quality".
- `runner_gap: cao_codex_tui_send`
  - Current fact: CAO TUI automation can hang after prompt send.
  - Needed fix: noninteractive fallback or stable `codex exec` runner path.

## Boundaries

- Do not delete fixed 8 Markdown files.
- Do not delete tracked reports, production data, SQL, or replay artifacts without evidence of no consumer.
- Do not use local runtime output as cross-run evidence.
- Do not turn one pasted report into a permanent hard-coded rule; extract reusable gates, evidence routes, or formatter contracts instead.
