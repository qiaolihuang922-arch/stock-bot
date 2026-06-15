# CHANGELOG: rr_wording_readability_v21_1_20260615

## Changes

- Updated `presentation/report.py` final Telegram wording so risk/reward shorthand is readable:
  - `RR` becomes `風險報酬`.
  - `理論RR` becomes `理論風險報酬`.
  - `等RR修復` becomes `等風險報酬`.
  - `RR不足` becomes `風險報酬不足`.
- Updated `core/generator.py` helper and funnel display labels to avoid exposing `等RR修復` in summaries.
- Updated formatter and official generator tests to lock the new visible wording.

## Contract Impact

- Telegram report wording changes only.
- No payload shape change.
- No strategy threshold or decision change.
- No DB schema or persistence change.
- No live Telegram delivery.
- Version remains `v21.1`.

## Direct Consumer Sync

- `core.generator.generate_report(dry_run=True)` now prints unheld cards and summaries with `風險報酬` wording.
- Internal state-machine values are still compatible with existing code paths.
- Theoretical values still display as non-actionable reference, e.g. `理論風險報酬 9.94僅參考`.

## Verification

- Formatter/generator regression:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests\test_unheld_gap_format.py tests\test_generator_report.py -q --tb=short
  ```
  Result: `205 passed, 147 warnings, 44 subtests passed`.
- Official generator dry-run:
  ```powershell
  $env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages,_=generate_report(dry_run=True); print(messages[1]); print('\n--- SUMMARY ---\n'); print(messages[2])"
  ```
  Result: unheld message shows `等風險報酬`, `風險報酬不足`, `理論風險報酬`; no live Telegram delivery.

## Covered Layers

- Formatter helper: covered by `tests/test_unheld_gap_format.py`.
- Official generator / message list: covered by `tests/test_generator_report.py` and dry-run.
- Runner/live Telegram: not executed by design.
- Production source / DB: not touched.

## Residual Risk

- The report still includes numeric risk/reward evidence because it is material to buy/no-buy decisions. Future work may add a legend or glossary, but this patch keeps the evidence inline and readable.
