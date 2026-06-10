# TASK: report_revenue_noise_fsm_20260610

## Status
- task_id: `report_revenue_noise_fsm_20260610`
- type: `normal_patch`
- status: `complete`
- version: `v21.0`
- QA level: `L2`

## Owner Problem
Owner pasted the 2026-06-10 v21.0 report and raised three visible problems:
- May revenue should already exist, but the report still showed 2026/04 revenue.
- The unheld stock cards are too noisy for mobile reading.
- The v21 trade state machine line looks useless because it repeats the same trigger wording.

## User Visible Result
- The future 30-day fundamentals block can refresh stale TWSE/TPEX OpenAPI monthly revenue with MOPS company monthly revenue, so available targets show 2026/05 revenue.
- Closing/after-hours unheld cards hide cross-day history lines like `歷史：前次 observe｜連續觀察 1 天`.
- Unheld trade state lines now show the missing event, for example `還差：量能確認` or `還差：回測確認`, instead of repeating the full trigger sentence.

## Non Goals
- No live Telegram delivery.
- No DB schema/RLS/grant/policy/index change.
- No manual SQL/DML.
- No change to holding sell/stop-loss decision logic.

## Impacted Modules And Consumers
- `core/future_watch.py`: future-watch fundamentals collection and MOPS monthly revenue fallback.
- `core/trade_state_machine.py`: user-visible unheld state-machine line.
- `presentation/report.py`: closing/after-hours unheld card noise suppression.
- `tests/test_generator_report.py`: MOPS revenue freshness and closing-card noise regression.
- `tests/test_trade_state_machine.py`: v21 state line regression.
- Direct consumers: official `generate_report(dry_run=True)`, Telegram message list, GitHub/Render runner report artifact.

## Output Contract
- `關注標的財報` keeps EPS and revenue on each target line.
- If TWSE/TPEX OpenAPI revenue is stale and MOPS company monthly revenue returns the expected previous month, replace only that target revenue month/Yoy.
- If MOPS fails or returns no row for a target, keep the best official existing value; do not fabricate May data.
- Unheld card state line format:
  - non-actionable: `交易狀態：<state>｜動作：等待｜還差：<next event>`
  - actionable: `交易狀態：<state>｜動作：<action>｜下一步：<next event>`
- `收盤` and `盤後` unheld cards must not show cross-day history detail lines.

## Acceptance
- Generator and trade-state-machine tests pass.
- Official `generate_report(dry_run=True)` returns 4 messages without live Telegram delivery.
- Dry-run unheld message no longer contains `歷史：前次 observe` or `連續觀察 1 天`.
- Dry-run future watch shows available 2026/05 revenue rows from MOPS fallback and keeps stale rows only when official fallback fails.

## Failure Specimen And Route
- Owner specimen: 2026-06-10 v21.0 Telegram report.
- Failure layer: official generator message list / future-watch formatter / unheld card formatter.
- Replay route: `generate_report(dry_run=True)` and targeted generator tests.
- Data finding: TWSE/TPEX OpenAPI monthly revenue source was still at ROC `11504`; MOPS company monthly revenue endpoint had ROC `11505` rows for most targets.

## Forbidden / Blocking
- No live Telegram delivery.
- Do not claim all targets have May revenue if MOPS cannot return a row.
- Do not weaken hard-stop or holding risk actions in this task.
- If git completion gate fails, do not claim complete.
