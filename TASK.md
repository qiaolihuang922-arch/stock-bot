# TASK: entry_quality_d_semantics_v21_1_20260615

## Status

- task_id: `entry_quality_d_semantics_v21_1_20260615`
- task_type: `normal_patch`
- status: `implemented`
- version: `v21.1`
- QA level: `L2`

## Owner Problem

Owner observed that many cards show `D`, even when a stock is limit-up or has risen for multiple days. The report makes it look like `D` means the market or stock is simply bad, while in the strategy it can also mean "current entry is not actionable" because of limit-up chasing, missing retest, low RR, or setup quality.

## User Visible Result

- Limit-up / rebound states are no longer overwritten by low entry quality.
- Snapshot reasons now say `個股弱勢` for per-stock `market_grade == D`, not `市場弱`.
- Unheld cards distinguish:
  - true setup-quality gap: `買點品質未過（目前 D，需 B 以上）`
  - rebound / retest state: `買點品質：回測 / 轉強後重評`
  - cooldown state: `買點品質：降溫後重評`
- Unlock wording uses `買點品質 B 以上`, so it is clear this is entry setup quality, not a general stock grade.

## Non Goals

- No live Telegram delivery.
- No DB schema or production data change.
- No strategy threshold change.
- No buy/sell decision threshold change.
- No version bump beyond current `v21.1`.

## Impacted Modules And Direct Consumers

- `presentation/report.py`
  - Direct consumer: official Telegram unheld card text.
- `core/generator.py`
  - Direct consumer: unheld funnel state transitions.
- `core/signal_snapshot.py`
  - Direct consumer: dry-run / snapshot reason labels.
- `tests/test_unheld_gap_format.py`
  - Formatter-level regression.
- `tests/test_generator_report.py`
  - Official message-list regression.

## Output Contract

- `D` may remain an internal entry-quality label, but visible text must explain the strategy state.
- Price behavior states (`LIMIT_LOCK`, `LIMIT_REBOUND`, `WEAK_REBOUND`) must not be hidden by generic `entry_quality D`.
- A non-actionable rebound card must explain that quality is re-evaluated after retest / strength confirmation.
- A true setup-quality card may show current D, but only as `買點品質未過（目前 D，需 B 以上）`.
- Per-stock D must not be presented as broad market weakness.

## Version Contract

- Header remains `v21.1`.
- This is a semantic presentation / state routing patch inside v21.1.

## Acceptance Conditions

- Official generator dry-run shows rebound cards using `買點品質：回測 / 轉強後重評`, not `品質 D→B`.
- Official generator dry-run still shows true setup cards with current D and the B target.
- Limit-up / rebound states are not downgraded to `等型態` solely because `entry_quality` is D.
- Snapshot probe confirms limit-up can have strong `market_grade` while still non-actionable due to chase / RR / heat.
- Related formatter, generator, analysis, condition, and state-machine tests pass.
- No live Telegram delivery.

## Fixture / Failure Specimen

- Owner sample: 06/15 v21.1 report where limit-up / strong rebound cards still showed D-like quality language and could be read as "the stock is weak" instead of "current entry is not actionable".
- Required replay route: official `generate_report(dry_run=True)` plus targeted snapshot probes.

## Forbidden And Blocking Conditions

- Do not hard-code one stock/date.
- Do not convert overheat / limit-up into buyable.
- Do not remove entry-quality checks from true setup validation.
- Do not change DB schema, backfill, or live delivery.
