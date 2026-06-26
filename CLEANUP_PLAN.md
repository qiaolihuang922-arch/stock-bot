# CLEANUP_PLAN.md

## Current Cleanup Status

- Active product cleanup: institutional trading data must appear in future-watch `關注標的財報` without false `資料不足`.
- No DB schema, production DB data, or live Telegram action is in scope.

## Completed

- D-drive portable Git/Bash installed under `D:\tools\git`.
- Local bootstrap scripts added under `tools/cao_agent/`.
- Local Git config, HOME, pip/pytest/npm/uv caches, and CAO context redirected away from C drive.
- Local pytest and generator dry-run verified after C-drive reinstall.
- Future-watch output removes history analogy and 30-day Taiwan market event sections.
- Telegram holding reduce cards now show share basis and current warning-breach wording.
- Telegram unheld overheat/failed-breakout wording now avoids chase-like ambiguity.
- Institutional trading line removed from holding/unheld cards after Owner correction.
- Future-watch fundamentals include institutional trading.
- TWSE institutional source now handles recent-date fallback.
- TPEx institutional source now parses official English fields.

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
