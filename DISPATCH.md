# DISPATCH.md

## Active

- task_md_holds: `telegram_all_cards_institutional_trading_20260626`
- status: `implemented + QA conditional pass + pending commit/push`
- current_version: `v21.1`
- live Telegram delivery: `not run`
- DB schema/write/backfill/delete: `none`
- startup: 依 `AGENTS.md` 啟動順序閱讀 `AGENTS.md` -> `DISPATCH.md` -> `CURRENT_STATE.md`

## Current Board

- Owner clarified that yesterday three-major institutional trading must be hard-output for every stock, not only buy candidates.
- Code now adds `昨日三大法人買賣超：...` to every holding and unheld card.
- Missing institutional data is shown as `資料不足`, not omitted or converted to 0.
- CAO runner could not start PM stage because local machine lacks `tmux`; local equivalent flow was used and the gap is tracked.

## Queued

- Restore CAO runner dependency after C-drive reinstall (`tmux` or Windows-compatible launcher).
- Clean full `tests/test_generator_report.py` legacy wording expectations.
- Add official three-major institutional trading data source/backfill path.

## Recently Done

- `telegram_all_cards_institutional_trading_20260626`: implemented every-card yesterday three-major institutional trading line; QA conditional pass.
- `telegram_readability_risk_wording_20260626`: implemented focused Telegram readability fixes; QA conditional pass.
- `future_watch_remove_history_events_20260626`: removed future-watch `歷史類比` and `未來30日台股影響事件`; QA passed; pushed.
- `docs_local_env_cleanup_20260626`: root Markdown compressed, D-drive deployment runbook optimized, local bootstrap verified, pushed.
- `local_d_drive_env_bootstrap_20260626`: installed D-drive portable Git/Bash and local bootstrap.

## Verification

- Exact final-card regression: `4 passed`.
- Combined focused regression: `6 passed, 229 deselected`.
- Full `tests/test_generator_report.py` not rerun this turn; known legacy full-file wording failures remain a cleanup item.

## Next Action

- Commit and push `telegram_all_cards_institutional_trading_20260626`, then run git completion and closeout gates.
