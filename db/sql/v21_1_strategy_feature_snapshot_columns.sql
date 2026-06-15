-- v21.1 Strategy feature snapshot columns.
-- Manual execution only. Do not run this SQL from agents in this task.
-- Copy and execute this entire file as one block in Supabase SQL editor.
--
-- Purpose:
-- - Persist the strategy features that v21.1 uses for buyability decisions.
-- - Keep daily report, daily_signal_snapshot, backfill, and later calibration
--   on the same source-of-truth instead of relying on transient runtime output.
-- - Avoid storing full K-line arrays in JSON; OHLCV remains in daily_price.
--
-- Execution notes:
-- 1. Owner reviews this full SQL block before execution.
-- 2. This block is idempotent and safe to re-run.
-- 3. This file does not write or backfill data.
-- 4. This file does not change RLS, grants, policies, roles, indexes, or constraints.

alter table if exists public.daily_signal_snapshot
    add column if not exists volume_ratio_10 numeric,
    add column if not exists volume_ratio_20 numeric,
    add column if not exists resistance_20 numeric,
    add column if not exists resistance_60 numeric,
    add column if not exists breakout_price_20 numeric,
    add column if not exists breakout_price_60 numeric,
    add column if not exists breakout_distance_20 numeric,
    add column if not exists breakout_distance_60 numeric,
    add column if not exists retest_zone_low numeric,
    add column if not exists retest_zone_high numeric,
    add column if not exists retest_zone_label text,
    add column if not exists raw_result jsonb default '{}'::jsonb;

comment on column public.daily_signal_snapshot.volume_ratio_10 is
    'Latest volume divided by the latest 10-bar average volume, matching v21.1 short-term volume context.';
comment on column public.daily_signal_snapshot.volume_ratio_20 is
    'Latest volume divided by the latest 20-bar average volume, matching v21.1 swing-volume context.';
comment on column public.daily_signal_snapshot.resistance_20 is
    '20-bar resistance anchor excluding the most recent 3 bars; used by v21.1 fast breakout/retest context.';
comment on column public.daily_signal_snapshot.resistance_60 is
    '60-bar resistance anchor excluding the most recent 5 bars; used by v21.1 higher-timeframe context.';
comment on column public.daily_signal_snapshot.breakout_price_20 is
    '20-bar breakout trigger derived from resistance_20 and the strategy breakout threshold.';
comment on column public.daily_signal_snapshot.breakout_price_60 is
    '60-bar breakout trigger derived from resistance_60 and the strategy breakout threshold.';
comment on column public.daily_signal_snapshot.breakout_distance_20 is
    'Percent distance from close to breakout_price_20. Positive means still below the trigger.';
comment on column public.daily_signal_snapshot.breakout_distance_60 is
    'Percent distance from close to breakout_price_60. Positive means still below the higher-timeframe trigger.';
comment on column public.daily_signal_snapshot.retest_zone_low is
    'Lower edge of the v21.1 retest zone, normally resistance_20.';
comment on column public.daily_signal_snapshot.retest_zone_high is
    'Upper edge of the v21.1 retest zone, normally breakout_price_20.';
comment on column public.daily_signal_snapshot.retest_zone_label is
    'Human-readable label for the retest zone source.';
comment on column public.daily_signal_snapshot.raw_result is
    'Compact strategy JSON snapshot for replay/debug. Full OHLCV arrays are intentionally not stored here.';

alter table if exists public.signal_items
    add column if not exists volume_ratio_10 numeric,
    add column if not exists volume_ratio_20 numeric,
    add column if not exists resistance_20 numeric,
    add column if not exists resistance_60 numeric,
    add column if not exists breakout_price_20 numeric,
    add column if not exists breakout_price_60 numeric,
    add column if not exists breakout_distance_20 numeric,
    add column if not exists breakout_distance_60 numeric,
    add column if not exists retest_zone_low numeric,
    add column if not exists retest_zone_high numeric,
    add column if not exists retest_zone_label text;

comment on column public.signal_items.volume_ratio_10 is
    'Latest volume divided by the latest 10-bar average volume for the report item.';
comment on column public.signal_items.volume_ratio_20 is
    'Latest volume divided by the latest 20-bar average volume for the report item.';
comment on column public.signal_items.resistance_20 is
    '20-bar resistance anchor excluding the most recent 3 bars for the report item.';
comment on column public.signal_items.resistance_60 is
    '60-bar resistance anchor excluding the most recent 5 bars for the report item.';
comment on column public.signal_items.breakout_price_20 is
    '20-bar breakout trigger derived from resistance_20.';
comment on column public.signal_items.breakout_price_60 is
    '60-bar breakout trigger derived from resistance_60.';
comment on column public.signal_items.breakout_distance_20 is
    'Percent distance from item price to breakout_price_20.';
comment on column public.signal_items.breakout_distance_60 is
    'Percent distance from item price to breakout_price_60.';
comment on column public.signal_items.retest_zone_low is
    'Lower edge of the v21.1 retest zone.';
comment on column public.signal_items.retest_zone_high is
    'Upper edge of the v21.1 retest zone.';
comment on column public.signal_items.retest_zone_label is
    'Human-readable label for the retest zone source.';

select 'v21_1_strategy_feature_snapshot_columns.sql complete' as sql_artifact_validation_marker;
