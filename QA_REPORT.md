# QA_REPORT: strategy_feature_persistence_v21_1_20260615

## Test Scope
- v21.1 strategy-feature snapshot payload.
- Daily after-close `daily_signal_snapshot` writer payload and schema fallback.
- Guarded `backfill_signals.py` payload and schema fallback.
- `signal_items` report item payload.
- V20-first volume calibration.
- Official generator dry-run.
- Backfill dry-run with synthetic and TWSE sources.

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

## Failure Specimen Countercheck
- Previous failure: v21.1 report had richer strategy context but durable DB rows did not have typed V20 / resistance / retest-zone features.
- Countercheck:
  - daily snapshot test confirms payload includes `volume_ratio_20`, `resistance_20`, `breakout_price_20`, `retest_zone_low`, and `raw_result`.
  - backfill test confirms historical rows include the same fields.
  - fallback tests confirm missing production columns do not crash the writer path.

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

## Not Tested
- Live Telegram delivery.
- Live Supabase SQL migration execution.
- Live production DB write/backfill.

## QA Conclusion
conditional pass

Reason: repo implementation, migration artifact, payloads, fallbacks, and dry-run/backfill routes pass locally; production completion still requires manually applying `db/sql/v21_1_strategy_feature_snapshot_columns.sql` and then running approved backfill/write commands.

Evidence:
- `19 passed` focused persistence/backfill/calibration tests.
- `334 passed, 149 warnings, 57 subtests passed` targeted strategy/report/backfill suite.
- Official generator dry-run produced `v21.1` without live write/delivery.
- TWSE backfill dry-run produced valid rows without DB writes.
