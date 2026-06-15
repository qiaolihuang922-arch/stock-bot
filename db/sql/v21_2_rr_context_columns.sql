-- v21.2 RR context columns.
-- Manual execution only. Do not run this SQL from agents in this task.
-- Copy and execute this entire file as one block in Supabase SQL editor.
--
-- Purpose:
-- - Persist the standard risk/reward inputs behind the visible RR number.
-- - Make RR auditable as entry / stop / target / reward / risk, not only a
--   single ratio that can be misread as a buy signal.
-- - Distinguish actionable RR from theoretical or blocked RR in historical
--   calibration and Telegram report generation.
--
-- Execution notes:
-- 1. Owner reviews this full SQL block before execution.
-- 2. This block is idempotent and safe to re-run.
-- 3. This file does not write or backfill data.
-- 4. This file does not change RLS, grants, policies, roles, indexes, or constraints.

alter table if exists public.daily_signal_snapshot
    add column if not exists rr_context text,
    add column if not exists rr_entry_price numeric,
    add column if not exists rr_stop_price numeric,
    add column if not exists rr_target_price numeric,
    add column if not exists rr_reward_amount numeric,
    add column if not exists rr_risk_amount numeric,
    add column if not exists rr_risk_pct numeric,
    add column if not exists rr_target_basis text,
    add column if not exists rr_formula text;

comment on column public.daily_signal_snapshot.rr_context is
    'RR usability context: actionable, setup_pending, theoretical, or blocked.';
comment on column public.daily_signal_snapshot.rr_entry_price is
    'Entry price used by the RR formula.';
comment on column public.daily_signal_snapshot.rr_stop_price is
    'Stop-loss price used by the RR formula.';
comment on column public.daily_signal_snapshot.rr_target_price is
    'Take-profit / target price used by the RR formula.';
comment on column public.daily_signal_snapshot.rr_reward_amount is
    'Reward amount: target minus entry.';
comment on column public.daily_signal_snapshot.rr_risk_amount is
    'Risk amount: entry minus stop, floored by strategy minimum stop buffer when applicable.';
comment on column public.daily_signal_snapshot.rr_risk_pct is
    'Risk amount divided by entry price.';
comment on column public.daily_signal_snapshot.rr_target_basis is
    'Human/audit label describing how the target price was derived.';
comment on column public.daily_signal_snapshot.rr_formula is
    'Formula contract, normally (target-entry)/(entry-stop).';

alter table if exists public.signal_items
    add column if not exists rr_context text,
    add column if not exists rr_entry_price numeric,
    add column if not exists rr_stop_price numeric,
    add column if not exists rr_target_price numeric,
    add column if not exists rr_reward_amount numeric,
    add column if not exists rr_risk_amount numeric,
    add column if not exists rr_risk_pct numeric,
    add column if not exists rr_target_basis text,
    add column if not exists rr_formula text;

comment on column public.signal_items.rr_context is
    'RR usability context for this report item.';
comment on column public.signal_items.rr_entry_price is
    'Entry price used by the RR formula for this report item.';
comment on column public.signal_items.rr_stop_price is
    'Stop-loss price used by the RR formula for this report item.';
comment on column public.signal_items.rr_target_price is
    'Take-profit / target price used by the RR formula for this report item.';
comment on column public.signal_items.rr_reward_amount is
    'Reward amount: target minus entry.';
comment on column public.signal_items.rr_risk_amount is
    'Risk amount: entry minus stop, floored by strategy minimum stop buffer when applicable.';
comment on column public.signal_items.rr_risk_pct is
    'Risk amount divided by entry price.';
comment on column public.signal_items.rr_target_basis is
    'Audit label describing how the target price was derived.';
comment on column public.signal_items.rr_formula is
    'Formula contract, normally (target-entry)/(entry-stop).';

select 'v21_2_rr_context_columns.sql complete' as sql_artifact_validation_marker;
