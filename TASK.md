# TASK: low_repair_remove_meaningless_source_gate_v21_1_20260622

## Task Status

- task_id: `low_repair_remove_meaningless_source_gate_v21_1_20260622`
- task_type: `risk_patch`
- status: `implemented`
- version_contract: report header remains `v21.1`
- QA level: L3

## Owner Problem

Owner pointed out that the phrase "source is trusted" is not a meaningful user-facing trading condition, and in many paths the source eligibility helper is effectively a no-op.

The concrete failure pattern is:

- Low-repair should not require a generic strategy-sample `available` flag when DB-backed low-repair conditions are already present.
- The only source-related hard stop for this route should be core market-data failure or conflict.
- Strategy / backtest evidence must remain supporting evidence, not a trade blocker.
- The report must not explain low-repair blocking with vague "source trusted" wording.

## User-Visible Result

- In `盤中`, a low-repair candidate whose DB-backed conditions are fully satisfied becomes:
  - `🟢 可買｜小倉｜低位修復成立`
  - buy text: `守支撐/5日均，不追價`
  - execution suggestion: small position only, `小倉<=10%`.
- In `盤後` / `收盤`, the same candidate remains:
  - `可準備｜低位修復成立`
  - next action is opening / next-session confirmation, not immediate buy.
- Missing strategy context or insufficient strategy sample alone does not block low-repair `可買`.
- Explicit core price / OHLCV / RR source-error or unresolved conflict still blocks.
- Strategy evidence source-error is reported as evidence unavailable, but it does not block the DB-backed setup.

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

- `可買` is allowed when all of the following are true:
  - report phase is `盤中`
  - DB-backed low-repair status is ready
  - hard blockers are absent
  - heat is not `HOT` / `EXTREME`
  - no explicit core market-data source-error / unresolved conflict is present
- `可準備` is used when low-repair is ready but the report phase is not intraday.
- Missing strategy context is not a blocker for this DB-backed route.
- Explicit core market-data source-error / unresolved conflict must fail closed and not show a buy recommendation.
- Strategy evidence source-error must not be upgraded into a hard trade gate.
- Summary must not say `新增買點未成立` when a low-repair intraday buy exists.

## Acceptance Criteria

- Regression proves complete intraday low-repair promotes to `可買｜小倉`.
- Regression proves after-hours low-repair remains `可準備`.
- Regression proves missing strategy context still allows low-repair `可買`.
- Regression proves strategy evidence source-error still allows DB-backed low-repair `可買`.
- Regression proves core price source-error does not become `可買`.
- Official dry-run sends no live Telegram and keeps after-hours output conservative.
- No DB writes are performed.
