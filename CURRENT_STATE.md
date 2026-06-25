# CURRENT_STATE.md

## Current Task

- task_id: `docs_local_env_cleanup_20260626`
- status: `docs cleanup verified + pushed`
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

- Git/Bash/Python bootstrap works locally.
- Focused report regression: `12 passed, 219 deselected`.
- Local dry-run smoke: Flask import OK; `generate_report(dry_run=True)` produced `4` messages.
- UTF-8 readback passed for fixed Markdown and deployment docs.
- Architect scope gate passed.
- Git completion and closeout gates passed after commit/push.

## Known Findings

- Full `tests/test_generator_report.py` still has older unrelated summary expectations.
- Legacy `.pytest_cache` is locked by old Windows ownership; bootstrap redirects pytest cache to D drive.
- Windows `py` launcher is unavailable; use repo `.venv` through the bootstrap environment.
- Node/WSL/CAO UI service runtime is not restored yet.

## Next Action

- None for this task. Future CAO/WSL restoration should follow the D-drive-first deployment runbook.
