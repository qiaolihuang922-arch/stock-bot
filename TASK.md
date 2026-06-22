# TASK: low_repair_ready_state_v21_1_20260622

## Task Status

- task_id: `low_repair_ready_state_v21_1_20260622`
- task_type: `risk_patch`
- status: `implemented`
- version_contract: runtime report remains `v21.1`
- QA level: L3

## Owner Problem

Owner pasted the `06/22 盤後｜v21.1` report and asked why a stock still cannot be bought when the displayed low-repair conditions are already satisfied.

Failure specimen:

- `3231 緯創` showed `等低位修復｜低位修復觀察`.
- The same card displayed `已滿足 支撐未破、站上5日均、量能有效、風險報酬達標`.
- This is a strategy/display conflict: the state machine stayed in waiting state while the visible checklist said the low-repair route was complete.

## User-Visible Result

- If low-repair conditions are all satisfied, the unheld card must not remain `等低位修復`.
- In after-hours reports, the correct state is `可準備｜低位修復成立`, not immediate `可買`.
- The card must explain the next actionable condition: open/next session confirmation without chasing, while holding support/5-day MA and keeping volume controlled.
- If one condition is still missing, keep `等低位修復` and show the missing item.

## Non-Goals

- No DB schema/RLS/grant/policy/role/index/constraint change.
- No production DB write/backfill/delete.
- No live Telegram delivery.
- No broad strategy redesign outside the low-repair state/display conflict and related funnel count consistency.

## Impacted Modules And Consumers

- `core/generator.py`: low-repair readiness helper and unheld funnel state promotion.
- `presentation/report.py`: low-repair-ready card wording and summary empty-bucket guard.
- `tests/test_generator_report.py`: regression coverage for low-repair-ready and mutually exclusive unheld buckets.
- Direct consumer: official `generate_report(dry_run=True)` Telegram message list.

## Output Contract

- `等低位修復` remains for incomplete low-repair conditions.
- `可準備｜低位修復成立` appears when all low-repair conditions are met.
- `可準備` does not mean immediate buy in `盤後`; it means next session confirmation before action.
- `隔日確認` and `僅追蹤` are mutually exclusive buckets in summary counts.
- Empty summary parentheses must not render.

## Acceptance Criteria

- Regression test proves all-met low-repair promotes to `可準備`, not `等低位修復`.
- Regression test proves incomplete low-repair still waits and shows the missing condition.
- Official dry-run shows `3231 緯創` as `可準備｜低位修復成立`.
- Official dry-run shows `2324 仁寶` still waiting because it has not stood back above 5-day MA.
- No live Telegram and no production DB write.
