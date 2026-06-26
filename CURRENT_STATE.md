# CURRENT_STATE.md

## Current Task

- task_id: `telegram_all_cards_institutional_trading_20260626`
- status: `implemented + QA conditional pass + pushed`
- version: `v21.1`
- live Telegram delivery: not run
- DB schema/write/backfill/delete: none
- startup: 依 `AGENTS.md` 啟動順序閱讀 `AGENTS.md` -> `DISPATCH.md` -> `CURRENT_STATE.md`

## Stable Context

- Owner reads Telegram on mobile; cards must say whether action is possible, what is missing, and what invalidates the setup.
- Cross-day state must come from production DB or an approved persistent source.
- DB structure changes require Owner approval.
- No live Telegram delivery without separate Owner approval.
- `準備觀察` is not buy; only explicit `可買` is actionable.
- On Windows, non-system development tools and caches should live on D drive by default.

## Current Implementation Notes

- Every holding/unheld card now hard-outputs `昨日三大法人買賣超：...`.
- Supported payload keys: `institutional_trading`, `three_major`, `three_major_institutional`, `institutional_investors`, `legal_person_trading`.
- Missing data displays `昨日三大法人買賣超：資料不足`.
- No official three-major data fetch/backfill source was added in this turn.

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

- Exact final-card regression:
  - `4 passed`
- Combined focused regression:
  - `6 passed, 229 deselected`
- Full `tests/test_generator_report.py` not rerun this turn; known legacy full-file wording failures remain a cleanup risk.
- Git completion gate passed after push to `origin/main`.

## Known Findings

- Full `tests/test_generator_report.py` still has older unrelated summary/wording expectations.
- Legacy `.pytest_cache` is locked by old Windows ownership; bootstrap redirects pytest cache to D drive.
- Windows `py` launcher is unavailable; use repo `.venv` through bootstrap environment.
- Node/WSL/CAO UI service runtime is not restored yet.
- `tmux` missing blocks CAO agent runner.
- Official three-major institutional trading source is not implemented yet; cards show `資料不足` until payload supplies data.

## Next Action

- None for this task after git completion and closeout gates pass.
