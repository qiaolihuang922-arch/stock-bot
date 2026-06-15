# QA_REPORT: premarket_phase_report_v21_0_6_20260615

## Test Scope
- Trading-day pre-open phase classification.
- Telegram header and summary wording for `盤前`.
- Regression risk for existing `盤中` wording.
- Official generator dry-run path with patched time.

## Risk Scan
- Fixing `非交易` by forcing everything to `盤中` would be misleading.
- Treating `盤前` like `盤後` would keep wrong `明日計畫` wording.
- Changing generic intraday suffixes could break existing phone-readable `盤中` reports.
- A single-date hard-code would fail the next trading day.

## Semantic Consistency
- `盤前`: same trading day, preparation/observation semantics.
- `盤中`: live intraday semantics, unchanged.
- `盤後` / `收盤`: next open / tomorrow confirmation semantics.
- `假日`: non-trading semantics.

## Failure Specimen Countercheck
- Owner pasted `06/15 非交易｜v21.0.5`.
- Countercheck with patched 2026-06-15 08:00:
  - generated headers: `【06/15 盤前｜v21.0.6】`;
  - `phase 盤前`;
  - no `06/15 非交易`;
  - no `明日計畫`.

## Additional Challenge
- Full targeted suite first failed when `盤中` wording regressed from `今日盤中風控建議` to `今日風控建議`.
- The regression was fixed by preserving the old `盤中` suffix and only adding a separate `盤前` suffix.

## Not Tested
- Live Telegram delivery.
- Production DB write/backfill.
- Official holiday API confirmation beyond the existing source/evidence paths.

## QA Conclusion
通過

Evidence:
- `2 passed` targeted phase tests.
- `248 passed, 147 warnings, 57 subtests passed` targeted report/state/evidence suite.
- Official dry-run probe produced `盤前` headers and no `明日計畫`.
