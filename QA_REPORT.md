# QA_REPORT: rr_context_standardization_v21_1_20260615

## Test Scope

- RR formula component generation in strategy output.
- Snapshot and signal-item persistence payloads for typed RR fields.
- Backfill payload compatibility.
- Telegram formatter/generator wording for high RR but blocked setup.
- Official generator dry-run with no live Telegram delivery.

## Risk Scan

- A high RR number can mislead the user into thinking a stock is buyable.
- RR不足 must remain visibly insufficient and not be hidden as theoretical.
- Schema extension must not break runner before Owner applies migration.
- Helper-level tests are not enough; final message list must be replayed.

## Cross-Block Semantic Consistency

- Unheld card state, blocker, `量化差距`, `補充`, and summary now agree:
  - `等型態` / quality D: high RR is theoretical.
  - `等回測` / sharp rebound: high RR is only reference until retest confirms.
  - `等RR修復`: low RR is shown as the blocker.
- No card converts `理論RR` into a buy recommendation.

## User Misread Risk

- Reduced: report no longer says `RR 達標` for non-actionable high RR.
- Remaining: target-basis choice is still a strategy assumption, so the new DB fields are needed for later calibration and audit.

## Failure Specimen Countercheck

- Owner-style dry-run report was replayed through official `generate_report(dry_run=True)`.
- `旺宏 2337` is still not buyable, but now explains: waiting for retest, current high RR is theoretical/reference only.
- `緯創 / 仁寶 / 技嘉` no longer display high RR as actionable evidence while quality/setup is D.

## Evidence

- `263 passed, 147 warnings, 44 subtests passed`.
- Official dry-run generated 4 messages, no live delivery.
- Dry-run confirmed `理論RR` wording on non-actionable high RR cards and normal `RR` wording on RR不足 card.
- Production DB verification after Owner-applied schema and approved-script backfill:
  - `daily_signal_snapshot`: 5786 rows, all `v21.1`.
  - RR component missing rows: 0.
  - exact duplicate groups: 0.
  - old-version overlap rows: 0.
  - prune dry-run delete candidates: 0.
  - warmup daily_price rows written: 664.

## Not Tested

- Live Telegram delivery.
- Next scheduled GitHub/Render runner artifact after push.
- Historical `signal_items` reconstruction.

## QA Conclusion

conditional pass

Reason: repo code, tests, official dry-run, production schema read, approved backfill, and duplicate audit pass. Live Telegram delivery was intentionally not performed, and the next scheduled runner artifact still needs observation.
