# CHANGELOG: low_repair_remove_meaningless_source_gate_v21_1_20260622

## Changes

- Updated `core/generator.py`
  - Removed the meaningless `strategy source must be available` requirement from the low-repair buy route.
  - Added explicit core market-data source-error / unresolved-conflict blocking only.
  - Missing source decision context or insufficient strategy sample no longer blocks DB-backed low-repair readiness.
  - Removed the vague `資料來源未完整，暫不升格可買` low-repair fallback.
  - `_unheld_decision_source_eligible` now checks stock decision data health, not strategy sample availability.

- Updated `presentation/report.py`
  - Low-repair intraday buy cards render as `🟢 可買｜小倉｜低位修復成立`.
  - Buy line says `守支撐/5日均，不追價`.
  - Data line says the low-repair condition is established, without stale generic `不適用` / source wording.
  - Core data source-error intraday cases do not display a buy-ready title.

- Updated `tests/test_generator_report.py`
  - Updated positive coverage so low-repair intraday buy does not require strategy evidence summary.
  - Added evidence/source split coverage: strategy evidence source-error does not block, core price source-error blocks.

## Contract Impact

- User-visible Telegram report state can now move from low-repair `可準備` to intraday `可買`.
- `可買` is intentionally small-position only and non-chasing.
- Low-repair uses its own DB-backed condition set; generic strategy sample availability is not a user-facing blocker.
- Strategy evidence remains confidence / display evidence. It does not create standalone buys and does not veto DB-backed setups.
- No DB contract change.
- No version header bump; report remains `v21.1`.

## Verification

- Targeted low-repair tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q -k "low_repair" --tb=short`
  - result: `4 passed, 213 deselected`
- Broader related report tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q -k "low_repair or unheld_funnel or postmarket_unheld_gate or next_day_confirmation or trend_continuation or confirmed_evidence_near_boundary" --tb=short`
  - result: `17 passed, 200 deselected`
- Evidence/source split case:
  - strategy evidence `source-error` still allowed DB-backed low-repair `可買｜小倉`
  - core price `source-error` did not produce `可買｜小倉`
- Official dry-run:
  - `generate_report(dry_run=True)`
  - result: `messages=4`, no live Telegram
  - because current run was after-hours, low-repair-ready candidates remain `可準備`, not `可買`

## Not Changed

- No production DB schema or data.
- No live Telegram.
- No unrelated future-watch source behavior.

## Residual Risk

- `.pytest_cache` may still warn with local Windows permission error; test results are unaffected.
- Full repository-wide test suite was not rerun in this follow-up cycle.
