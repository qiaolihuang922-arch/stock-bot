-- v20.0 Strategy Evidence Foundation schema draft.
-- Review in QA before running against production.

create table if not exists market_daily_bars (
    stock_id text not null,
    trade_date date not null,
    open numeric not null,
    high numeric not null,
    low numeric not null,
    close numeric not null,
    volume numeric not null,
    turnover numeric,
    source text not null default 'daily_close',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (stock_id, trade_date, source)
);

create table if not exists strategy_feature_snapshots (
    stock_id text not null,
    trade_date date not null,
    strategy_version text not null,
    price numeric,
    change_pct numeric,
    chg_1d numeric,
    chg_3d numeric,
    chg_5d numeric,
    chg_10d numeric,
    vol_ratio_5 numeric,
    vol_ratio_10 numeric,
    breakout_distance numeric,
    rr numeric,
    score numeric,
    confidence numeric,
    market_state text,
    trend text,
    structure_state text,
    structure_phase text,
    volume_state text,
    heat_state text,
    trade_state text,
    decision text,
    action numeric,
    is_tradeable boolean not null default false,
    is_best_candidate boolean not null default false,
    watch_category text not null,
    reject_family text,
    blockers jsonb,
    raw_reason_summary text,
    audit_category text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (stock_id, trade_date, strategy_version)
);

create table if not exists strategy_outcome_metrics (
    stock_id text not null,
    trade_date date not null,
    strategy_version text not null,
    watch_category text,
    reject_family text,
    horizon_days integer not null,
    close_return_pct numeric,
    relative_return_pct numeric,
    max_favorable_excursion_pct numeric,
    max_adverse_excursion_pct numeric,
    hit_breakout_after_signal boolean not null default false,
    hit_stop_like_drawdown boolean not null default false,
    best_entry_gap_pct numeric,
    outcome_label text not null default 'pending',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (stock_id, trade_date, strategy_version, horizon_days)
);

create table if not exists strategy_classification_audit (
    stock_id text not null,
    trade_date date not null,
    strategy_version text not null,
    original_category text,
    suggested_audit_category text not null,
    distortion_type text not null,
    evidence_summary text,
    severity text not null default 'medium',
    review_status text not null default 'open',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (stock_id, trade_date, strategy_version, distortion_type)
);

create table if not exists market_events (
    id bigserial primary key,
    stock_id text,
    event_type text not null,
    title text,
    summary text,
    source_name text not null,
    source_url text not null,
    published_at timestamptz not null,
    market_effective_at timestamptz not null,
    ingested_at timestamptz not null default now(),
    dedupe_key text not null unique,
    confidence numeric,
    reliability numeric,
    tags jsonb
);

create index if not exists idx_strategy_feature_category
    on strategy_feature_snapshots (strategy_version, watch_category, trade_date);

create index if not exists idx_strategy_outcome_category
    on strategy_outcome_metrics (strategy_version, watch_category, horizon_days);

create index if not exists idx_strategy_audit_open
    on strategy_classification_audit (strategy_version, review_status, trade_date);
