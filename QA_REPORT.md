# QA_REPORT: low_repair_intraday_buy_v21_1_20260622

## Test Scope

- Low-repair executable transition.
- User-visible unheld card wording.
- Summary execution bridge and new-entry suggestion.
- Negative source-evidence path.
- Official dry-run safety.

## Risk Scan

- DB schema change: none.
- DB write / backfill / delete: none.
- Live Telegram: none.
- Strategy risk: limited to low-repair candidates that already satisfy DB-backed support, 5-day MA, volume, and risk/reward checks.
- Failure mode checked: condition-complete card remains non-actionable forever.

## Cross-Block Semantic Checks

- Intraday complete low-repair card can become `可買`.
- After-hours complete low-repair card remains `可準備`.
- Summary no longer says no buy exists when a low-repair intraday buy is present.
- Source-ineligible cases do not become buy recommendations.

## Failure Specimen Rebuttal

- Owner question: "都滿足是可準備，那到底什麼時候會進入可買?"
- Answer in behavior:
  - `盤中` + DB-backed checklist complete + source eligible -> `可買｜小倉`
  - `盤後` / `收盤` + checklist complete -> `可準備`
  - source incomplete -> not `可買`

## Commands And Results

- `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q -k "low_repair" --tb=short`
  - result: `4 passed, 213 deselected`
- `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q -k "low_repair or unheld_funnel or postmarket_unheld_gate or next_day_confirmation or trend_continuation or confirmed_evidence_near_boundary" --tb=short`
  - result: `17 passed, 200 deselected`
- Manual source-negative probe:
  - result: no `可買｜小倉`
- Official dry-run:
  - result: `messages=4`, no live Telegram

## Not Tested

- Live Telegram delivery.
- Production DB write/read-after-write, because this task had no DB writes.
- Full all-test repository sweep.

## QA Conclusion

conditional pass.

The requested low-repair transition is fixed and covered at helper, formatter, summary, and dry-run levels. Conditional because full repository-wide tests were not rerun in this final follow-up.
