# CURRENT_STATE.md

## Current Task

- task_id: `telegram_readability_risk_wording_20260626`
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

- `REDUCE_25/REDUCE_50` cards now show share basis: total shares, suggested sell shares, ratio, and target remaining shares.
- Holding risk next-step now uses current price when available:
  - below warning -> `已跌破警戒 ...`
  - below stop -> `已跌破停損 ...`
- Overheat unheld cards no longer let `等量能` override `過熱觀察`; visible state becomes `等冷卻` when appropriate.
- Failed breakout triggers now require reclaim plus volume confirmation.
- Brief summary keeps `新倉：無有效進場` and adds reason.

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

- `python -m pytest tests/test_generator_report.py -k "holding_next_step_uses_risk_prices_not_breakout_zone or reduce_card_shows_share_basis or failed_breakout_card_does_not_show_attack_volume_as_positive or failed_breakout_within_reclaim_buffer_waits_reclaim_not_terminal_reject or overheat or today_buy"`
  - `14 passed, 219 deselected`
- Exact QA regression:
  - `4 passed`
- Full `tests/test_generator_report.py`:
  - `46 failed, 190 passed`
  - Not a completion blocker for this focused patch, but remains a cleanup risk.
- Git completion gate passed after push to `origin/main`.

## Known Findings

- Full `tests/test_generator_report.py` still has older unrelated summary/wording expectations.
- Legacy `.pytest_cache` is locked by old Windows ownership; bootstrap redirects pytest cache to D drive.
- Windows `py` launcher is unavailable; use repo `.venv` through bootstrap environment.
- Node/WSL/CAO UI service runtime is not restored yet.
- `tmux` missing blocks CAO agent runner.

## Next Action

- None for this task after git completion and closeout gates pass.
