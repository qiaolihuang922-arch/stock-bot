# CHANGELOG: intraday_user_view_state_readability_v21_1_20260623

## Changes

- Updated `presentation/report.py`
  - Added `_overheat_contract_parts`.
  - Overheated names now split by current move:
    - still positive / locked: keep cooling / no-chase.
    - pullback `<= -2%`: show `回測中，觀察是否守住`.
    - sharp pullback `<= -8%`: show `急殺回測，先看支撐`.
  - Synced overheat-pullback card titles to `等回測｜回測確認` or `等回測｜急殺回測`.
  - Added `_low_repair_compact_lines` using DB-backed `low_repair_status` values.
  - Suppressed positive repair history on `淘汰` cards.

- Updated `tests/test_generator_report.py`
  - Added regression tests for:
    - normal overheat pullback display.
    - sharp overheat pullback display.
    - compact low-repair missing condition.
    - rejected-card history suppression.
  - Updated low-repair expected wording from verbose checklist to compact actionable lines.

## Contract Impact

- User-visible Telegram card text changes for unheld candidates.
- No payload shape change.
- No DB schema or write contract change.
- Report version remains `v21.1`.

## Direct Consumers Synced

- Official Telegram unheld card formatter.
- Existing report tests that assert low-repair wording.

## Verification

- Focused new tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q -k "overheat_pullback or overheat_sharp or low_repair_compact or rejected_card_suppresses" --tb=short`
  - result: `4 passed, 217 deselected`
- Related report subset:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q -k "overheat or low_repair or cooldown or retest or rejected or mobile" --tb=short`
  - result: `25 passed, 196 deselected`
- Official dry-run:
  - `generate_report(dry_run=True)`
  - result: `messages=4`, no live Telegram delivery.
  - observed 06/23 unheld output:
    - 南亞科: `等回測｜急殺回測`
    - 華邦電: `等回測｜回測確認`
    - 緯創 / 仁寶: compact low-repair missing `站回5日均`

## Not Changed

- No production DB write.
- No live Telegram.
- No schema, RLS, grant, policy, role, index, or constraint change.
- No summary-section redesign in this cycle.

## Residual Risk

- Full `tests/test_generator_report.py` currently has legacy expectation failures unrelated to this focused fix:
  - stale old-copy assertions for source-error, industry, old retest wording, and live future-watch source counts.
  - result observed in full run: `213 passed, 11 failed`.
- Local `.pytest_cache` still emits a Windows permission warning; focused tests pass despite the warning.
