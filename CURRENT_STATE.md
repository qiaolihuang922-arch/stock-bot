# CURRENT_STATE.md

## Current Task

- task_id: `future_watch_remove_history_events_20260626`
- status: `implemented + QA passed + pushed`
- version: `v21.1`
- live Telegram delivery: not run
- DB schema/write/backfill/delete: none

## Stable Context

- Owner reads Telegram on mobile; cards must say whether action is possible, what is missing, and what invalidates the setup.
- Cross-day state must come from production DB or an approved persistent source.
- DB structure changes require Owner approval.
- No live Telegram delivery without separate Owner approval.
- `準備觀察` is not buy; only explicit `可買` is actionable.
- On Windows, non-system development tools and caches should live on D drive by default.

## Local Environment

- Tool root: `D:\tools`.
- Portable Git/Bash: `D:\tools\git`.
- Repo venv: `.venv`.
- D-drive caches/config: `D:\tools\gitconfig`, `D:\tools\home`, `D:\tools\cache`.
- Bootstrap:
  - PowerShell: `. .\tools\cao_agent\local_env.ps1`
  - cmd: `call tools\cao_agent\local_env.cmd`
- Daily bootstrap does not write Git config; set `STOCK_BOT_WRITE_GIT_CONFIG=1` only for first-time safe.directory/autocrlf repair.
- Full D-drive setup/runbook: `tools/cao_agent/DEPLOYMENT.md`.

## Verification Snapshot

- Future-watch focused tests: `8 passed, 224 deselected`.
- Combined focused regression: `20 passed, 212 deselected`.
- Official dry-run smoke:
  - `MESSAGE_COUNT=4`
  - `HAS_HISTORY=False`
  - `HAS_TW_EVENTS=False`
  - `HAS_FUTURE_WATCH=True`
  - `HAS_MOPS=True`
  - `HAS_FUND=True`
- Git completion gate passed after commit/push; closeout gate passed.

## Known Findings

- Full `tests/test_generator_report.py` still has older unrelated summary expectations.
- Legacy `.pytest_cache` is locked by old Windows ownership; bootstrap redirects pytest cache to D drive.
- Windows `py` launcher is unavailable; use repo `.venv` through the bootstrap environment.
- Node/WSL/CAO UI service runtime is not restored yet.

## Next Action

- None for this task.
