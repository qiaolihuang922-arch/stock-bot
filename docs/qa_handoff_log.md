# QA Handoff Log

This file is append-only. Each development change should add a new entry so QA can decide which local checks and full regressions to run later.

## 2026-05-25 - batch-001

### Change 1
- Summary: v19.3.1 Telegram formatter small fixes: position detail titles now use the same action label as the position summary, and unheld detail cards now follow the same grouped order as the unheld summary.
- Files changed:
  - `core/generator.py`
  - `tests/test_generator_report.py`
- Test level: L1
- Scope: formatter / Telegram
- Minimal validation run:
  - `.venv/bin/python -m pytest tests/test_generator_report.py`
  - `.venv/bin/python -m pytest`
- Skipped tests:
  - Live Telegram delivery test
  - Live Supabase read/write test
  - Live TWSE data fetch
- Reason for skipping: Formatter-only change; no external-service behavior, DB schema, or data-fetching logic was changed.
- External services touched: none
- DB/schema/write risk: no
- QA focus:
  - Confirm v19.3.1 report title shows the new version.
  - Confirm holding detail order matches holding summary order.
  - Confirm holding detail title labels match summary action labels, especially `底倉續抱` and `續抱觀察`.
  - Confirm unheld detail cards follow group order: `禁止追高`, `等待冷卻`, `弱勢/未觸發`, `其他觀察`.

### Change 2
- Summary: Added this QA handoff log as the standard append-only record for future development batches.
- Files changed:
  - `docs/qa_handoff_log.md`
- Test level: L0
- Scope: docs / QA process
- Minimal validation run:
  - Manual file creation check.
- Skipped tests:
  - Unit tests
  - Integration tests
  - External-service tests
- Reason for skipping: Documentation-only process change.
- External services touched: none
- DB/schema/write risk: no
- QA focus:
  - Confirm future code changes append records here instead of overwriting old entries.

## 2026-05-25 - batch-002

### Change 1
- Summary: v19.3.1 formatter bug fix: normalized Telegram card price-line rendering so the closing full-width parenthesis is always included, covering the `價格：128.5（+2.80%）` case.
- Files changed:
  - `core/generator.py`
  - `tests/test_generator_report.py`
  - `docs/qa_handoff_log.md`
- Test level: L1
- Scope: formatter / Telegram
- Minimal validation run:
  - `.venv/bin/python -m pytest tests/test_generator_report.py`
- Skipped tests:
  - Full regression test suite
  - Live Telegram delivery test
  - Live Supabase read/write test
  - Live TWSE data fetch
- Reason for skipping: Single formatter-only bug fix; no strategy, sorting, grouping, DB, or external-service logic changed.
- External services touched: none
- DB/schema/write risk: no
- QA focus:
  - Confirm unheld detail card price lines end with a closing `）`.
  - Confirm `華邦電` renders as `價格：128.5（+2.80%）`.
  - Confirm no Telegram structure, sorting, grouping, or strategy wording changed.

## 2026-05-25 - batch-003

### Change 1
- Summary: v19.3.1 release blocker fix: added official daily write guard so online daily writes require complete 12-stock watchlist coverage before writing `daily_signal_snapshot`, `daily_price`, `signal_runs`, or `signal_items`.
- Files changed:
  - `core/watchlist.py`
  - `core/generator.py`
  - `services/daily_snapshot_store.py`
  - `services/signal_store.py`
  - `tests/test_daily_snapshot_store.py`
  - `docs/qa_handoff_log.md`
- Test level: L2
- Scope: snapshot / DB / backfill / formatter warning
- Minimal validation run:
  - `.venv/bin/python -m pytest tests/test_daily_snapshot_store.py`
  - `.venv/bin/python -m pytest`
  - `.venv/bin/python scripts/dry_run_replay.py --dry-run --validate --source synthetic --version v19.3.1 --start-date 2026-05-18 --end-date 2026-05-22`
  - `.venv/bin/python scripts/backfill_signals.py --dry-run --source synthetic --version v19.3.1 --start-date 2026-05-18 --end-date 2026-05-22`
- Skipped tests:
  - Formal backfill write
  - Live Telegram delivery
  - Live Supabase write verification
  - TWSE live replay/backfill rerun
- Reason for skipping: Requirement explicitly avoids formal backfill writes; blocker fix is guarded by unit tests and synthetic replay/backfill dry-run, while live external-service checks are reserved for QA regression.
- External services touched: none
- DB/schema/write risk: yes
- QA focus:
  - Confirm complete 12-stock results write both signal and price payloads.
  - Confirm missing one watchlist code returns `recorded=False`, reason `incomplete_watchlist`, and empty `price_rows` / `signal_rows`.
  - Confirm `record_daily_signals()` also skips before creating `signal_runs` / `signal_items` when watchlist coverage is incomplete.
  - Confirm Telegram report appends a warning like `每日快照未寫入：缺少 2421, 3035` when daily coverage is incomplete.
  - Confirm holding stocks still cannot become `is_tradeable` or `is_best_candidate`.

### Change 2
- Summary: Routed daily write warnings into the default Telegram summary message so incomplete-watchlist warnings appear in the first of the standard three messages, not only in the full detail text.
- Files changed:
  - `core/generator.py`
  - `tests/test_generator_report.py`
  - `docs/qa_handoff_log.md`
- Test level: L1
- Scope: formatter / Telegram / DB warning display
- Minimal validation run:
  - `.venv/bin/python -m pytest tests/test_generator_report.py`
- Skipped tests:
  - Full regression test suite
  - Replay/backfill dry-run
  - Live Telegram delivery
  - Live Supabase write verification
  - TWSE live fetch
- Reason for skipping: Display plumbing only; DB guard behavior was already validated in batch-003 Change 1, and this change only passes the existing warning into the default summary formatter.
- External services touched: none
- DB/schema/write risk: no
- QA focus:
  - Confirm default three-message Telegram output includes `每日快照未寫入` in the first summary message when `missing_stock_ids` is returned.
  - Confirm the warning is not hidden in detail-only content.
  - Confirm standard holding/unheld detail messages remain unchanged.

## 2026-05-26 - batch-004

### Change 1
- Summary: Added Yahoo daily K-line fallback for online report generation when TWSE daily K-line requests time out or return no usable daily rows. The existing Yahoo/realtime fallback only covered live price; this change lets strategy generation continue only when fallback daily closes/volumes are available.
- Files changed:
  - `services/stock_api.py`
  - `core/generator.py`
  - `tests/test_generator_report.py`
  - `tests/test_stock_api_history.py`
  - `docs/qa_handoff_log.md`
- Test level: L1
- Scope: data source / formatter error path / Telegram
- Minimal validation run:
  - `.venv/bin/python -m pytest tests/test_generator_report.py tests/test_stock_api_history.py`
- Skipped tests:
  - Full regression test suite
  - Live Telegram delivery
  - Live Supabase write verification
  - Live TWSE/Yahoo network smoke test
  - Replay/backfill dry-run
- Reason for skipping: Targeted data-source fallback fix with mocked local tests; live provider behavior should be verified by QA in networked regression.
- External services touched: none
- DB/schema/write risk: no
- QA focus:
  - Simulate TWSE timeout and confirm Yahoo daily fallback produces usable closes/volumes.
  - Confirm report only shows `無有效數據` when both TWSE daily and Yahoo daily fallback fail.
  - Confirm daily snapshot DB guard still blocks writes if fallback does not cover all 12 stocks.
  - Confirm fallback OHLCV and price source are marked `yahoo` when used.

### Change 2
- Summary: Added product-facing v19.4 strategy diagnosis document for 2026-05-26 intraday data-source, unheld blocker, and holding-state review.
- Files changed:
  - `docs/v19_4_strategy_diagnosis_2026-05-26.md`
  - `docs/qa_handoff_log.md`
- Test level: L0
- Scope: docs / strategy diagnosis
- Minimal validation run:
  - Manual document creation check.
- Skipped tests:
  - Unit tests
  - Full regression test suite
  - Live Telegram delivery
  - Live Supabase write verification
  - TWSE/Yahoo network smoke test
- Reason for skipping: Documentation-only output from diagnostic analysis; no code path changed.
- External services touched: none
- DB/schema/write risk: no
- QA focus:
  - Confirm the diagnosis document is present and readable.
  - Confirm no implementation change is implied by this documentation-only commit.

### Change 3
- Summary: Implemented v19.3.2 corrective patch for 2026-05-26 intraday report: added top-level data-source transparency, RR hidden-reason text, four-way unheld grouping, differentiated holding labels, and narrow holding-signal branch fixes for high-profit pullback, weak/far holdings, and light-loss weak pullback.
- Files changed:
  - `core/generator.py`
  - `services/analysis.py`
  - `tests/test_analysis_engine.py`
  - `tests/test_generator_report.py`
  - `docs/qa_handoff_log.md`
- Test level: L2
- Scope: formatter / Telegram / strategy / holding / RR
- Minimal validation run:
  - `.venv/bin/python -m pytest tests/test_analysis_engine.py tests/test_generator_report.py`
- Skipped tests:
  - Full regression test suite
  - Replay/backfill dry-run
  - Live Telegram delivery
  - Live Supabase read/write verification
  - Live TWSE/Yahoo network smoke test
- Reason for skipping: v19.3.2 intentionally scoped to Telegram display semantics and limited holding-signal branches; no DB schema, write path, backfill path, or provider request logic changed. Full regression and live services remain QA batch responsibilities.
- External services touched: none
- DB/schema/write risk: no
- QA focus:
  - Confirm Telegram version shows `v19.3.2`, not `v19.4`.
  - Confirm intraday summary displays `資料：即時價 realtime｜日線 yahoo` or `mixed` when sources differ.
  - Confirm hidden RR displays contextual text such as `持倉不看新倉RR`, `過熱`, `弱勢`, `量能不足`, or `遠離觸發`.
  - Confirm unheld stocks split into `禁止追高`, `等待冷卻`, `可觀察但不可買`, and `弱勢淘汰`, with non-buy headings no longer all shown as `⛔ 不買`.
  - Confirm holding summary/detail labels differentiate `核心續抱`, `洗盤續抱`, `洗盤警戒`, `續抱觀察`, and `風控觀察`.
  - Confirm no DB schema or daily write/backfill behavior changed.

### Change 4
- Summary: Optimized online daily report data requests so intraday/daily Telegram generation only requests the minimum 20 daily rows required by strategy, avoids the previous 4-month TWSE monthly scan, and skips Yahoo quote lookup when realtime price is already usable.
- Files changed:
  - `core/generator.py`
  - `tests/test_generator_report.py`
  - `docs/qa_handoff_log.md`
- Test level: L1
- Scope: data source / Telegram / performance
- Minimal validation run:
  - `.venv/bin/python -m pytest tests/test_generator_report.py tests/test_stock_api_history.py`
  - Local timing probe: 12-stock quote scan dropped from about 55s to about 2.1s in the current environment.
- Skipped tests:
  - Full regression test suite
  - Replay/backfill dry-run
  - Live Telegram delivery
  - Live Supabase write verification
  - Formal TWSE/Yahoo provider regression
- Reason for skipping: Targeted online report request optimization; replay/backfill historical fetch paths and DB write logic were not changed. Live provider variability should be confirmed by QA/network smoke.
- External services touched: Yahoo / TWSE during local timing probe
- DB/schema/write risk: no
- QA focus:
  - Confirm online report still covers all 12 stocks.
  - Confirm each stock uses `months=1`, `min_rows=20` Yahoo daily when sufficient.
  - Confirm TWSE fallback is limited to `months=1`, `max_months=2`, `min_rows=20`.
  - Confirm realtime price source remains `realtime` and no extra Yahoo quote request is made when realtime succeeds.
  - Confirm replay/backfill behavior remains unchanged.
