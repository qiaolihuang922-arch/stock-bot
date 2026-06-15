-- v21.3 Strategy axis memory columns.
-- Manual execution only. Do not run this SQL from agents in this task.
-- Copy and execute this entire file as one block in Supabase SQL editor.
--
-- Purpose:
-- - Persist the three strategy axes behind the Telegram report:
--   stock strength, entry setup state, and actionability.
-- - Persist setup blockers and data-quality states so multi-day memory comes
--   from production DB, not local cache, runtime dicts, report text, or agent
--   conversation memory.
-- - Keep OHLCV in daily_price; these columns only store derived strategy
--   evidence and audit labels.
--
-- Execution notes:
-- 1. Owner reviews this full SQL block before execution.
-- 2. This block is idempotent and safe to re-run.
-- 3. This file does not write or backfill data.
-- 4. This file does not change RLS, grants, policies, roles, indexes, or constraints.

alter table if exists public.daily_signal_snapshot
    add column if not exists stock_strength_state text,
    add column if not exists entry_setup_state text,
    add column if not exists actionability_state text,
    add column if not exists setup_family text,
    add column if not exists setup_valid boolean,
    add column if not exists setup_blocker text,
    add column if not exists setup_blockers jsonb,
    add column if not exists data_quality_state text,
    add column if not exists price_data_state text,
    add column if not exists volume_data_state text,
    add column if not exists volume_basis text,
    add column if not exists intraday_volume_run_rate numeric,
    add column if not exists retest_state text,
    add column if not exists retest_reference_price numeric,
    add column if not exists retest_days_since_breakout integer,
    add column if not exists breakout_reference_type text;

comment on column public.daily_signal_snapshot.stock_strength_state is
    'Derived stock strength axis, e.g. LIMIT_STRONG, SHARP_REBOUND, STRONG, IMPROVING, WEAK.';
comment on column public.daily_signal_snapshot.entry_setup_state is
    'Derived entry setup axis, e.g. READY, WAIT_RETEST, WAIT_COOLDOWN, WAIT_RR, WAIT_VOLUME, WAIT_SETUP.';
comment on column public.daily_signal_snapshot.actionability_state is
    'Derived executable action axis, e.g. BUYABLE, NO_CHASE, WAIT_RETEST, WAIT_RR, WAIT_SETUP.';
comment on column public.daily_signal_snapshot.setup_family is
    'Strategy family for the setup, e.g. breakout, pre_breakout, rebound_retest, trend_continuation, failed_breakout.';
comment on column public.daily_signal_snapshot.setup_valid is
    'Whether the setup is currently actionable by strategy rules; false means wait/no-buy, not necessarily weak stock.';
comment on column public.daily_signal_snapshot.setup_blocker is
    'Primary blocker preventing actionability, e.g. no_retest, overheated, rr_low, low_volume, quality_low.';
comment on column public.daily_signal_snapshot.setup_blockers is
    'All known setup blockers as JSON array. Empty array means no blocker.';
comment on column public.daily_signal_snapshot.data_quality_state is
    'Overall data quality: complete, partial, insufficient, source_error, stale, or missing_source.';
comment on column public.daily_signal_snapshot.price_data_state is
    'Price data quality state for this snapshot.';
comment on column public.daily_signal_snapshot.volume_data_state is
    'Volume data quality state for this snapshot; avoids treating missing volume as normal.';
comment on column public.daily_signal_snapshot.volume_basis is
    'Volume basis: daily_close_volume, intraday_raw_volume, intraday_run_rate, fallback_missing, etc.';
comment on column public.daily_signal_snapshot.intraday_volume_run_rate is
    'Estimated full-day volume ratio during intraday runs. Null when unavailable or not intraday.';
comment on column public.daily_signal_snapshot.retest_state is
    'Retest memory state: not_applicable, waiting, testing, held, failed, confirmed.';
comment on column public.daily_signal_snapshot.retest_reference_price is
    'Price level used as the retest anchor for this snapshot.';
comment on column public.daily_signal_snapshot.retest_days_since_breakout is
    'Number of trading snapshots since the relevant breakout/rebound reference.';
comment on column public.daily_signal_snapshot.breakout_reference_type is
    'Breakout anchor source, e.g. close_20, high_20, close_60, high_60, manual.';

alter table if exists public.signal_items
    add column if not exists stock_strength_state text,
    add column if not exists entry_setup_state text,
    add column if not exists actionability_state text,
    add column if not exists setup_family text,
    add column if not exists setup_valid boolean,
    add column if not exists setup_blocker text,
    add column if not exists setup_blockers jsonb,
    add column if not exists data_quality_state text,
    add column if not exists price_data_state text,
    add column if not exists volume_data_state text,
    add column if not exists volume_basis text,
    add column if not exists intraday_volume_run_rate numeric,
    add column if not exists retest_state text,
    add column if not exists retest_reference_price numeric,
    add column if not exists retest_days_since_breakout integer,
    add column if not exists breakout_reference_type text;

comment on column public.signal_items.stock_strength_state is
    'Report-item stock strength axis.';
comment on column public.signal_items.entry_setup_state is
    'Report-item entry setup axis.';
comment on column public.signal_items.actionability_state is
    'Report-item actionability axis.';
comment on column public.signal_items.setup_family is
    'Report-item setup family.';
comment on column public.signal_items.setup_valid is
    'Whether this report item setup is actionable by strategy rules.';
comment on column public.signal_items.setup_blocker is
    'Primary report-item setup blocker.';
comment on column public.signal_items.setup_blockers is
    'All report-item setup blockers as JSON array.';
comment on column public.signal_items.data_quality_state is
    'Overall data quality state for this report item.';
comment on column public.signal_items.price_data_state is
    'Price data quality state for this report item.';
comment on column public.signal_items.volume_data_state is
    'Volume data quality state for this report item.';
comment on column public.signal_items.volume_basis is
    'Volume basis for this report item.';
comment on column public.signal_items.intraday_volume_run_rate is
    'Estimated full-day volume ratio during intraday report runs. Null when unavailable.';
comment on column public.signal_items.retest_state is
    'Retest state for this report item.';
comment on column public.signal_items.retest_reference_price is
    'Retest anchor price for this report item.';
comment on column public.signal_items.retest_days_since_breakout is
    'Trading snapshots since the breakout/rebound reference for this item.';
comment on column public.signal_items.breakout_reference_type is
    'Breakout anchor source for this report item.';

select 'v21_3_strategy_axis_memory_columns.sql complete' as sql_artifact_validation_marker;
