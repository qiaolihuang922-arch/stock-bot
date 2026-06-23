# QA_REPORT: intraday_user_view_state_readability_v21_1_20260623

## Test Scope

- Overheat card semantics when price is still strong vs already pulling back.
- Low-repair card compactness and missing-condition clarity.
- Rejected-card history contradiction.
- Official dry-run message-list rendering.

## Risk Scan

- Strategy risk: medium. This changes user-visible state wording but not the underlying buy/sell engine.
- DB risk: none. Read-only dry-run only.
- Live delivery risk: none. Telegram send was not run.
- User misunderstanding risk checked:
  - no longer tells a sharply falling overheated stock to simply wait for cooling.
  - low repair now says the actual missing level instead of repeating route text.
  - rejected cards no longer show positive repair history.

## Cross-Block Semantic Consistency

- Positive overheat:
  - title/body remain cooling / no-chase.
- Pullback overheat:
  - title/body both say wait for retest confirmation.
- Low repair:
  - route, observation, missing condition, and effective buy point point to the same support / MA source.
- Rejected:
  - no positive `修復中 / 權重 +1` line under an eliminated card.

## Failure Specimen Rebuttal

- Owner specimen: 06/23 intraday report.
- Rebuttal from dry-run:
  - 南亞科 changed to `等回測｜急殺回測`.
  - 華邦電 changed to `等回測｜回測確認`.
  - 緯創 / 仁寶 now show `近期支撐`, `5日均`, `量能`, and only the actual missing `站回5日均`.
  - 光寶科 rejected card no longer displays repair history in the dry-run excerpt.

## Commands And Results

- `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q -k "overheat_pullback or overheat_sharp or low_repair_compact or rejected_card_suppresses" --tb=short`
  - result: `4 passed, 217 deselected`
- `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q -k "overheat or low_repair or cooldown or retest or rejected or mobile" --tb=short`
  - result: `25 passed, 196 deselected`
- `.\.venv\Scripts\python.exe -c "from core.generator import generate_report; generate_report(dry_run=True)"`
  - result: `messages=4`, no live send.

## Not Tested

- Live Telegram delivery.
- Production DB write/read-after-write.
- Full repository green state.

## Full-Test Note

- Full `tests/test_generator_report.py` was run once.
- Result: `213 passed, 11 failed`.
- Failures are stale / broader contract expectations outside this focused fix, including old source-error wording, old retest wording, old industry/source lines, and future-watch live source count expectations.
- These are recorded as residual debt, not as passing evidence.

## QA Conclusion

conditional pass.

The 06/23 user-visible failure path is fixed in focused tests and official dry-run output. Conditional because the full legacy report test file is not green and needs a separate cleanup/calibration cycle.
