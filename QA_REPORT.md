# QA_REPORT: strategy_feature_persistence_v21_1_20260615

## Test Scope
- v21.1 strategy-feature snapshot payload.
- Daily after-close `daily_signal_snapshot` writer payload and schema fallback.
- Guarded `backfill_signals.py` payload and schema fallback.
- `signal_items` report item payload.
- V20-first volume calibration.
- Official generator dry-run.
- Backfill dry-run with synthetic and TWSE sources.
- v21.1 unheld Telegram card readability for waiting / rejected tracking states.

## Risk Scan
- If fields are only inside Telegram text, later calibration cannot prove whether V20 / resistance / retest gates worked.
- If fields are only inside raw JSON, DB queries and QA probes become fragile.
- If schema is not applied yet and runner writes new fields unguarded, the scheduled report path can crash.
- If backfill uses a short window, 60D resistance and outcome calibration are not reliable.

## Cross-block Semantic Consistency
- `daily_signal_snapshot`, `signal_items`, backfill rows, raw_result, and volume calibration now use the same strategy-feature names.
- Full OHLCV arrays are not stored in raw_result; OHLCV remains in `daily_price`.
- V20 is used for calibration buckets first, with legacy `volume_ratio` fallback only when V20 is missing.
- Backfill recommendation is 730 calendar days plus 120-day warmup.
- Unheld waiting-card explanations now use the same evidence shape when the fields exist; `急彈待回測` no longer has an exclusive richer display path.
- Redundant no-decision lines are suppressed only when they repeat internal "not applicable" evidence already represented in `量化差距`.

## Failure Specimen Countercheck
- Previous failure: v21.1 report had richer strategy context but durable DB rows did not have typed V20 / resistance / retest-zone features.
- Countercheck:
  - daily snapshot test confirms payload includes `volume_ratio_20`, `resistance_20`, `breakout_price_20`, `retest_zone_low`, and `raw_result`.
  - backfill test confirms historical rows include the same fields.
  - fallback tests confirm missing production columns do not crash the writer path.
- Owner report failure: `旺宏` showed detailed retest / V10/V20 / quality / RR evidence, but other unheld states only showed generic blockers and noisy internal lines.
- Countercheck:
  - `tests/test_unheld_gap_format.py` verifies `等型態` now shows quality, breakout zone, distance, V10/V20, and RR context.
  - The same test verifies the `急彈待回測` branch still preserves retest-zone, V10/V20, quality, RR, and unlock wording.
  - `tests/test_generator_report.py` guards the official generator report path against broad formatter regressions.

## Additional Challenge
- Ran a guarded TWSE dry-run backfill:
  - `daily_price rows: 3`
  - `daily_signal_snapshot rows: 3`
  - `VALIDATION OK`
  - `DRY RUN ONLY: no database writes`
- Official generator dry-run returned:
  - `VERSION v21.1`
  - `messages 4`
  - `write_results None`
- Report readability regression returned:
  - `205 passed, 147 warnings, 44 subtests passed`

## Not Tested
- Live Telegram delivery.
- Live Supabase SQL migration execution.
- Live production DB write/backfill.
- Live Telegram delivery of the report readability change.

## QA Conclusion
conditional pass

Reason: repo implementation, migration artifact, payloads, fallbacks, and dry-run/backfill routes pass locally; production completion still requires manually applying `db/sql/v21_1_strategy_feature_snapshot_columns.sql` and then running approved backfill/write commands.

Evidence:
- `19 passed` focused persistence/backfill/calibration tests.
- `334 passed, 149 warnings, 57 subtests passed` targeted strategy/report/backfill suite.
- Official generator dry-run produced `v21.1` without live write/delivery.
- TWSE backfill dry-run produced valid rows without DB writes.
- `205 passed, 147 warnings, 44 subtests passed` for unheld formatter and generator report regression.
