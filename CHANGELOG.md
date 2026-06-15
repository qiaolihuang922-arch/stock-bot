# CHANGELOG: strategy_readability_audit_v21_1_20260615

## Changes

- Updated `presentation/report.py` final Telegram wording so evidence is strategy-aware instead of fixed text replacement:
  - `等型態` potential reward says the blocker is type/quality.
  - `等回測` potential reward says the blocker is missing retest confirmation.
  - `淘汰 / 弱反彈` potential reward says the blocker is weak rebound not yet turning strong.
  - `可準備` basis says open confirmation is still required.
- Normalized other visible shorthand:
  - `setup` -> `買點型態` in explanation lines only, without changing stock titles.
  - `V10 / V20` -> `10日量 / 20日量`.
  - `品質B以上` and `風險報酬>=1.5` now include readable spacing.
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
- Non-actionable high values now display the active strategy blocker, e.g. `潛在報酬：好（9.94倍），但型態/品質未過`.

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
  Result: unheld message shows state-aware potential reward wording and no visible `setup / V10 / V20 / 理論RR`; no live Telegram delivery.

## Covered Layers

- Formatter helper: covered by `tests/test_unheld_gap_format.py`.
- Official generator / message list: covered by `tests/test_generator_report.py` and dry-run.
- Runner/live Telegram: not executed by design.
- Production source / DB: not touched.

## Residual Risk

- The report still includes numeric evidence because it is material to buy/no-buy decisions. Future work may further shorten cards, but this patch keeps evidence tied to the strategy blocker.
