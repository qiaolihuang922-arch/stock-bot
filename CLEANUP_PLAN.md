# CLEANUP_PLAN.md

## Current Cleanup Status

- No runtime output or SQL draft was created in this task.
- No production DB cleanup was performed.
- No table or row deletion was performed.

## Completed This Round

- Replaced misleading low-repair support wording.
- Replaced inconsistent volume wording.
- Removed raw tiny RR gap from chase-risk cards.
- Added report-layer tests for the recurring mobile-reading failures.
- Rewrote active handoff docs to UTF-8 readable Chinese.
- Added follow-up checks for warning-breached holdings, low-repair actionable market text, and large absolute reclaim gaps.
- Installed D-drive portable Git/Bash under `D:\tools\git`.
- Added local D-drive bootstrap scripts under `tools/cao_agent/`.
- Redirected local Git config, HOME, pip/pytest/npm/uv caches, and CAO context away from C drive.
- Verified local pytest and generator dry-run after the C-drive reinstall.

## Deferred / Not In Scope

- Full legacy summary expectation cleanup in `tests/test_generator_report.py`.
- Broader strategy calibration beyond current report-consistency fixes.
- Any DB backfill / prune / dedupe.
- Optional future cleanup: unlock or remove legacy `.pytest_cache` with elevated Windows permissions.
- Optional future environment work: D-drive-first Node/WSL/CAO service restoration.

## Cleanup Rules Reinforced

- Do not add single-stock permanent rules.
- Future report readability fixes must include a formatter or official report test, not only helper tests.
