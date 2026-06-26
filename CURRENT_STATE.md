# CURRENT_STATE.md

## Current Task

- task_id: `future_watch_institutional_trading_20260626`
- status: `implemented + QA conditional pass + pending commit/push`
- version: `v21.1`
- live Telegram delivery: not run
- DB schema/write/backfill/delete: none
- startup: 依 `AGENTS.md` 啟動順序閱讀 `AGENTS.md` -> `DISPATCH.md` -> `CURRENT_STATE.md`

## Stable Context

- Owner reads Telegram on mobile; summary and cards must avoid repeated noise and recommendation-like wording.
- Cross-day state must come from production DB or an approved persistent source.
- DB structure changes require Owner approval.
- No live Telegram delivery without separate Owner approval.
- On Windows, non-system development tools, caches, venvs, worktrees, runner context, artifacts, and logs should live on D drive by default.

## Current Implementation Notes

- Per-stock holding/unheld cards do not display `昨日三大法人買賣超`.
- Future-watch `關注標的財報` prints `昨日三大法人買賣超 {trade_date}：外資 ...｜投信 ...｜自營 ...｜合計 ...`.
- TWSE T86 now tries recent candidate dates and keeps the first available data.
- TPEx OpenAPI English institutional fields and ROC `Date` are parsed.
- Missing institutional data is scoped to the fundamentals block as `昨日三大法人買賣超：資料不足`.

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

- Focused source regression:
  - `2 passed`
- Focused future-watch regression:
  - `8 passed, 229 deselected`
- Read-only live probe:
  - `status=available`
  - `errors=[]`
  - `institutional_count=2281`
  - Owner 12-stock sample and TPEx 6488 all have institutional trading values.
- Full `tests/test_generator_report.py` not rerun this turn; known legacy full-file wording failures remain a cleanup risk.
- Git completion gate pending commit/push.

## Known Findings

- Full `tests/test_generator_report.py` still has older unrelated summary/wording expectations.
- Legacy `.pytest_cache` is locked by old Windows ownership; bootstrap redirects pytest cache to D drive.
- Windows `py` launcher is unavailable; use repo `.venv` through bootstrap environment.
- Node/WSL/CAO UI service runtime is not restored yet.
- `tmux` missing blocks CAO agent runner.

## Next Action

- Commit and push source fix, then run git completion and closeout gates.
