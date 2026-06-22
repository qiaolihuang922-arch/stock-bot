# TASK: intraday_low_repair_buy_state_sync_v21_1_20260622

## Task Status

- task_id: `intraday_low_repair_buy_state_sync_v21_1_20260622`
- task_type: `risk_patch`
- status: `implemented`
- version_contract: report header remains `v21.1`
- QA level: L3

## Owner Problem

Owner asked whether the intraday path was handled after the after-hours low-repair fix, and when the report will actually say a stock can be bought.

Concrete failure specimen:

- A low-repair candidate can have a title and buy line that imply `can buy / small position`.
- The same intraday card still showed stale state-machine text such as `trading state: waiting for data`.
- That creates a direct user-visible contradiction: the reader cannot know whether it is executable now or still blocked.

## User-Visible Result

- Intraday low-repair with all DB-backed conditions satisfied now renders a consistent executable card:
  - title: `可買｜小倉｜低位修復成立`
  - state: `交易狀態：可買｜動作：小倉試單｜條件：守支撐/5日均，不追價`
  - buy line: `買點：可買｜低位修復小倉｜守支撐/5日均，不追價`
  - intraday trigger: `守支撐/5日均 + 量能不失控，小倉試單`
- After-hours / close low-repair with all conditions satisfied remains non-executable:
  - title: `可準備｜低位修復成立`
  - next trigger: `開盤不追高；守支撐/5日均 + 量能不失控，小倉確認`

## Non-Goals

- No DB schema change.
- No production DB write, backfill, prune, or dedupe.
- No live Telegram delivery.
- No broad redesign of breakout, retest, cooling, or holding risk logic.

## Impacted Modules And Consumers

- `presentation/report.py`
  - unheld low-repair card state line
  - after-hours low-repair prepare trigger line
- `tests/test_generator_report.py`
  - user-visible regression for intraday low-repair executable card
  - user-visible regression for after-hours low-repair prepare card
- Direct consumer:
  - official Telegram message list produced by `formatTelegramMessages`

## Output Contract

- Intraday low-repair is executable only when the low-repair gate has already promoted the funnel state to `可買` and `low_repair_intraday_buy_ready` is true.
- In that route, stale state-machine text from generic helpers must not override the low-repair executable decision.
- After-hours complete low-repair is `可準備`, not `可買`.
- After-hours trigger must explain the next session condition, not repeat a generic `重新評估`.

## Acceptance Conditions

- Intraday low-repair card contains `可買｜小倉` and a matching `交易狀態：可買`.
- Intraday low-repair card does not contain `交易狀態：等資料` or `還差：資料恢復`.
- After-hours complete low-repair card contains the open-confirmation trigger.
- Related unheld/report tests still pass.
- No live Telegram is sent and no production DB data is changed.

## Failure Specimen And Validation Route

- Failure layer: official report formatter / Telegram card body.
- Validation route:
  - `tests/test_generator_report.py::GeneratorReportTest::test_low_repair_ready_promotes_to_intraday_small_buy`
  - `tests/test_generator_report.py::GeneratorReportTest::test_low_repair_all_conditions_met_promotes_to_prepare_not_waiting`
  - related report-state regression subset.
