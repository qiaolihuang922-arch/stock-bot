# TASK: rr_context_standardization_v21_1_20260615

## Status
- task_id: `rr_context_standardization_v21_1_20260615`
- task_type: `risk_patch`
- status: `implemented`
- version: `v21.1`
- QA level: `L3`

## Owner Problem
Owner asked why report RR values are often very large, whether the formula matches common trading practice, and asked to fix the strategy/report so it follows normal entry-stop-target risk/reward logic instead of presenting self-made or misleading buy evidence.

## User Visible Result
- High RR is no longer shown as `達標` unless the setup is actually actionable.
- Non-actionable high RR is labeled as `理論RR` with the reason: `setup未成立`, `僅參考`, `等回測`, or the active blocker.
- RR不足 still displays as normal `RR x｜需>=1.5`, not as theoretical RR.
- Unheld cards keep strategy-granular evidence: blocker first, then distance, breakout/retest zone, V10/V20, quality, and RR context.

## Non Goals
- No live Telegram delivery.
- No live production DB schema change in this task.
- No direct production DML.
- No RLS, grant, policy, role, index, or constraint change.
- No broker/order execution.
- No buy-rule loosening.

## Impacted Modules And Direct Consumers
- `services/analysis.py`
  - Consumer: strategy result, official generator, daily snapshot/backfill payloads.
- `core/signal_snapshot.py`
  - Consumer: daily snapshot and backfill feature payload.
- `services/signal_store.py`
  - Consumer: `signal_items` report-run persistence through shared feature list.
- `services/daily_snapshot_store.py`
  - Consumer: `daily_signal_snapshot` payload through shared feature list.
- `presentation/report.py`
  - Consumer: Telegram message list.
- `db/sql/v21_2_rr_context_columns.sql`
  - Consumer: Owner-reviewed Supabase migration artifact; not executed by agent.

## Output Contract
- Strategy result may include:
  - `rr_context`: `actionable`, `setup_pending`, `theoretical`, or `blocked`.
  - `rr_entry_price`, `rr_stop_price`, `rr_target_price`.
  - `rr_reward_amount`, `rr_risk_amount`, `rr_risk_pct`.
  - `rr_target_basis`.
  - `rr_formula`: `(target-entry)/(entry-stop)`.
- `daily_signal_snapshot` and `signal_items` payloads carry these typed RR fields when schema exists; existing schema fallback removes them instead of crashing.
- Telegram:
  - actionable RR: `RR x達標`;
  - non-actionable high RR: `理論RR x（setup未成立）` or `理論RR x僅參考`;
  - insufficient RR: `RR x｜需>=1.5`.

## Version Contract
- Visible report wording remains under current `v21.1` line because this is a v21.1 strategy-evidence correction, not a new trading mode.
- SQL artifact name is `v21_2_rr_context_columns.sql` because it is a forward schema extension artifact requiring Owner review before execution.

## Acceptance Conditions
- Official generator dry-run must show high RR unheld names as theoretical unless setup is actionable.
- RR不足 cards must not be relabeled as theoretical.
- Snapshot and signal-item payload tests must prove RR formula inputs are persisted through the shared feature contract.
- No live Telegram delivery.
- No production DB schema execution by agent.

## Fixture / Failure Specimen
- Owner sample: `旺宏 2337` showed a strong rebound near limit-up, but report needed to explain why it was not buyable.
- Owner sample: `緯創 / 仁寶 / 技嘉` showed very high RR while still blocked by weak setup or quality D.
- Required replay route: official `generate_report(dry_run=True)` message list, not a helper-only fixture.

## Forbidden And Blocking Conditions
- Do not call non-actionable high RR `達標`.
- Do not hide RR components behind a single number once persistence fields are available.
- Do not execute DB schema changes without Owner approval.
- Do not use synthetic or local-only data as cross-day evidence.
