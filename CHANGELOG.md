# CHANGELOG: intraday_low_repair_buy_state_sync_v21_1_20260622

## Changes

- Updated `presentation/report.py`
  - Low-repair intraday executable cards now override stale generic state-machine text.
  - When `low_repair_actionable` is true, the state line becomes:
    `交易狀態：可買｜動作：小倉試單｜條件：守支撐/5日均，不追價`
  - After-hours / close low-repair prepare cards now use a concrete next-session trigger:
    `明日觸發：開盤不追高；守支撐/5日均 + 量能不失控，小倉確認`

- Updated `tests/test_generator_report.py`
  - Added regression assertions that intraday low-repair buy cards cannot still show `交易狀態：等資料` or `還差：資料恢復`.
  - Added regression assertion for the after-hours low-repair open-confirmation trigger.

## Contract Impact

- No DB contract change.
- No version header bump; report remains `v21.1`.
- Intraday low-repair now has an internally consistent executable display:
  - title, state, buy line, and trigger all say small-position buy is allowed only under support / 5-day MA / no-chase conditions.
- After-hours low-repair remains preparation only.

## Direct Consumers Synced

- `formatTelegramMessages` output.
- Telegram unheld stock card.
- Summary behavior from the previous low-repair executable route remains unchanged.

## Verification

- Targeted low-repair tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q -k "low_repair" --tb=short`
  - result: `4 passed, 213 deselected`
- Broader related report tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q -k "score_source or evidence_modifier or supporting_evidence or low_repair or unheld_funnel or postmarket_unheld_gate" --tb=short`
  - result: `14 passed, 203 deselected, 2 subtests passed`
- Official dry-run:
  - `generate_report(dry_run=True)`
  - result: `messages=4`, `live_telegram=False`

## Not Changed

- No production DB write.
- No live Telegram.
- No schema, RLS, grant, policy, role, index, or constraint change.

## Residual Risk

- Full repository-wide test suite was not rerun.
- Local `.pytest_cache` still emits a Windows permission warning; tests pass despite the warning.
