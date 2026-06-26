# DISPATCH.md

## Active

- task_md_holds: `future_watch_fundamentals_spaced_layout_20260626`
- status: `implemented + QA passed + pending commit/push`
- current_version: `v21.1`
- live Telegram delivery: `not run`
- DB schema/write/backfill/delete: `none`
- startup: 依 `AGENTS.md` 啟動順序閱讀 `AGENTS.md` -> `DISPATCH.md` -> `CURRENT_STATE.md`

## Current Board

- Owner rejected the compact two-line fundamentals layout as too cramped.
- Future-watch fundamentals now use spaced layout again:
  - stock line;
  - EPS line;
  - revenue line;
  - institutional line;
  - blank line between stocks.
- MOPS source-error hiding, institutional bias labels, summary priority line, and source fixes remain.
- No strategy, DB, source, or live Telegram changes.

## Queued

- Restore CAO runner dependency after C-drive reinstall (`tmux` or Windows-compatible launcher).
- Clean full `tests/test_generator_report.py` legacy wording expectations.

## Recently Done

- `future_watch_fundamentals_spaced_layout_20260626`: restored spaced fundamentals layout; QA passed pending git completion.
- `telegram_mobile_readability_consolidation_20260626`: implemented mobile readability consolidation; pushed.
- `future_watch_institutional_mobile_compact_20260626`: implemented compact future-watch institutional display; pushed.
- `future_watch_institutional_trading_20260626`: fixed institutional source parsing and date fallback; pushed.

## Verification

- Focused regression: `11 passed, 227 deselected`.
- Read-only sample render: 2356/2376/2421 use spaced layout with blank lines.
- Full `tests/test_generator_report.py` not rerun this turn.
- Git completion gate: pending commit/push.

## Next Action

- Commit and push spaced layout fix, then run git completion and closeout gates.
