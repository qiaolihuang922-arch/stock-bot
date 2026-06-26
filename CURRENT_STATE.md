# CURRENT_STATE.md

## Current Task

- task_id: `telegram_mobile_readability_consolidation_20260626`
- status: `implemented + QA passed + pushed`
- version: `v21.1`
- live Telegram delivery: not run
- DB schema/write/backfill/delete: none
- startup: 依 `AGENTS.md` 啟動順序閱讀 `AGENTS.md` -> `DISPATCH.md` -> `CURRENT_STATE.md`

## Stable Context

- Owner reads Telegram on mobile; summary and cards must avoid repeated noise and recommendation-like wording.
- Future-watch `關注標的財報` can carry EPS、營收、三大法人，但每檔要短。
- Cross-day state must come from production DB or an approved persistent source.
- DB structure changes require Owner approval.
- No live Telegram delivery without separate Owner approval.
- On Windows, non-system development tools, caches, venvs, worktrees, runner context, artifacts, and logs should live on D drive by default.

## Current Implementation Notes

- MOPS source-error is hidden from future-watch output.
- Future-watch fundamentals are two lines per stock.
- Institutional line includes bias: `昨日法人偏買/偏賣/分歧：...`。
- Afterhours summary includes `明日優先` with action shares.
- Today-buy holding context is shortened.

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

- Syntax:
  - `py_compile` passed
- Focused regression:
  - `15 passed, 223 deselected`
- Read-only sample render:
  - 12 future-watch fundamentals use two-line compact format.
- Full `tests/test_generator_report.py` not rerun this turn; known legacy full-file wording failures remain a cleanup risk.
- Git completion gate passed after push to `origin/main`.

## Known Findings

- Full `tests/test_generator_report.py` still has older unrelated summary/wording expectations.
- Legacy `.pytest_cache` is locked by old Windows ownership; bootstrap redirects pytest cache to D drive.
- Windows `py` launcher is unavailable; use repo `.venv` through bootstrap environment.
- Node/WSL/CAO UI service runtime is not restored yet.
- `tmux` missing blocks CAO agent runner.

## Next Action

- None for this task after git completion and closeout gates pass.
