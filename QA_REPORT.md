# QA_REPORT: limit_lock_primary_reason_v21_1_20260622

## Test Scope

- Limit-lock / limit-rebound unheld funnel priority.
- User-visible unheld card wording.
- Mobile readability replay for structure-failure priority.
- Related low-repair and evidence-source regressions.

## Risk Scan

- Strategy risk: touches visible state priority for unheld candidates.
- DB risk: none; no schema or data write.
- Live delivery risk: none; Telegram delivery was not run.
- User misunderstanding risk checked: lock-up cards must not show RR or score as the main blocker.

## Cross-Block Semantic Consistency

- Locked / overheated names:
  - title says wait for retest / no chase.
  - body says wait for unlock and retest hold.
  - no RR / quality / score data line appears as the active blocker.
- Failed breakout:
  - remains structure-led and does not get softened into wait-retest only because it is limit-like.

## Failure Specimen Rebuttal

- Owner concern: 06/22 after-hours cards mixed lock-up, RR, quality, and data-score reasons.
- Rebuttal result:
  - lock-up now owns the visible primary reason.
  - RR / quality are not shown while lock-up is the active reason.
  - open / cooling / retest is the next actionable condition.

## Commands And Results

- `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q -k "limit_lock or limit_up or overheat or low_repair or unheld_funnel or mobile or confirmed_evidence_preserves_limit or score_source or supporting_evidence" --tb=short`
  - result: `24 passed, 193 deselected, 2 subtests passed`
- `generate_report(dry_run=True)`
  - result: `messages=4`, `live_telegram=False`

## Not Tested

- Live Telegram delivery.
- Production DB write/read-after-write, because this task did not write DB data.
- Full repository-wide test suite.

## QA Conclusion

conditional pass.

The visible lock-up primary reason is now consistent at the funnel and formatter layers. Conditional because this was a focused regression pass, not a full repository sweep.
