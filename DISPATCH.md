# DISPATCH.md

## Active

- task_md_holds: `telegram_readability_risk_wording_20260626`
- status: `implemented + QA conditional pass + pushed`
- current_version: `v21.1`
- live Telegram delivery: `not run`
- DB schema/write/backfill/delete: `none`
- startup: 依 `AGENTS.md` 啟動順序閱讀 `AGENTS.md` -> `DISPATCH.md` -> `CURRENT_STATE.md`

## Current Board

- 06/26 Owner failure specimen showed mobile-reading issues in v21.1 intraday Telegram report:
  - `減碼 50%` did not show share basis/sell quantity.
  - Already-breached warning lines still said future `跌破警戒 ... 續減`.
  - Overheated unheld names could show `等量能｜過熱觀察`.
  - Failed breakout needed clearer no-chase/confirmation wording.
  - Summary needed a reason for no new entries.
- Code now updates position/unheld/summary formatter wording and final-output tests.
- CAO runner could not start PM stage because local machine lacks `tmux`; local equivalent flow was used and the gap is tracked.

## Queued

- Restore CAO runner dependency after C-drive reinstall (`tmux` or Windows-compatible launcher).
- Clean full `tests/test_generator_report.py` legacy wording expectations.

## Recently Done

- `telegram_readability_risk_wording_20260626`: implemented focused Telegram readability fixes; QA conditional pass.
- `future_watch_remove_history_events_20260626`: removed future-watch `歷史類比` and `未來30日台股影響事件`; QA passed; pushed.
- `docs_local_env_cleanup_20260626`: root Markdown compressed, D-drive deployment runbook optimized, local bootstrap verified, pushed.
- `local_d_drive_env_bootstrap_20260626`: installed D-drive portable Git/Bash and local bootstrap.

## Verification

- Focused final-output regression: `14 passed, 219 deselected`.
- Exact QA regression: `4 passed`.
- Full `tests/test_generator_report.py`: `46 failed, 190 passed`; failures are not treated as pass and remain a cleanup item.
- Git completion gate passed after push to `origin/main`.

## Next Action

- None for this task after git completion and closeout gates pass.
