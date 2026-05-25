-- v19.3 position execution schema.
-- Run in Supabase SQL Editor before deploying the Telegram Edge Function.
-- The Edge Function should use the Supabase service role key, not the anon key.

create extension if not exists pgcrypto;

create table if not exists positions (
    stock_code text primary key,
    stock_name text not null,
    shares integer not null check (shares >= 0),
    avg_price numeric not null default 0 check (avg_price >= 0),
    realized_profit_taken_ratio numeric not null default 0
        check (realized_profit_taken_ratio >= 0 and realized_profit_taken_ratio <= 1),
    last_realized_profit_date date,
    status text not null default 'ACTIVE'
        check (status in ('ACTIVE', 'CLOSED')),
    source text not null default 'manual'
        check (source in ('manual', 'telegram', 'fallback')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

alter table positions enable row level security;

create table if not exists position_events (
    id uuid primary key default gen_random_uuid(),
    stock_code text not null references positions(stock_code),
    stock_name text not null,
    event_date date not null default ((timezone('Asia/Taipei', now()))::date),
    event_type text not null
        check (event_type in (
            'TAKE_PROFIT',
            'REDUCE',
            'ADD',
            'STOP',
            'MANUAL_ADJUST'
        )),
    action_label text not null,
    shares_delta integer not null,
    shares_before integer not null check (shares_before >= 0),
    shares_after integer not null check (shares_after >= 0),
    avg_price_before numeric,
    avg_price_after numeric,
    realized_profit_delta numeric not null default 0
        check (realized_profit_delta >= 0 and realized_profit_delta <= 1),
    realized_profit_taken_ratio_after numeric not null default 0
        check (
            realized_profit_taken_ratio_after >= 0
            and realized_profit_taken_ratio_after <= 1
        ),
    telegram_callback_id text,
    telegram_chat_id text,
    telegram_message_id text,
    payload jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

alter table position_events enable row level security;

create or replace function set_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

drop trigger if exists trg_positions_updated_at on positions;
create trigger trg_positions_updated_at
before update on positions
for each row
execute function set_updated_at();

create unique index if not exists idx_position_events_callback_id
    on position_events (telegram_callback_id)
    where telegram_callback_id is not null;

create index if not exists idx_position_events_stock_date
    on position_events (stock_code, event_date desc);

create index if not exists idx_positions_status
    on positions (status);

insert into positions (
    stock_code,
    stock_name,
    shares,
    avg_price,
    realized_profit_taken_ratio,
    last_realized_profit_date,
    status,
    source
) values
    ('3231', '緯創', 440, 140.92, 0, null, 'ACTIVE', 'manual'),
    ('2421', '建準', 0, 0, 0, null, 'CLOSED', 'manual'),
    ('3035', '智原', 50, 209, 0, null, 'ACTIVE', 'manual'),
    ('2303', '聯電', 0, 0, 0, null, 'CLOSED', 'manual'),
    ('3481', '群創', 0, 0, 0, null, 'CLOSED', 'manual'),
    ('2344', '華邦電', 0, 0, 0, null, 'CLOSED', 'manual'),
    ('2376', '技嘉', 0, 0, 0, null, 'CLOSED', 'manual'),
    ('2408', '南亞科', 0, 0, 0, null, 'CLOSED', 'manual'),
    ('2356', '英業達', 550, 52.15, 0.5, '2026-05-25', 'ACTIVE', 'manual'),
    ('2324', '仁寶', 0, 0, 0, null, 'CLOSED', 'manual'),
    ('2301', '光寶科', 50, 208.5, 0, null, 'ACTIVE', 'manual'),
    ('2337', '旺宏', 0, 0, 0, null, 'CLOSED', 'manual')
on conflict (stock_code) do update set
    stock_name = excluded.stock_name,
    shares = excluded.shares,
    avg_price = excluded.avg_price,
    realized_profit_taken_ratio = excluded.realized_profit_taken_ratio,
    last_realized_profit_date = excluded.last_realized_profit_date,
    status = excluded.status,
    source = excluded.source,
    updated_at = now();
