# TASK: db_table_health_audit_20260615

## Status

- task_id: `db_table_health_audit_20260615`
- task_type: `normal_patch`
- status: `implemented`
- version: `v21.1`
- QA level: `L2`

## Owner Problem

Owner saw multiple DB columns showing the same value every day and asked whether the data is useful, whether repeated values are fake, and whether all tables / output flow are still healthy.

## User Visible Result

- Added a reusable read-only table health audit script.
- Audited all current production tables used by the bot.
- Separated expected constant metadata from real data gaps.
- Added tests so future `signal_items` writes must include strategy-memory fields without fabricating historical rows.

## Non Goals

- No live Telegram delivery.
- No DB schema change.
- No production row deletion.
- No fabricated backfill for historical `signal_items`.
- No direct production DML.

## Impacted Modules And Direct Consumers

- `scripts/audit_db_table_health.py`
- `tests/test_audit_db_table_health.py`
- `tests/test_daily_snapshot_store.py`
- Production DB read-only audit:
  - `daily_price`
  - `daily_signal_snapshot`
  - `market_theme_confirmed_evidence`
  - `market_theme_index_daily_bars`
  - `position_events`
  - `positions`
  - `sector_theme_members`
  - `signal_items`
  - `signal_outcomes`
  - `signal_runs`

## Output Contract

- Audit script must be read-only.
- Audit output must include `read_only=true`, `live_telegram=false`, and `schema_change=false`.
- Duplicate checks must use table-specific keys only; event tables must not be treated as duplicate just because the same stock appears multiple times.
- Mostly-null columns are reported as evidence gaps, not filled with fake values.

## Version Contract

- Runtime report remains `v21.1`.
- No user-visible Telegram version bump for this utility-only audit.

## Acceptance Conditions

- Production audit runs without DB errors.
- Tests cover duplicate-key semantics and future `signal_items` strategy fields.
- MD files classify:
  - expected constant metadata;
  - actionable data gaps;
  - fields that should stay null until a matching setup exists.
- No live Telegram delivery.

## Fixture / Failure Specimen

- Owner observation: several columns looked identical across days, which made the table look useless or fake.
- Required route:
  - read all production tables;
  - profile constant / mostly-null / duplicate candidates;
  - classify findings;
  - add reusable audit command and tests;
  - update handoff and cleanup docs.

## Forbidden And Blocking Conditions

- Do not delete DB rows in this task.
- Do not invent historical values to make columns look populated.
- Do not classify repeated stock events as duplicate rows without a table-specific unique key.
- Do not claim scheduled bot output is fixed from this audit alone.
