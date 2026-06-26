# DISPATCH.md

## Active

- task_md_holds: `future_watch_institutional_trading_20260626`
- status: `implemented + QA conditional pass + pushed`
- current_version: `v21.1`
- live Telegram delivery: `not run`
- DB schema/write/backfill/delete: `none`
- startup: 依 `AGENTS.md` 啟動順序閱讀 `AGENTS.md` -> `DISPATCH.md` -> `CURRENT_STATE.md`

## Current Board

- Owner correctly challenged the previous `資料不足` result: official institutional trading should not be treated as unavailable.
- Root cause found:
  - TWSE T86 was queried as a single date, so an empty/unpublished/holiday date could look like missing data.
  - TPEx OpenAPI uses English field names and `SecuritiesCompanyCode`, which the previous parser did not handle.
- Code now checks recent TWSE candidate dates and preserves the first available institutional row.
- Code now parses TPEx English institutional fields and ROC date.
- Read-only live probe now merges 2281 institutional rows; Owner 12-stock sample and TPEx 6488 all have institutional trading.
- CAO runner could not start PM stage because local machine lacks `tmux`; local equivalent PM -> Tech -> QA documents were used and the gap is tracked.

## Queued

- Restore CAO runner dependency after C-drive reinstall (`tmux` or Windows-compatible launcher).
- Clean full `tests/test_generator_report.py` legacy wording expectations.

## Recently Done

- `future_watch_institutional_trading_20260626`: fixed institutional source parsing and date fallback; QA conditional pass; pushed.
- `telegram_all_cards_institutional_trading_20260626`: superseded by Owner correction; cards should not carry this line now.
- `telegram_readability_risk_wording_20260626`: implemented focused Telegram readability fixes; QA conditional pass.
- `future_watch_remove_history_events_20260626`: removed future-watch history analogy and 30-day Taiwan market event sections; QA passed; pushed.
- `docs_local_env_cleanup_20260626`: root Markdown compressed, D-drive deployment runbook optimized, local bootstrap verified, pushed.

## Verification

- Focused source regression: `2 passed`.
- Focused future-watch regression: `8 passed, 229 deselected`.
- Read-only live probe: `status=available`, `institutional_count=2281`, 12 Owner sample stocks and TPEx 6488 have values.
- Full `tests/test_generator_report.py` not rerun this turn; known legacy full-file wording failures remain a cleanup item.
- Git completion gate passed after push to `origin/main`.

## Next Action

- None for this task after git completion and closeout gates pass.
