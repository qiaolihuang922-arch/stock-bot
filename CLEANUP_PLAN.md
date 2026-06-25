# CLEANUP_PLAN.md

## Current Cleanup Status

- Active cleanup: compress root handoff Markdown and centralize D-drive deployment instructions.
- No product code, DB schema, production DB data, or live Telegram action is in scope.

## Completed

- D-drive portable Git/Bash installed under `D:\tools\git`.
- Local bootstrap scripts added under `tools/cao_agent/`.
- Local Git config, HOME, pip/pytest/npm/uv caches, and CAO context redirected away from C drive.
- Local pytest and generator dry-run verified after C-drive reinstall.
- v21.1 Telegram readability fixes remain completed and pushed.

## Deferred

- Unlock or remove legacy `.pytest_cache` with elevated Windows permissions.
- Restore Node/WSL/CAO UI services with D-drive-first placement.
- Clean unrelated legacy expectations in full `tests/test_generator_report.py`.

## Rule Of Thumb

- Keep root Markdown short and current.
- Put operational commands in `tools/cao_agent/DEPLOYMENT.md`.
- Put uncertain cleanup candidates here instead of deleting evidence.
