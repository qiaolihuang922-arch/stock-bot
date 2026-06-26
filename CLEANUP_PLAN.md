# CLEANUP_PLAN.md

## Current Cleanup Status

- Active product cleanup: future-watch fundamentals should balance readability and length.
- No DB schema, production DB data, or live Telegram action is in scope.

## Completed

- D-drive portable Git/Bash installed under `D:\tools\git`.
- Local bootstrap scripts added under `tools/cao_agent/`.
- Future-watch output removes history analogy and 30-day Taiwan market event sections.
- Institutional trading line removed from holding/unheld cards after Owner correction.
- Future-watch fundamentals include institutional trading.
- TWSE institutional source handles recent-date fallback.
- TPEx institutional source parses official English fields.
- Future-watch institutional line uses compact wording with bias label.
- Future-watch source-error noise hidden.
- Afterhours summary includes action-share priority line.
- Future-watch fundamentals restored to spaced layout after compact version proved too cramped.

## Deferred

- Restore CAO runner service dependency after C-drive reinstall: install/replace `tmux` in a D-drive-compatible path or update runner to use a Windows-compatible session launcher.
- Unlock or remove legacy `.pytest_cache` with elevated Windows permissions.
- Restore Node/WSL/CAO UI services with D-drive-first placement.
- Clean unrelated legacy expectations in full `tests/test_generator_report.py`.
- Later remove unused historical/global future-watch helpers only after confirming no other scripts/tests consume them.

## Rule Of Thumb

- Keep root Markdown short and current.
- Put operational commands in `tools/cao_agent/DEPLOYMENT.md`.
- Put uncertain cleanup candidates here instead of deleting evidence.
