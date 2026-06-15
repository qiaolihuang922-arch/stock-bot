# QA_REPORT: strategy_feature_persistence_v21_1_20260615

## Test Scope

- v21.1 strategy-feature snapshot payload and schema fallback.
- Guarded historical backfill payload.
- `signal_items` report-run persistence payload.
- V20-first volume calibration.
- Market/theme evidence automation path under normal `run_mode=bot`.
- Telegram unheld-card readability and standalone breakout-distance display.
- Official generator dry-run with no live Telegram delivery.

## Risk Scan

- Persisted strategy evidence must not exist only inside Telegram text or raw JSON.
- Runner must not crash before/after migration because of schema mismatch.
- Report cards must not hide decision evidence in one special branch while other states show generic blockers.
- `距突破` must be a visible stock-card field and not depend on whether the current strategy branch is breakout, retest, RR repair, cooling, or rejection.
- Readability optimization must be strategy-granular, not a global removal of lines.

## Counterchecks

- Persistence tests confirm daily snapshot/backfill payloads include V20, resistance, breakout price/distance, retest zone, and compact `raw_result`.
- Fallback tests confirm missing production columns do not crash write paths.
- Volume calibration tests confirm V20 is used before legacy `volume_ratio`.
- Report tests confirm:
  - `等型態` and `急彈待回測` expose comparable setup evidence;
  - `距突破：x%｜狀態` appears as a standalone line for holding and unheld cards;
  - `盤面` no longer embeds breakout-distance text.
- Formatter regression confirms cooling cards suppress internal `RR -（過熱）` / `過熱不適用` data noise and show blocker-aware `補充`.
- Dry-run confirms strong rebound holding cards use rebound-continuation next-step wording.
- Official generator dry-run produced v21.1 messages without live delivery.

## Evidence

- `19 passed` focused persistence/backfill/calibration tests.
- `334 passed, 149 warnings, 57 subtests passed` targeted strategy/report/backfill suite.
- `205 passed, 147 warnings, 44 subtests passed` report formatter/generator regression.
- `71 passed, 13 subtests passed` evidence automation tests.
- Dry-run report confirmed standalone `距突破` lines in stock cards.

## Not Tested

- Live Telegram delivery.
- Production runner artifact after the latest push.
- Broker/order execution.

## QA Conclusion

conditional pass

Reason: repo implementation, DB payloads, backfill path, report formatter, and dry-run route pass locally. Final production confidence still requires observing the next scheduled `run_mode=bot` after the after-close safe-write window; no live Telegram delivery was performed.
