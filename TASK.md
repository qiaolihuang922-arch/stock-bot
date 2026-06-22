# TASK: limit_lock_primary_reason_v21_1_20260622

## Task Status

- task_id: `limit_lock_primary_reason_v21_1_20260622`
- task_type: `risk_patch`
- status: `implemented`
- version_contract: report header remains `v21.1`
- QA level: L3

## Owner Problem

Owner reviewed the 06/22 after-hours report from the user perspective and found that limit-up / overheated cards still exposed the wrong blocker layer:

- A locked limit-up stock could show `等風險報酬` even though the real decision is `漲停/過熱，不追價`.
- RR, entry quality, technical score, and `資料不足` lines appeared while the stock was not tradable because of lock-up / overheat.
- This made the report hard to read and made the user ask why a limit-up stock was blocked by RR instead of by no-chase / retest rules.

## User-Visible Result

- Limit-up / locked / limit-rebound cards now prioritize the no-chase reason.
- A locked card should read like:
  - `等回測｜漲停不追`
  - `狀態：漲停/過熱，不追價`
  - `等待：解除鎖定後，看開板回測是否守住`
  - `有效買點：開板/降溫 + 回測不破 + 非追高`
- The same card must not show RR / quality / technical-score blockers as the main reason.
- Structural failure still has higher priority than limit lock. If a stock is both failed breakout and limit-like, it remains structure-failed / rejected, not wait-retest.

## Non-Goals

- No DB schema change.
- No production DB write, backfill, prune, or dedupe.
- No live Telegram delivery.
- No broad redesign of low-repair, breakout, or holding risk logic.

## Impacted Modules And Consumers

- `core/generator.py`
  - unheld funnel priority for `LIMIT_LOCK` and `LIMIT_REBOUND`
- `presentation/report.py`
  - unheld card title/action for limit-like states
  - entry-check lines for locked / overheated cards
  - suppression of irrelevant RR/score data lines under lock-up
- `tests/test_generator_report.py`
  - visible regression coverage for lock-up card wording and no RR noise
- Direct consumer:
  - official Telegram message list.

## Output Contract

- `LIMIT_LOCK` / `漲停不追`:
  - funnel state: `等回測`
  - title action: `等回測｜漲停不追`
  - primary display: no-chase, wait for open / cooling / retest.
- `LIMIT_REBOUND` / `漲停反彈待確認`:
  - funnel state: `隔日確認`
  - primary display: no chase, wait for next-session confirmation.
- Failed breakout / structure failure has higher priority than lock-up display.
- RR / quality / score lines are not shown as primary blockers while lock-up is the active reason.

## Acceptance Conditions

- Limit-lock card does not contain `等風險報酬`, `缺口：解除鎖定`, `數據：風險報酬`, or `綜合`.
- Limit-lock card contains the three useful lines: state, wait, effective buy point.
- Failed-breakout fixture remains rejected / structure-led, not wait-retest.
- Related report tests pass.
- No live Telegram is sent and no production DB data is changed.

## Failure Specimen And Validation Route

- Failure layer: official report formatter and unheld funnel state.
- Owner specimen: 06/22 after-hours unheld cards for 智原 / 聯電 / 旺宏 / 南亞科 / 光寶科 showing mixed lock-up, RR, quality, and data-score blockers.
- Validation route:
  - limit-lock regression in `tests/test_generator_report.py::test_confirmed_evidence_preserves_limit_lock_chase_hard_blocker`
  - mobile readability replay that protects structural-failure priority.
