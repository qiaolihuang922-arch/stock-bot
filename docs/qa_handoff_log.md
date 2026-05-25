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
