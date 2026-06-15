# CURRENT_STATE.md

## Current Task

- task_id: `db_table_health_audit_20260615`
- status: `implemented + QA passed`
- version: `v21.1`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; report wording must be decision-first and avoid unexplained internal shorthand.
- Production dispatch model: Render web service is called every five minutes, then GitHub workflow dispatch runs `run_mode=bot`.
- Production source-of-truth is Supabase / runner data, not local cache, worktree state, or agent memory.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval unless explicitly authorized.
- Non-schema DB writes/backfills must use approved repo scripts or service APIs; direct hand-written production DML is forbidden.
- DB backfill/prune tasks must automatically update MD and cleanup evidence.

## Current Implementation State

- Runtime report remains `v21.1`.
- v21.3 strategy-axis memory schema is applied in production.
- `daily_signal_snapshot` has `5786` v21.1 strategy-memory rows from the previous backfill.
- Retest memory is tightened:
  - only active retest rows have `retest_reference_price` / `retest_days_since_breakout`;
  - non-retest rows keep those fields null.
- New read-only audit utility exists:
  - `scripts/audit_db_table_health.py`
- Future `signal_items` item payloads are tested to include strategy-memory fields.

## Table Health Findings

- Expected constants:
  - `daily_price.source=twse`
  - `daily_signal_snapshot.version=v21.1`
  - formula/basis labels such as `rr_formula`, `volume_basis`, `breakout_reference_type`
  - official TWSE source labels in market-theme tables
- Real gaps to fix or explicitly ignore:
  - `market_theme_index_daily_bars.open/high/low/volume/turnover/member_count` are all null.
  - `signal_outcomes.max_high_pct/max_drawdown_pct` are all null.
  - historical `signal_items` new strategy-memory columns are all null by design; do not fabricate.
- `position_events` repeated stocks are valid event history, not duplicate rows.

## Verification State

- Production audit command:
  - `.\.venv\Scripts\python.exe scripts\audit_db_table_health.py`
  - result: `errors=[]`
- Tests:
  - `56 passed`
- No live Telegram delivery.
- No DB schema change.
- No production deletion.

## Known Follow-ups

- Observe next scheduled `run_mode=bot` report and check fresh `signal_items` strategy fields.
- Decide whether to enrich or hide `market_theme_index_daily_bars` OHLCV/member placeholder columns.
- Implement or retire `signal_outcomes` max high/drawdown metrics.
