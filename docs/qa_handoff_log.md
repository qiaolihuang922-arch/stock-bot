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
