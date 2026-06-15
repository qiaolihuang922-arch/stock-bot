# CURRENT_STATE.md

## Current Task

- task_id: `strategy_feature_persistence_v21_1_20260615`
- status: `complete`
- version: `v21.1`
- no live Telegram delivery.
- production DB backfill was executed through approved repo scripts only.

## Stable Context

- Owner reads Telegram on mobile; wording must be decision-first and avoid internal pipeline noise.
- Production dispatch model is Render web service called every five minutes, then GitHub workflow dispatch.
- Production source-of-truth remains Supabase / runner data, not local cache.
- DB schema/RLS/grant/policy/role/index/constraint changes normally require Owner approval; Owner authorized adding fields / more recording for this task.
- Non-schema DB write/backfill must use existing approved repo scripts or service APIs; direct hand-written production DML is forbidden.

## Current Changes

- v21.1 strategy features are no longer report-only.
- Market/theme evidence stale-row root cause:
  - normal bot path writes `daily_price` / `daily_signal_snapshot`;
  - market/theme evidence writes live under `run_mode=daily_evidence`;
  - workflow previously had no schedule, only manual dispatch.
- `.github/workflows/stock-bot-clean.yml` now runs market/theme freshness inside normal `run_mode=bot` after the bot step.
- `daily_evidence` remains available only as a manual recovery mode.
- New SQL artifact adds typed strategy-feature columns to:
  - `daily_signal_snapshot`
  - `signal_items`
- Daily snapshot, report item persistence, and backfill rows now carry:
  - V10/V20 volume;
  - 20D/60D resistance;
  - 20D/60D breakout prices and distances;
  - retest zone;
  - compact raw_result where applicable.
- Schema-missing fallback keeps runner/backfill from crashing before migration is applied.
- `backfill_signals.py` now supports `--lookback-days`.
- Owner applied the SQL migration; schema was verified read-only before backfill.
- v21.1 strategy-feature backfill has been executed for the 12 tracked stocks.
- market/theme evidence gaps for `2026-06-11`, `2026-06-12`, and `2026-06-15` have been filled.

## Backfill Decision

- Completed strategy-feature backfill: `730` calendar days.
- Reason:
  - 60D resistance needs enough warmup;
  - outcome calibration needs repeated 1/3/5/10-day forward samples across regimes;
  - Owner said two years of DB data should exist.
- Script warmup: `120` calendar days before requested start.
- Result:
  - `daily_signal_snapshot` v21.1 total rows: `5112`.
  - All 12 tracked stocks have v21.1 snapshots through `2026-06-15`.
  - v21.1 feature columns are non-null on all `5112` v21.1 rows.
  - No live Telegram delivery.

## Verification State

- Focused persistence/backfill/calibration:
  - `19 passed`.
- Targeted strategy/report/backfill suite:
  - `334 passed, 149 warnings, 57 subtests passed`.
- Official generator dry-run:
  - `v21.1`;
  - `messages 4`;
  - `write_results None`.
- TWSE v21.1 strategy backfill:
  - approved script used: `scripts/backfill_signals.py`;
  - version: `v21.1`;
  - source: `twse`;
  - `schema_fallback=False` on completed single-stock writes.
- Market/theme freshness / backfill check:
  - `2026-06-10` complete;
  - `2026-06-11` complete after backfill;
  - `2026-06-12` complete after backfill;
  - `2026-06-13`, `2026-06-14` weekend / no rows expected;
  - `2026-06-15` complete after backfill.
- Evidence automation tests:
  - `71 passed, 13 subtests passed`.

## Git State

- branch: `main`
- upstream: `origin/main`
- HEAD equals upstream: `yes`
- worktree: clean except local `.pytest_cache` permission warning.
- bash completion gate could not run because WSL/Hyper-V is unavailable; Windows-equivalent git checks passed.

## Known Follow-ups

- Market/theme evidence should resume through the normal bot workflow after the after-close safe-write window.
- `trades` appears unused by code and has only one old row, but deletion needs a dedicated cleanup task and evidence review.
