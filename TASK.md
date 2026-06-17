# TASK: report_state_sync_v21_1_20260617

## Task Status

- task_id: `report_state_sync_v21_1_20260617`
- task_type: `risk_patch`
- status: `implemented`
- version_contract: runtime report remains `v21.1`
- QA level: L3

## Owner Problem

Owner pasted the `06/17 收盤｜v21.1` report and asked to repair it with the correct trading-reader mindset. The report still contains strategy/display conflicts: retest status does not follow price, holding risk wording ignores warning-line breaches, overheat wording says limit-up when the current day is not limit-up, and some waiting states do not tell the reader exactly what condition matters.

## User-Visible Result

- Cards should answer only useful trading questions:
  - Can act now or not?
  - If not, what exact event is being waited for?
  - Has that event already happened, failed, or not happened?
- Retest cards must distinguish `尚未回測`, `回測中守住`, and `回測失守`.
- Holding risk cards must not say `未跌破風控` when current price has breached warning.
- Overheat cards must not mention `漲停` unless the current move is actually near/at limit-up.
- Volume/data waiting cards must avoid tautologies and show concrete missing condition where the data exists.
- Summary must remove non-decision noise and keep only actionable buckets.

## Non-Goals

- No DB schema/RLS/grant/policy/role/index/constraint change.
- No live Telegram delivery.
- No production DB write/backfill/delete in this cycle.
- No broad strategy redesign beyond correcting state/display conflicts for the existing v21.1 strategy.

## Impacted Modules And Consumers

- `presentation/report.py`: user-visible Telegram card formatting and consistency guards.
- `core/generator.py`: summary wording and holding risk text if needed.
- `tests/test_generator_report.py`: regression specimens for the pasted conflict patterns.
- Direct consumer: official `generate_report(dry_run=True)` message list and mobile Telegram reading path.

## Output Contract

For unheld cards:

- `距突破` remains visible.
- `等回測` cards must show a retest basis and whether current price is above/near/below it.
- If current price is below the retest basis beyond tolerance, do not show `尚未回測`; show the retest as failed/失守 and wait for re-entry or new support.
- `等冷卻` cards may say `漲停不追` only when the current day is near/at limit-up; otherwise use `短線過熱，不追價`.
- `等量能` cards must show `目前量能` and the target threshold when available, not only `量能回升後再評估`.
- `等資料` must not be used when DB-backed price/snapshot evidence exists.

For holding cards:

- If `current_price < warning_price <= avg/entry context`, wording must say `跌破警戒，未到停損` or stronger.
- `未跌破風控` may only appear when current price is above warning and stop.

For summary:

- Remove decision-duplicate lines such as detail index and filler.
- Keep market posture, current actionable holding actions, new valid entries, and unheld buckets.

## Failure Specimen And Acceptance Route

Failure specimen is the Owner-pasted `06/17 收盤｜v21.1` report:

- `2337 旺宏`: `回測基準 166.5；尚未回測` while current price is `161.5`, which means the basis was already tested and lost.
- `2421 建準`: current price `144.5`, warning `145.19`, stop `140.60`; wording says `未跌破風控`.
- `2344/2408`: current day is not limit-up, but text still says `漲停/過熱不追`.
- `2303 聯電`: state says `等量能` but output only repeats `量能回升後再評估`.
- Summary contains non-decision filler.

Acceptance route:

1. Add regression tests at formatter/generator level for the above specimens.
2. Patch the official report path, not a synthetic helper only.
3. Run targeted tests and official generator dry-run.
4. Confirm no live Telegram and no DB writes.

## Acceptance Criteria

- Tests prove retest-basis lost is not displayed as `尚未回測`.
- Tests prove holding warning breach is not displayed as `未跌破風控`.
- Tests prove non-limit overheat does not display `漲停/過熱`.
- Tests prove volume waiting gives a concrete missing threshold line where volume data exists.
- Official `generate_report(dry_run=True)` returns messages without the known contradiction patterns.
