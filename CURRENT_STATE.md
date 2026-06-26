# CURRENT_STATE.md

## Current Task

- task_id: `future_watch_fundamentals_spaced_layout_20260626`
- status: `implemented + QA passed + pushed`
- version: `v21.1`
- live Telegram delivery: not run
- DB schema/write/backfill/delete: none
- startup: 依 `AGENTS.md` 啟動順序閱讀 `AGENTS.md` -> `DISPATCH.md` -> `CURRENT_STATE.md`

## Stable Context

- Owner reads Telegram on mobile; dense single-line fundamentals are harder to scan than spaced blocks.
- Future-watch `關注標的財報` should keep a spaced card-like layout.
- MOPS source-error should stay hidden from Telegram output.
- Cross-day state must come from production DB or an approved persistent source.
- No live Telegram delivery without separate Owner approval.
- Windows development tools and caches should live on D drive by default.

## Current Implementation Notes

- `關注標的財報` uses spaced layout again.
- Institutional line remains compact with bias label.
- Summary `明日優先` and source parsing fixes remain.

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

- Focused regression:
  - `11 passed, 227 deselected`
- Read-only sample render:
  - 2356、2376、2421 財報區恢復分行與空行。
- Full `tests/test_generator_report.py` not rerun this turn.
- Git completion gate passed after push to `origin/main`.

## Known Findings

- Full `tests/test_generator_report.py` still has older unrelated summary/wording expectations.
- Legacy `.pytest_cache` is locked by old Windows ownership; bootstrap redirects pytest cache to D drive.
- Windows `py` launcher is unavailable; use repo `.venv` through bootstrap environment.
- Node/WSL/CAO UI service runtime is not restored yet.
- `tmux` missing blocks CAO agent runner.

## Next Action

- None for this task after git completion and closeout gates pass.
