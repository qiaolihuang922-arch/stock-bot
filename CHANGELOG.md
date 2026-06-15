# CHANGELOG: unheld_readability_v21_1_20260615

## Changes

- Updated `presentation/report.py` unheld blocker formatting:
  - added decision-first reason mapping;
  - compacted measurable gaps for RR, quality, breakout/retest zone, volume, heat, source, and sample blockers;
  - replaced the main diagnostic labels with `不能買 / 還差 / 可買條件`;
  - suppressed repetitive `補充` lines except true `依據` lines for prepare-style cards.
- Kept the existing strategy state machine and thresholds unchanged.
- Updated formatter and official generator tests to lock the new mobile-readable contract.

## Contract Impact

- Telegram unheld cards change visible wording only.
- No payload shape change.
- No DB schema or persistence change.
- No live Telegram delivery.
- Version remains `v21.1`.

## Direct Consumer Sync

- `core.generator.generate_report(dry_run=True)` uses the new wording through existing formatter helpers.
- Non-actionable cards still show `買點：不買...` or `不可買...`.
- `可買條件` is treated as future unlock criteria, not a current recommendation.

## Verification

- Formatter/generator regression:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests\test_unheld_gap_format.py tests\test_generator_report.py -q --tb=short
  ```
  Result: `205 passed, 147 warnings, 44 subtests passed`.
- Official generator dry-run:
  ```powershell
  $env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -c "from core.generator import generate_report; messages,_=generate_report(dry_run=True); print(messages[1])"
  ```
  Result: unheld message uses `不能買 / 還差 / 可買條件`; no live Telegram delivery.

## Covered Layers

- Formatter helper: covered by `tests/test_unheld_gap_format.py`.
- Official generator / message list: covered by `tests/test_generator_report.py` and dry-run.
- Runner/live Telegram: not executed by design.
- Production source / DB: not touched.

## Residual Risk

- Some cards still contain several required data points because the strategy state itself has multiple blockers; this patch groups them into readable clauses rather than removing evidence.
- Further reduction should be a separate product decision on which evidence can be hidden, not a formatter-only cleanup.
