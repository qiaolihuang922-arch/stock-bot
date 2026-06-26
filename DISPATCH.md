# DISPATCH.md

## Active

- task_md_holds: `future_watch_institutional_trading_20260626`
- status: `implemented + QA conditional pass + pushed`
- current_version: `v21.1`
- live Telegram delivery: `not run`
- DB schema/write/backfill/delete: `none`
- startup: 依 `AGENTS.md` 啟動順序閱讀 `AGENTS.md` -> `DISPATCH.md` -> `CURRENT_STATE.md`

## Current Board

- Owner corrected the display contract: yesterday three-major institutional trading should move out of per-stock cards and appear under future-watch `關注標的財報`.
- Holding and unheld Telegram cards no longer hard-output `昨日三大法人買賣超`, so missing source data does not create repeated card noise.
- Future-watch `關注標的財報` now appends `昨日三大法人買賣超` for each watched stock fundamentals block.
- Read-only live probe confirmed TWSE T86 source returns data for 20260625 and merges 1326 institutional rows; 2421 has real values instead of `資料不足`.
- CAO runner could not start PM stage because local machine lacks `tmux`; local equivalent PM -> Tech -> QA documents were used and the gap is tracked.

## Queued

- Restore CAO runner dependency after C-drive reinstall (`tmux` or Windows-compatible launcher).
- Clean full `tests/test_generator_report.py` legacy wording expectations.
- Separately live-verify TPEx institutional open-data row shape; parser support is added but this turn's manual live proof focused on TWSE.

## Recently Done

- `future_watch_institutional_trading_20260626`: moved institutional trading from stock cards to future-watch fundamentals; QA conditional pass; pushed.
- `telegram_all_cards_institutional_trading_20260626`: superseded by Owner correction; cards should not carry this line now.
- `telegram_readability_risk_wording_20260626`: implemented focused Telegram readability fixes; QA conditional pass.
- `future_watch_remove_history_events_20260626`: removed future-watch history analogy and 30-day Taiwan market event sections; QA passed; pushed.
- `docs_local_env_cleanup_20260626`: root Markdown compressed, D-drive deployment runbook optimized, local bootstrap verified, pushed.

## Verification

- Focused regression: `8 passed, 228 deselected`.
- Read-only live probe: `STATUS=available`, `INSTITUTIONAL_ITEMS=1326`, 2421 values merged from TWSE T86 for `20260625`.
- Full `tests/test_generator_report.py` not rerun this turn; known legacy full-file wording failures remain a cleanup item.
- Git completion gate passed after push to `origin/main`.

## Next Action

- None for this task after git completion and closeout gates pass.
