# TASK: strong_rebound_not_weak_v21_0_7_20260615

## Status
- task_id: `strong_rebound_not_weak_v21_0_7_20260615`
- type: `risk_patch`
- status: `complete`
- version: `v21.0.7`
- QA level: `L2`

## Owner Problem
Owner pointed out that a stock such as 旺宏 can be near limit-up while the report still labels it `弱反彈待確認`. The visible problem is that the report behaves like a rigid machine: it keeps an old weak-rebound label even when live price action has clearly strengthened.

## User Visible Result
- Strong intraday rebounds are no longer labeled as weak rebound.
- `WEAK_REBOUND` with live/day change >= 7% becomes `急彈待回測`.
- The action remains conservative: no chase, wait for pullback/retest confirmation.
- Low-change weak rebound still remains weak/rejected.
- Version bumps to `v21.0.7`.

## Non Goals
- No live Telegram delivery.
- No DB schema or production DB writes.
- No broker/order execution.
- No blanket permission to buy limit-up / near-limit-up stocks.

## Impacted Modules And Consumers
- `core/generator.py`
  - Consumer: blocker labels, unheld funnel, rejected reason, wait text, summary.
- `core/trade_state_machine.py`
  - Consumer: visible unheld trade-state line and guards.
- `presentation/report.py`
  - Consumer: Telegram unheld card reason / gap / unlock text.
- `tests/test_generator_report.py`
- `tests/test_market_theme_evidence.py`
- `tests/test_trade_state_machine.py`

## Output Contract
- If `price_behavior=WEAK_REBOUND` but live/day change >= 7%, visible state must be `急彈待回測`, not `弱反彈待確認`.
- Such cards must be tracking/wait states, not buy states.
- Card reason must say `急彈未回測`.
- Trigger must wait for retest / non-chase confirmation.
- Existing lower-change weak rebound behavior must remain rejected as weak.

## Acceptance
- Focused tests prove:
  - low-change weak rebound still rejects as weak;
  - +8% weak-rebound raw state becomes `等回測｜急彈待回測`.
- Targeted report/state/evidence suites pass.
- Official dry-run generates `v21.0.7` and no live Telegram delivery.

## Failure Specimen And Route
- Owner failure: pasted report where 旺宏 near limit-up remained `弱反彈待確認`.
- Failure layer: official generator + trade state machine + Telegram formatter.
- Verification route:
  - `tests/test_generator_report.py`
  - `tests/test_trade_state_machine.py`
  - `tests/test_market_theme_evidence.py`
  - official `generate_report(dry_run=True)` message list.

## Forbidden / Blocking
- Do not relabel a strong rebound as buyable without setup/RR/retest.
- Do not hard-code 旺宏 or a single date.
- Do not remove weak-rebound rejection for genuinely weak rebounds.
- Do not live-send Telegram.
