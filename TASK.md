# TASK: report_conflict_entry_gate_v21_0_5_20260615

## Status
- task_id: `report_conflict_entry_gate_v21_0_5_20260615`
- type: `risk_patch`
- status: `complete`
- version: `v21.0.5`
- QA level: `L2`

## Owner Problem
Owner pasted the 06/15 intraday report and asked to solve visible conflicts, unreasonable blockers, and clarify whether volume / market / heat should block buying or whether this is a low-point entry.

## User Visible Result
- Version bumps to `v21.0.5`.
- Broad market weakness and individual-stock weakness are separated:
  - broad `market_state=weak/bear` can produce `市場弱`;
  - stock-level `market_grade=D/E` now displays as `個股弱勢` and waits for setup / approach.
- A card can no longer show `隔日確認` while the trade-state line says `等資料`.
- Non-actionable `觀察 / 不可追高觀察` cards do not turn into data-wait states from source-only noise.
- Low RR plus low entry quality blocks a preparation card and sends it to `等RR修復` / `等型態`.
- Dry-run 06/15 report shows no valid new buy; heat/limit-up and weak setup are wait conditions, not low-point buy signals.

## Non Goals
- No live Telegram delivery.
- No DB schema/RLS/grant/policy/role/index/constraint change.
- No production DB writes or backfill.
- No broker/order execution.

## Impacted Modules And Consumers
- `core/generator.py`
  - Consumer: official report generator, unheld funnel, visible version.
- `core/trade_state_machine.py`
  - Consumer: unheld visible trade state line and guard classification.
- `presentation/report.py`
  - Consumer: Telegram unheld card formatting.
- `tests/test_generator_report.py`
- `tests/test_trade_state_machine.py`
- `tests/test_market_theme_evidence.py`

## Output Contract
- R2 / neutral market reports must not display unheld cards as `等市場｜市場弱` solely because the stock has `market_grade=D`.
- Stock-level weakness displays as `個股弱勢`.
- `隔日確認` cannot coexist with `交易狀態：等資料`.
- Source-only gaps block actionable buy/ready decisions, but do not pollute non-actionable watch cards into `等資料`.
- `RR<1.5` plus low entry quality must prevent `可準備`.
- Heat / limit-up cards remain non-buy: `等冷卻` or `等回測`.

## Research Basis
- Breakouts need confirmation and volume; low-volume breakouts are higher fakeout risk.
- Pullback/retest entries need support/reclaim confirmation instead of chasing.
- Market trend is a risk throttle, but stock-level weakness should not be mislabeled as a broad-market gate.
- Overheated or locked-limit moves should wait for cooldown / retest before entry.

## Acceptance
- Official dry-run generates `v21.0.5`.
- Dry-run checks:
  - no `R2` + `等市場｜市場弱` conflict;
  - no `隔日確認` + `交易狀態：等資料` conflict;
  - no English `entry quality low` leakage;
  - no valid buy shown for the pasted 06/15 specimen route.
- Related tests pass.

## Failure Specimen And Route
- Owner failure: 06/15 intraday v21.0.4 report.
- Failure layer: official generator + trade state machine + Telegram formatter.
- Verification route:
  - `tests/test_generator_report.py`
  - `tests/test_trade_state_machine.py`
  - `tests/test_market_theme_evidence.py`
  - official `generate_report(dry_run=True)` message list.

## Forbidden / Blocking
- Do not send live Telegram.
- Do not label weak individual setup as broad market weakness.
- Do not call a card buyable without a valid setup, RR/quality gate, and non-overheated entry condition.
