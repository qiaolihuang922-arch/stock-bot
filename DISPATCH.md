# DISPATCH.md

## Active

- task_md_holds: `future_watch_institutional_mobile_compact_20260626`
- status: `implemented + QA passed + pushed`
- current_version: `v21.1`
- live Telegram delivery: `not run`
- DB schema/write/backfill/delete: `none`
- startup: 依 `AGENTS.md` 啟動順序閱讀 `AGENTS.md` -> `DISPATCH.md` -> `CURRENT_STATE.md`

## Current Board

- Owner provided the盘後 future-watch specimen and asked to optimize the three-major institutional trading line.
- Display changed from long dated wording to compact mobile wording:
  - `昨日三大法人：外+2,736｜投-102｜自-480｜合+2,153張`
- Date is no longer displayed; `昨日` is the time label.
- Numbers are rounded to whole lots; unit appears once at line end.
- No source, DB, strategy, or live Telegram changes.

## Queued

- Restore CAO runner dependency after C-drive reinstall (`tmux` or Windows-compatible launcher).
- Clean full `tests/test_generator_report.py` legacy wording expectations.

## Recently Done

- `future_watch_institutional_mobile_compact_20260626`: implemented compact future-watch institutional display; QA passed; pushed.
- `future_watch_institutional_trading_20260626`: fixed institutional source parsing and date fallback; QA conditional pass; pushed.
- `telegram_all_cards_institutional_trading_20260626`: superseded by Owner correction; cards should not carry this line now.
- `future_watch_remove_history_events_20260626`: removed future-watch history analogy and 30-day Taiwan market event sections; QA passed; pushed.
- `docs_local_env_cleanup_20260626`: root Markdown compressed, D-drive deployment runbook optimized, local bootstrap verified, pushed.

## Verification

- Focused future-watch regression: `9 passed, 229 deselected`.
- Read-only sample render: 12 institutional lines use compact format.
- Full `tests/test_generator_report.py` not rerun this turn; known legacy full-file wording failures remain a cleanup item.
- Git completion gate passed after push to `origin/main`.

## Next Action

- None for this task after git completion and closeout gates pass.
