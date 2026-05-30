-- Evidence Phase 5: unified market/theme index source tables.
-- Manual execution only. Do not run this SQL from agents in this task.
-- Copy and execute this entire file as one block in Supabase SQL editor.
--
-- Purpose:
-- - Use one index OHLCV source table for both broad market indexes and
--   sector/theme indexes.
-- - Keep only one membership table for theme constituents.
-- - Avoid parallel tables with identical OHLCV duties.
--
-- This file does not drop previously created draft tables. Drop decisions must
-- be made only after production rows are verified empty or migrated.

create table if not exists public.market_theme_index_daily_bars (
    id bigserial primary key,
    trade_date date not null,
    as_of timestamptz not null,
    index_scope text not null
        check (index_scope in ('market', 'sector_theme')),
    market_index text not null,
    sector_theme_key text,
    index_name text,
    source_family text not null default 'market_data'
        check (source_family in (
            'market_data',
            'production_db',
            'owner_approved_persistent'
        )),
    source_name text not null,
    index_method text not null default 'external_index'
        check (index_method in (
            'external_index',
            'provider_sector_index'
        )),
    open numeric,
    high numeric,
    low numeric,
    close numeric not null,
    change_pct numeric,
    volume numeric,
    turnover numeric,
    member_count integer,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    check (
        (index_scope = 'market' and sector_theme_key is null)
        or
        (index_scope = 'sector_theme' and sector_theme_key is not null)
    ),
    check (jsonb_typeof(metadata) = 'object')
);

comment on table public.market_theme_index_daily_bars is
    'Unified source table for broad market and sector/theme index OHLCV rows. Replaces separate market_index_daily_bars and sector_theme_daily_bars drafts.';
comment on column public.market_theme_index_daily_bars.index_scope is
    'market for broad indexes; sector_theme for theme/sector indexes.';
comment on column public.market_theme_index_daily_bars.market_index is
    'Stable market key, such as TAIEX, TPEx, or another approved index family.';
comment on column public.market_theme_index_daily_bars.sector_theme_key is
    'Required for sector_theme rows; null for broad market rows.';
comment on column public.market_theme_index_daily_bars.source_family is
    'Approved persistent source family only; runtime/local/cache rows are forbidden.';

create unique index if not exists uq_market_theme_index_daily_bars_observation
on public.market_theme_index_daily_bars (
    trade_date,
    index_scope,
    market_index,
    coalesce(sector_theme_key, ''),
    source_family,
    source_name
);

create index if not exists idx_market_theme_index_daily_bars_trade_date
on public.market_theme_index_daily_bars (trade_date);

create index if not exists idx_market_theme_index_daily_bars_market_latest
on public.market_theme_index_daily_bars (market_index, trade_date desc);

create index if not exists idx_market_theme_index_daily_bars_theme_latest
on public.market_theme_index_daily_bars (sector_theme_key, trade_date desc)
where index_scope = 'sector_theme';

create table if not exists public.sector_theme_members (
    id bigserial primary key,
    sector_theme_key text not null,
    stock_code text not null,
    stock_name text,
    market_index text not null default 'TAIEX',
    weight numeric,
    is_active boolean not null default true,
    valid_from date not null default current_date,
    valid_to date,
    source_family text not null default 'owner_approved_persistent'
        check (source_family in (
            'market_data',
            'production_db',
            'owner_approved_persistent'
        )),
    source_name text not null,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    check (valid_to is null or valid_to >= valid_from),
    check (jsonb_typeof(metadata) = 'object')
);

comment on table public.sector_theme_members is
    'Persistent sector/theme membership mapping used to compute breadth and build confirmed market/theme evidence.';

create unique index if not exists uq_sector_theme_members_identity
on public.sector_theme_members (
    sector_theme_key,
    stock_code,
    valid_from,
    source_family,
    source_name
);

create index if not exists idx_sector_theme_members_theme_active
on public.sector_theme_members (sector_theme_key, is_active);

create index if not exists idx_sector_theme_members_stock_active
on public.sector_theme_members (stock_code, is_active);

select 'evidence_phase_5_market_theme_index_sources.sql complete' as sql_artifact_validation_marker;
