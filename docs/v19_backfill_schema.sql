-- v19.0 backfill schema draft only.
-- Do not run this until unit tests and dry-run replay are reviewed.

create table if not exists daily_price (
    stock_id text not null,
    trade_date date not null,
    open numeric,
    high numeric,
    low numeric,
    close numeric not null,
    volume numeric,
    source text not null default 'replay',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (stock_id, trade_date)
);

create table if not exists daily_signal_snapshot (
    stock_id text not null,
    trade_date date not null,
    version text not null,
    close numeric not null,
    volume_ratio numeric,
    pattern text,
    market_state text,
    structure_state text,
    position_state text,
    rr numeric,
    score numeric,
    heat_level integer,
    action text,
    reasons jsonb,
    is_tradeable boolean not null default false,
    is_best_candidate boolean not null default false,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (stock_id, trade_date, version)
);

create index if not exists idx_daily_signal_snapshot_trade_date
    on daily_signal_snapshot (trade_date);

create index if not exists idx_daily_signal_snapshot_tradeable
    on daily_signal_snapshot (version, is_tradeable, is_best_candidate);
