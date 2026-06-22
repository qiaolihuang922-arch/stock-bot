# QA_REPORT: low_repair_remove_meaningless_source_gate_v21_1_20260622

## Test Scope

- Low-repair executable transition.
- User-visible unheld card wording.
- Summary execution bridge and new-entry suggestion.
- Missing context, strategy evidence source-error, and core price source-error paths.
- Official dry-run safety.

## Risk Scan

- DB schema change: none.
- DB write / backfill / delete: none.
- Live Telegram: none.
- Strategy risk: limited to low-repair candidates that already satisfy DB-backed support, 5-day MA, volume, and risk/reward checks.
- Failure mode checked: meaningless source gate blocks an otherwise complete DB-backed low-repair route.

## Cross-Block Semantic Checks

- Intraday complete low-repair card can become `可買`.
- After-hours complete low-repair card remains `可準備`.
- Summary no longer says no buy exists when a low-repair intraday buy is present.
- Missing strategy context does not block low-repair buy.
- Strategy evidence source-error does not block a DB-backed setup.
- Core price source-error does not become a buy recommendation.

## Failure Specimen Rebuttal

- Owner question: "資料來源可信又是什麼，目前不是沒作用嗎?"
- Answer in behavior:
  - `盤中` + DB-backed checklist complete + no core market-data source-error/conflict -> `可買｜小倉`
  - `盤後` / `收盤` + checklist complete -> `可準備`
  - strategy evidence source-error -> evidence unavailable, not a trade blocker
  - core price / OHLCV / RR source-error or conflict -> not `可買`

## Commands And Results

- `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q -k "low_repair" --tb=short`
  - result: `4 passed, 213 deselected`
- `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q -k "low_repair or unheld_funnel or postmarket_unheld_gate or next_day_confirmation or trend_continuation or confirmed_evidence_near_boundary" --tb=short`
  - result: `17 passed, 200 deselected`
- Evidence/source split case:
  - strategy evidence source-error still allowed DB-backed low-repair `可買｜小倉`
  - core price source-error did not produce `可買｜小倉`
- Official dry-run:
  - result: `messages=4`, no live Telegram

## Not Tested

- Live Telegram delivery.
- Production DB write/read-after-write, because this task had no DB writes.
- Full all-test repository sweep.

## QA Conclusion

conditional pass.

The meaningless source gate has been removed from the low-repair route. Strategy evidence is auxiliary; core market-data source failure still fails closed. Conditional because full repository-wide tests were not rerun in this follow-up.
