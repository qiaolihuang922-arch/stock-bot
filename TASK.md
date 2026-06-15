# TASK: strategy_axis_split_v21_1_20260615

## Status

- task_id: `strategy_axis_split_v21_1_20260615`
- task_type: `normal_patch`
- status: `implemented`
- version: `v21.1`
- QA level: `L2`

## Owner Problem

Owner observed that report cards still feel like a dead machine: stocks at lows, limit-up stocks, and multi-day rising stocks can all appear blocked by the same `D`-like language. The report does not clearly answer whether the stock is weak, whether the setup is missing, or whether the action is simply "wait / do not chase".

## User Visible Result

- Unheld cards now show a strategy split line:
  - `強弱`: current stock behavior / strength.
  - `買點`: whether entry setup is ready, waiting for retest, cooling, risk/reward, volume, or pattern.
  - `行動`: buyable / wait / do not chase / do not buy.
- Limit-up no longer reads like generic weakness: it can show `強勢鎖價` while action remains wait / no chase.
- Strong rebound no longer reads like generic weakness: it can show `急彈修復` while setup remains `等回測確認`.
- True weak or failed patterns can still show weak / invalid, but the reason is separated from potential reward.

## Non Goals

- No live Telegram delivery.
- No DB schema or production data change.
- No threshold calibration in this round.
- No buy/sell rule loosening.
- No version bump beyond current `v21.1`.

## Impacted Modules And Direct Consumers

- `services/analysis.py`
  - Adds derived strategy axis fields to raw result.
  - Direct consumer: official generator, snapshots, replay payloads.
- `core/generator.py`
  - Adds visible split line and fallback derivation for older/replayed payloads.
  - Direct consumer: Telegram report message list.
- `presentation/report.py`
  - Renders the split line in unheld cards.
  - Direct consumer: Owner mobile reading path.
- `tests/test_analysis_engine.py`
- `tests/test_generator_report.py`

## Output Contract

- A card must not use one grade to represent strength, setup, and action at the same time.
- `強弱` may be strong while `買點` is not ready.
- `買點` may wait for retest/cooldown/RR/setup without implying the stock is dead.
- `行動` must remain conservative when the setup is not ready.
- Replay payloads with stale derived fields must prefer current explicit behavior evidence (`LIMIT_LOCK`, `LIMIT_REBOUND`, `WEAK_REBOUND`) over stale derived labels.

## Version Contract

- Header remains `v21.1`.
- This is a presentation/derived-state split inside v21.1, not a DB or strategy-threshold release.

## Acceptance Conditions

- Official `generate_report(dry_run=True)` shows `拆解：強弱 ...｜買點 ...｜行動 ...` on unheld cards.
- Limit-up card can show `強勢鎖價` but still wait / no chase.
- Strong rebound card can show `急彈修復` but still wait for retest.
- Confirmed breakout snapshot can produce `READY` / `BUYABLE`.
- Weak rebound snapshot remains non-tradeable and waits for retest.
- Related formatter/generator/analysis/condition/state-machine tests pass.
- No live Telegram delivery and no DB writes.

## Fixture / Failure Specimen

- Owner sample: 06/15 v21.1 report where cards with limit-up, rebound, and multi-day strength still looked like generic D / no-buy forever.
- Required replay route: official `generate_report(dry_run=True)` plus targeted `analyze_ohlcv_snapshot` probes.

## Forbidden And Blocking Conditions

- Do not hard-code a single stock/date.
- Do not mark limit-up or overheated moves as buyable.
- Do not hide true setup-quality failures.
- Do not change DB schema, backfill, or live delivery in this task.
