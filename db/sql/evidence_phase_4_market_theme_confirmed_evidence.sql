-- Evidence Phase 4: confirmed market/theme evidence source-of-truth.
-- Manual execution only. Do not run this SQL from agents in this task.
-- Copy and execute this entire file as one block in Supabase SQL editor.
-- Do not copy only the middle section; missing the final statement terminator
-- can produce ERROR 42601 syntax error at end of input.
--
-- Execution notes:
-- 1. Owner manually opens the Supabase SQL editor or a Postgres console.
-- 2. Owner reviews this full SQL block before execution.
-- 3. This block is designed to be idempotent for repeated manual execution.
-- 4. This task did not execute this SQL, backfill data, write production DB data,
--    or deliver live Telegram messages.
-- 5. Validation for syntax-fix tasks is local/non-production only.
--
-- RLS / permissions guidance:
-- This file intentionally does not enable policies or broad permissions because
-- production role names and access rules are environment-specific. Decide RLS
-- and permissions manually in the production DB console before exposing this
-- table to any runner or application role.

create table if not exists public.market_theme_confirmed_evidence (
    id bigserial primary key,
    trade_date date not null,
    as_of timestamptz not null,
    market_index text not null,
    sector_theme_key text not null,
    source_family text not null,
    source_name text not null,
    freshness text not null
        check (freshness in (
            'fresh',
            'stale',
            'missing-source',
            'source-error',
            'insufficient-data'
        )),
    evidence_value jsonb not null default '{}'::jsonb,
    watchlist_breadth jsonb not null default '{}'::jsonb,
    support_level text not null
        check (support_level in (
            'confirmed',
            'supporting',
            'weak',
            'invalidated'
        )),
    evidence_status text not null default 'confirmed'
        check (evidence_status in (
            'confirmed',
            'rejected',
            'superseded'
        )),
    lineage jsonb not null default '{}'::jsonb,
    metadata jsonb not null default '{}'::jsonb,
    notes text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    check (jsonb_typeof(evidence_value) = 'object'),
    check (jsonb_typeof(watchlist_breadth) = 'object'),
    check (jsonb_typeof(lineage) = 'object'),
    check (jsonb_typeof(metadata) = 'object')
);

comment on table public.market_theme_confirmed_evidence is
    'Production source-of-truth table for confirmed market/theme evidence. Intended for future read-only reconstruction by fresh GitHub runners.';
comment on column public.market_theme_confirmed_evidence.trade_date is
    'Trading date used for cross-day reconstruction and query filters.';
comment on column public.market_theme_confirmed_evidence.as_of is
    'Timezone-aware timestamp when the evidence was observed or generated.';
comment on column public.market_theme_confirmed_evidence.market_index is
    'Stable market index or market-scope key, such as TWSE, TPEx, NASDAQ, or SPY.';
comment on column public.market_theme_confirmed_evidence.sector_theme_key is
    'Stable sector or theme key, such as semiconductor, ai_server, or shipping.';
comment on column public.market_theme_confirmed_evidence.source_family is
    'Source family for traceability, such as market_data, watchlist, theme_classifier, or manual_review.';
comment on column public.market_theme_confirmed_evidence.source_name is
    'Concrete provider, job, calculation, table, view, or manual review name.';
comment on column public.market_theme_confirmed_evidence.freshness is
    'Freshness state. missing-source, source-error, and insufficient-data must fail closed in future consumers.';
comment on column public.market_theme_confirmed_evidence.evidence_value is
    'Raw or normalized evidence values needed to reconstruct the support judgment.';
comment on column public.market_theme_confirmed_evidence.watchlist_breadth is
    'Watchlist breadth evidence for the trade date, stored as structured JSON for traceability.';
comment on column public.market_theme_confirmed_evidence.support_level is
    'Confirmed support level: confirmed, supporting, weak, or invalidated.';
comment on column public.market_theme_confirmed_evidence.evidence_status is
    'Lifecycle state for the row: confirmed, rejected, or superseded.';
comment on column public.market_theme_confirmed_evidence.lineage is
    'Lineage metadata such as upstream table, source key, run id, snapshot id, rule version, or calculation inputs.';
comment on column public.market_theme_confirmed_evidence.metadata is
    'Forward-compatible metadata that is not required for core reconstruction.';
comment on column public.market_theme_confirmed_evidence.notes is
    'Optional human-readable production review notes.';
comment on column public.market_theme_confirmed_evidence.created_at is
    'Timestamp when this DB row was inserted.';
comment on column public.market_theme_confirmed_evidence.updated_at is
    'Timestamp maintained by future write paths; this SQL does not install triggers.';

create unique index if not exists uq_market_theme_evidence_observation
on public.market_theme_confirmed_evidence (
    trade_date,
    market_index,
    sector_theme_key,
    source_family,
    source_name,
    as_of
);

comment on index public.uq_market_theme_evidence_observation is
    'Uniqueness contract: the same source may publish multiple versions per trade_date/theme only when as_of differs.';

create index if not exists idx_market_theme_evidence_trade_date
on public.market_theme_confirmed_evidence (trade_date);

create index if not exists idx_market_theme_evidence_market_trade_date
on public.market_theme_confirmed_evidence (market_index, trade_date);

create index if not exists idx_market_theme_evidence_theme_trade_date
on public.market_theme_confirmed_evidence (sector_theme_key, trade_date);

create index if not exists idx_market_theme_evidence_source_trade_date
on public.market_theme_confirmed_evidence (source_family, source_name, trade_date);

create index if not exists idx_market_theme_evidence_trade_date_as_of
on public.market_theme_confirmed_evidence (trade_date, as_of desc);

create index if not exists idx_market_theme_evidence_latest_confirmed
on public.market_theme_confirmed_evidence (
    trade_date,
    market_index,
    sector_theme_key,
    as_of desc
)
where evidence_status = 'confirmed'
  and freshness = 'fresh'
  and support_level in ('confirmed', 'supporting');

-- Future read-only reconstruction query shape:
--
-- select *
-- from public.market_theme_confirmed_evidence
-- where trade_date = :trade_date
--   and evidence_status = 'confirmed'
--   and freshness = 'fresh'
-- order by market_index, sector_theme_key, as_of desc;

select 'evidence_phase_4_market_theme_confirmed_evidence.sql complete' as sql_artifact_validation_marker;
