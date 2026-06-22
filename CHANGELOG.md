# CHANGELOG: low_repair_intraday_buy_v21_1_20260622

## Changes

- Updated `core/generator.py`
  - Added `low_repair_intraday_buy_ready(data, report_context=None)`.
  - Promotes complete low-repair candidates to `可買` only during `盤中`.
  - Keeps complete low-repair candidates as `可準備` outside intraday reports.
  - Fails closed when strategy source evidence is missing, insufficient, source-error, or conflicting.
  - Adds low-repair small-position entries to new-entry suggestions.
  - Updates execution bridge so a real low-repair buy does not still say `新增買點未成立`.

- Updated `presentation/report.py`
  - Low-repair intraday buy cards render as `🟢 可買｜小倉｜低位修復成立`.
  - Buy line says `守支撐/5日均，不追價`.
  - Data line says the low-repair condition is established, without stale generic `不適用` / source wording.
  - Source-ineligible intraday cases do not display a buy-ready title.

- Updated `tests/test_generator_report.py`
  - Added positive coverage for intraday low-repair buy-ready output.
  - Kept existing after-hours coverage for `可準備`.
  - Summary assertion confirms low-repair buy appears in new-entry suggestions and removes `新增買點未成立`.

## Contract Impact

- User-visible Telegram report state can now move from low-repair `可準備` to intraday `可買`.
- `可買` is intentionally small-position only and non-chasing.
- No DB contract change.
- No version header bump; report remains `v21.1`.

## Verification

- Targeted low-repair tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q -k "low_repair" --tb=short`
  - result: `4 passed, 213 deselected`
- Broader related report tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q -k "low_repair or unheld_funnel or postmarket_unheld_gate or next_day_confirmation or trend_continuation or confirmed_evidence_near_boundary" --tb=short`
  - result: `17 passed, 200 deselected`
- Manual source-negative formatter probe:
  - source evidence not eligible did not produce `可買｜小倉`
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
