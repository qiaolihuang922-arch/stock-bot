-- Evidence chain market/theme production ops manual template.
-- Manual only. Agent must not execute.
-- This artifact is not a migration and is not evidence that production is live.
-- This task did not perform live Supabase writes, formal backfill, production RLS
-- changes, read-only role changes, or Telegram delivery.
-- Replace every :PLACEHOLDER only after Owner approval in the production console.
-- Do not run this whole file as a single copy/paste without replacing
-- placeholders and selecting the intended section. Step A/B/C are commented
-- templates; Step D is read-only but still requires :TRADE_DATE replacement.
-- Do not store project URLs, passwords, service-role keys, or connection strings here.

-- Step A: optional read-only role/grant, requires Owner approval.
-- owner-input-required:
--   :READONLY_ROLE_NAME
--   :OWNER_APPROVED_SCHEMA_NAME
--
-- begin manual-owner-approved-step-a;
-- grant usage on schema public to :READONLY_ROLE_NAME;
-- grant select on public.market_theme_confirmed_evidence to :READONLY_ROLE_NAME;
-- end manual-owner-approved-step-a;

-- Step B: optional RLS policy, requires Owner approval.
-- owner-input-required:
--   :READONLY_ROLE_NAME
--   :OWNER_APPROVED_POLICY_NAME
--
-- begin manual-owner-approved-step-b;
-- alter table public.market_theme_confirmed_evidence enable row level security;
-- create policy :OWNER_APPROVED_POLICY_NAME
-- on public.market_theme_confirmed_evidence
-- for select
-- to :READONLY_ROLE_NAME
-- using (true);
-- end manual-owner-approved-step-b;

-- Step C: optional backfill/upsert template, requires Owner approval.
-- owner-input-required:
--   :OWNER_APPROVED_SOURCE_NAME
--   :TRADE_DATE
--   :AS_OF
--   :MARKET_INDEX
--   :SECTOR_THEME_KEY
--   :EVIDENCE_VALUE_JSONB
--   :WATCHLIST_BREADTH_JSONB
--   :LINEAGE_JSONB
--
-- begin manual-owner-approved-step-c;
-- insert into public.market_theme_confirmed_evidence (
--     trade_date,
--     as_of,
--     market_index,
--     sector_theme_key,
--     source_family,
--     source_name,
--     freshness,
--     evidence_value,
--     watchlist_breadth,
--     support_level,
--     evidence_status,
--     lineage,
--     metadata,
--     notes
-- ) values (
--     :TRADE_DATE,
--     :AS_OF,
--     :MARKET_INDEX,
--     :SECTOR_THEME_KEY,
--     'production_db',
--     :OWNER_APPROVED_SOURCE_NAME,
--     'fresh',
--     :EVIDENCE_VALUE_JSONB,
--     :WATCHLIST_BREADTH_JSONB,
--     'supporting',
--     'confirmed',
--     :LINEAGE_JSONB,
--     jsonb_build_object('manual_template', true, 'owner_approved', true),
--     'Owner-approved manual backfill template row'
-- )
-- on conflict (trade_date, market_index, sector_theme_key, source_family, source_name, as_of)
-- do update set
--     freshness = excluded.freshness,
--     evidence_value = excluded.evidence_value,
--     watchlist_breadth = excluded.watchlist_breadth,
--     support_level = excluded.support_level,
--     evidence_status = excluded.evidence_status,
--     lineage = excluded.lineage,
--     metadata = excluded.metadata,
--     notes = excluded.notes,
--     updated_at = now();
-- end manual-owner-approved-step-c;

-- Step D: read-only verification queries.
-- These queries are safe to run manually because they only inspect catalog/table
-- state. Results are for Owner interpretation and do not prove production is
-- complete unless Owner confirms the observed output.

select
    'table_visibility' as check_name,
    to_regclass('public.market_theme_confirmed_evidence')::text as observed_table;

select
    'rls_enabled' as check_name,
    c.relrowsecurity as rls_enabled,
    c.relforcerowsecurity as rls_forced
from pg_class c
join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'public'
  and c.relname = 'market_theme_confirmed_evidence';

select
    'policies' as check_name,
    schemaname,
    tablename,
    policyname,
    roles,
    cmd,
    qual
from pg_policies
where schemaname = 'public'
  and tablename = 'market_theme_confirmed_evidence'
order by policyname;

select
    'grants' as check_name,
    grantee,
    privilege_type
from information_schema.role_table_grants
where table_schema = 'public'
  and table_name = 'market_theme_confirmed_evidence'
order by grantee, privilege_type;

select
    'readonly_smoke_shape' as check_name,
    count(*) as rows_seen,
    count(*) filter (
        where evidence_status = 'confirmed'
          and freshness = 'fresh'
          and support_level in ('confirmed', 'supporting')
    ) as fresh_confirmed_or_supporting_rows
from public.market_theme_confirmed_evidence
where trade_date = :TRADE_DATE;
