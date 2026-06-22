# CHANGELOG: limit_lock_primary_reason_v21_1_20260622

## Changes

- Updated `core/generator.py`
  - `LIMIT_LOCK` / `漲停不追` now promotes to `等回測` before RR-based waiting states.
  - `LIMIT_REBOUND` / `漲停反彈待確認` now promotes to `隔日確認` before RR-based waiting states.
  - Failed breakout / structural failure remains higher priority than lock-up display.

- Updated `presentation/report.py`
  - Added one display helper for limit-like states.
  - Limit-lock cards now render:
    - `狀態：漲停/過熱，不追價`
    - `等待：解除鎖定後，看開板回測是否守住`
    - `有效買點：開板/降溫 + 回測不破 + 非追高`
  - Limit-like cards suppress irrelevant RR / quality / score data lines.
  - Limit-like cards no longer use generic `缺口：解除鎖定後再評估`.

- Updated `tests/test_generator_report.py`
  - Added negative assertions so limit-lock cards cannot show `等風險報酬`, `數據：風險報酬`, or score noise.
  - Updated expected lock-up wording to the new mobile-readable contract.

## Contract Impact

- User-visible report state changes for lock-up names:
  - from mixed `等風險報酬｜漲停不追`
  - to clear `等回測｜漲停不追`
- No DB contract change.
- No version header bump; report remains `v21.1`.

## Direct Consumers Synced

- Telegram unheld cards.
- Unheld funnel state counts for lock-up names.
- Mobile readability replay tests.

## Verification

- Related report tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q -k "limit_lock or limit_up or overheat or low_repair or unheld_funnel or mobile or confirmed_evidence_preserves_limit or score_source or supporting_evidence" --tb=short`
  - result: `24 passed, 193 deselected, 2 subtests passed`
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
