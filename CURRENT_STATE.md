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

- Per-stock holding/unheld cards no longer display `昨日三大法人買賣超`.
- Future-watch `關注標的財報` now prints `昨日三大法人買賣超 {trade_date}：外資 ...｜投信 ...｜自營 ...｜合計 ...` under each watched stock fundamentals block.
- Missing institutional data is scoped to that fundamentals block as `昨日三大法人買賣超：資料不足`.
- Live source support added for TWSE T86 and TPEx three-institution daily trading.
- Read-only TWSE live probe for 20260625 confirmed 1326 merged rows and real 2421 data.

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
  - `8 passed, 228 deselected`
- Read-only live probe:
  - `STATUS=available`
  - `INSTITUTIONAL_ITEMS=1326`
  - 2421 TWSE T86 institutional trading merged for `20260625`
- Full `tests/test_generator_report.py` not rerun this turn; known legacy full-file wording failures remain a cleanup risk.
- Git completion gate pending commit/push.

## Known Findings

- Full `tests/test_generator_report.py` still has older unrelated summary/wording expectations.
- Legacy `.pytest_cache` is locked by old Windows ownership; bootstrap redirects pytest cache to D drive.
- Windows `py` launcher is unavailable; use repo `.venv` through bootstrap environment.
- Node/WSL/CAO UI service runtime is not restored yet.
- `tmux` missing blocks CAO agent runner.
- TPEx institutional parser is implemented, but this turn's manual live evidence only confirmed TWSE.

## Next Action

- Commit and push current task, then run git completion and closeout gates.
