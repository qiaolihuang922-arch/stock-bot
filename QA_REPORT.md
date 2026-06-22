# QA_REPORT: intraday_low_repair_buy_state_sync_v21_1_20260622

## Test Scope

- Intraday low-repair executable unheld card.
- After-hours low-repair prepare card.
- Related report-state and source/evidence regression subset.

## Risk Scan

- Strategy risk: the change touches user-visible buy/prepare wording for low-repair candidates.
- DB risk: none; no schema or data write.
- Live delivery risk: none; Telegram delivery was not run.
- User misunderstanding risk checked: card title, state line, buy line, and trigger must not disagree.

## Cross-Block Semantic Consistency

- Intraday complete low-repair:
  - title says `可買｜小倉`
  - state says `可買｜小倉試單`
  - buy line says `可買｜低位修復小倉`
  - trigger says `守支撐/5日均 + 量能不失控，小倉試單`
- After-hours complete low-repair:
  - remains `可準備`
  - trigger explains next-session confirmation, not immediate buy.

## Failure Specimen Rebuttal

- Owner concern: after-hours handling was fixed, but intraday might still be unclear.
- Rebuttal result:
  - the formatter-level intraday low-repair card is now explicitly executable when the low-repair gate is ready.
  - stale generic state text `等資料` is explicitly blocked by regression tests.

## Commands And Results

- `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q -k "low_repair" --tb=short`
  - result: `4 passed, 213 deselected`
- `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q -k "score_source or evidence_modifier or supporting_evidence or low_repair or unheld_funnel or postmarket_unheld_gate" --tb=short`
  - result: `14 passed, 203 deselected, 2 subtests passed`
- `generate_report(dry_run=True)`
  - result: `messages=4`, `live_telegram=False`

## Not Tested

- Live Telegram delivery.
- Production DB write/read-after-write, because this task did not write DB data.
- Full repository-wide test suite.

## QA Conclusion

conditional pass.

The visible intraday contradiction is covered at the formatter/report-card layer. Conditional because this was a focused risk patch, not a full repository test sweep.
