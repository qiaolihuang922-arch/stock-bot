# CURRENT_STATE.md

## Current Task

- task_id: `local_d_drive_env_bootstrap_20260626`
- status: `D-drive local environment implemented + verified + pushed`
- version: `v21.1`
- live Telegram delivery: not run
- DB schema change: none
- DB write/backfill/delete: none

## Stable Context

- Owner reads Telegram on mobile; every card must answer: can act now, what is missing, and what invalidates the setup.
- Cross-day state must come from production DB or approved persistent source.
- DB structure changes require Owner approval.
- No live Telegram delivery without separate Owner approval.
- `準備觀察` is not buy. Only explicit `可買` is actionable.
- Owner's C drive is unreliable/reinstalled. On Windows, install or write non-system development dependencies to D drive by default.

## Current Implementation State

- D-drive tool root: `D:\tools`.
- Portable Git/Bash: `D:\tools\git`.
- D-drive Git config: `D:\tools\gitconfig\.gitconfig`.
- D-drive HOME for local tools: `D:\tools\home`.
- D-drive caches: `D:\tools\cache\pip`, `D:\tools\cache\pytest`, `D:\tools\cache\npm`, `D:\tools\cache\uv`.
- Local bootstrap scripts: `tools/cao_agent/local_env.ps1` and `tools/cao_agent/local_env.cmd`.
- Existing repo `.venv` remains usable and is added to PATH by the bootstrap scripts.
- Git safe.directory is configured in the D-drive Git config to handle C-drive reinstall/SID ownership mismatch.

## Verification State

- D-drive Git/Bash available: `git version 2.54.0.windows.1`; `GNU bash, version 5.3.9(1)-release`.
- D-drive local bootstrap works from both PowerShell process-bypass and cmd.
- Architect scope gate passed.
- Focused report regression: `12 passed, 219 deselected`.
- Pytest cache reroute probe: `1 passed, 230 deselected`.
- Local dry-run smoke: Flask app import OK; `generate_report(dry_run=True)` produced `dry_run message_count 4`.
- No production DB data was changed.

## Known Findings

- Full `tests/test_generator_report.py` still has older unrelated summary expectations.
- Legacy `.pytest_cache` is still locked by old Windows ownership and may make raw `git status` warn when listing untracked files.
- The bootstrap scripts redirect pytest cache to D-drive cache, so tests no longer need the locked `.pytest_cache`.
- Windows `py` launcher is still not available in PATH; use repo `.venv\Scripts\python.exe` through the bootstrap environment.
- Node/WSL/CAO service runtime is not restored yet; current local execution covers Git, Bash, Python, pytest, Flask import, and generator dry-run.

## Next Action

- None for this task. If CAO UI/WSL orchestration is needed later, restore it separately with D-drive-first placement for distro/worktree/output where feasible.
