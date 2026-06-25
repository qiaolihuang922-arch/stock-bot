# DISPATCH.md

## Active

- task_md_holds: `local_d_drive_env_bootstrap_20260626`
- status: `D-drive local environment implemented + verified + pushed`
- current_version: `v21.1`
- live Telegram delivery: `not run`
- DB schema change: `none`
- DB write/backfill/delete: `none`

## Result Summary

- Windows C drive was reinstalled/unreliable, so local development now uses D-drive-first tooling.
- Portable Git for Windows 2.54.0 installed under `D:\tools\git`; Git Bash is available from the same tree.
- Local shell bootstrap scripts added under `tools/cao_agent/`: `local_env.ps1` and `local_env.cmd`.
- Bootstrap scripts set D-drive paths for Git config, HOME, pip/pytest/npm/uv caches, CAO context, repo `.venv`, Git, and Bash.
- Git dubious ownership from the C-drive SID change is handled via D-drive `GIT_CONFIG_GLOBAL`.
- Legacy `.pytest_cache` remains locked by old Windows ownership; pytest cache is redirected to `D:\tools\cache\pytest`.

## Verification

- `git version 2.54.0.windows.1`
- `GNU bash, version 5.3.9(1)-release`
- `Python 3.12.13`
- Architect scope gate passed with D-drive Git/Bash.
- Focused report regression: `12 passed, 219 deselected`.
- Single pytest cache reroute probe: `1 passed, 230 deselected`.
- Local import/dry-run smoke: Flask app import OK; `generate_report(dry_run=True)` produced `dry_run message_count 4`.

## Current Git State

- Environment bootstrap commit pushed to `origin/main`.
- Git completion gate passed after closeout.

## Next Action

- None for this task.
