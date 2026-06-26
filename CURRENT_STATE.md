# CURRENT_STATE.md

## Current Task

- task_id: `future_watch_institutional_mobile_compact_20260626`
- status: `implemented + QA passed + pending commit/push`
- version: `v21.1`
- live Telegram delivery: not run
- DB schema/write/backfill/delete: none
- startup: 依 `AGENTS.md` 啟動順序閱讀 `AGENTS.md` -> `DISPATCH.md` -> `CURRENT_STATE.md`

## Stable Context

- Owner reads Telegram on mobile; summary and cards must avoid repeated noise and recommendation-like wording.
- Future-watch `關注標的財報` can carry EPS、營收、三大法人，但每行要短。
- Cross-day state must come from production DB or an approved persistent source.
- DB structure changes require Owner approval.
- No live Telegram delivery without separate Owner approval.
- On Windows, non-system development tools, caches, venvs, worktrees, runner context, artifacts, and logs should live on D drive by default.

## Current Implementation Notes

- Per-stock holding/unheld cards do not display `昨日三大法人`.
- Future-watch institutional line now uses compact format:
  - `昨日三大法人：外+2,736｜投-102｜自-480｜合+2,153張`
- Date is not shown.
- Lots are rounded to whole numbers.
- Source parsing fixes from previous task remain in place.

## Local Environment

- Tool root: `D:\tools`.
- Portable Git/Bash: `D:\tools\git`.
- Repo venv: `.venv`.
- D-drive caches/config: `D:\tools\gitconfig`, `D:\tools\home`, `D:\tools\cache`.
- Bootstrap:
  - PowerShell: `. .\tools\cao_agent\local_env.ps1`
  - cmd: `call tools\cao_agent\local_env.cmd`
- CAO runner gap: `tools/cao_agent/ensure_cao_services.sh` currently fails because `tmux` is not installed after C-drive reinstall.

## Verification Snapshot

- Focused future-watch regression:
  - `9 passed, 229 deselected`
- Read-only sample render:
  - 12 institutional lines use compact format.
- Full `tests/test_generator_report.py` not rerun this turn; known legacy full-file wording failures remain a cleanup risk.
- Git completion gate pending commit/push.

## Known Findings

- Full `tests/test_generator_report.py` still has older unrelated summary/wording expectations.
- Legacy `.pytest_cache` is locked by old Windows ownership; bootstrap redirects pytest cache to D drive.
- Windows `py` launcher is unavailable; use repo `.venv` through bootstrap environment.
- Node/WSL/CAO UI service runtime is not restored yet.
- `tmux` missing blocks CAO agent runner.

## Next Action

- Commit and push compact display fix, then run git completion and closeout gates.
