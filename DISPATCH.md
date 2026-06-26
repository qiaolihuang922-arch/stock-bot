# DISPATCH.md

## Active

- task_md_holds: `telegram_mobile_readability_consolidation_20260626`
- status: `implemented + QA passed + pending commit/push`
- current_version: `v21.1`
- live Telegram delivery: `not run`
- DB schema/write/backfill/delete: `none`
- startup: 依 `AGENTS.md` 啟動順序閱讀 `AGENTS.md` -> `DISPATCH.md` -> `CURRENT_STATE.md`

## Current Board

- Owner asked to fix all remaining user-view issues in the afterhours specimen.
- Implemented mobile readability consolidation:
  - hide MOPS source-error from Telegram output;
  - compact future-watch fundamentals to two lines per stock;
  - add institutional bias labels;
  - add afterhours `明日優先` with sell/reduce shares;
  - shorten today-buy context line.
- No strategy, DB, source, or live Telegram changes.
- CAO runner still lacks `tmux`; local equivalent PM -> Tech -> QA documents were used.

## Queued

- Restore CAO runner dependency after C-drive reinstall (`tmux` or Windows-compatible launcher).
- Clean full `tests/test_generator_report.py` legacy wording expectations.

## Recently Done

- `telegram_mobile_readability_consolidation_20260626`: implemented mobile readability consolidation; QA passed pending git completion.
- `future_watch_institutional_mobile_compact_20260626`: implemented compact future-watch institutional display; pushed.
- `future_watch_institutional_trading_20260626`: fixed institutional source parsing and date fallback; pushed.
- `future_watch_remove_history_events_20260626`: removed future-watch history analogy and 30-day Taiwan market event sections; pushed.
- `docs_local_env_cleanup_20260626`: root Markdown compressed, D-drive deployment runbook optimized, local bootstrap verified, pushed.

## Verification

- Syntax: `py_compile` passed.
- Focused regression: `15 passed, 223 deselected`.
- Read-only sample render: 12 future-watch fundamentals use two-line compact format.
- Full `tests/test_generator_report.py` not rerun this turn; known legacy full-file wording failures remain a cleanup item.
- Git completion gate: pending commit/push.

## Next Action

- Commit and push readability consolidation, then run git completion and closeout gates.
