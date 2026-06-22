# TASK: low_repair_intraday_buy_v21_1_20260622

## Task Status

- task_id: `low_repair_intraday_buy_v21_1_20260622`
- task_type: `risk_patch`
- status: `implemented`
- version_contract: report header remains `v21.1`
- QA level: L3

## Owner Problem

Owner asked why a stock that already satisfies the low-repair checklist still only shows `可準備`, and when it actually becomes `可買`.

The concrete failure pattern is:

- After-hours output correctly says all low-repair conditions are met, but the report does not explain that this is not yet an intraday executable signal.
- Intraday output needs a real promotion path from `可準備` to `可買` when the same DB-backed low-repair checklist remains valid.
- The system must not fake memory or promote a buy when source evidence is incomplete.

## User-Visible Result

- In `盤中`, a low-repair candidate whose DB-backed conditions are fully satisfied and whose strategy source is eligible becomes:
  - `🟢 可買｜小倉｜低位修復成立`
  - buy text: `守支撐/5日均，不追價`
  - execution suggestion: small position only, `小倉<=10%`.
- In `盤後` / `收盤`, the same candidate remains:
  - `可準備｜低位修復成立`
  - next action is opening / next-session confirmation, not immediate buy.
- If strategy source evidence is missing, source-error, insufficient, or conflicting, the candidate cannot become `可買`.

## Non-Goals

- No DB schema / RLS / grant / policy / role / index / constraint change.
- No production DB write, backfill, prune, or dedupe.
- No live Telegram delivery.
- No broad strategy redesign outside the low-repair executable transition.

## Impacted Modules And Consumers

- `core/generator.py`
  - low-repair intraday executable gate
  - unheld funnel state promotion
  - summary execution bridge
  - new-entry suggestion line
- `presentation/report.py`
  - unheld card title/body/data lines for low-repair buy-ready state
- `tests/test_generator_report.py`
  - positive and negative regression coverage
- Direct consumer:
  - official `generate_report(dry_run=True)` Telegram message list

## Output Contract

- `可買` is allowed only when all of the following are true:
  - report phase is `盤中`
  - DB-backed low-repair status is ready
  - hard blockers are absent
  - heat is not `HOT` / `EXTREME`
  - strategy evidence source is eligible
- `可準備` is used when low-repair is ready but the report phase is not intraday.
- Missing / bad source evidence must fail closed and not show a buy recommendation.
- Summary must not say `新增買點未成立` when a low-repair intraday buy exists.

## Acceptance Criteria

- Regression proves complete intraday low-repair promotes to `可買｜小倉`.
- Regression proves after-hours low-repair remains `可準備`.
- Regression / probe proves incomplete source evidence does not become `可買`.
- Official dry-run sends no live Telegram and keeps after-hours output conservative.
- No DB writes are performed.
