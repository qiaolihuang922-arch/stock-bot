-- v19.2 migration for DB-driven positions.
-- Run after v19_position_execution_schema.sql if the table already exists.

alter table positions
    drop constraint if exists positions_avg_price_check;

alter table positions
    alter column avg_price set default 0;

alter table positions
    add constraint positions_avg_price_check check (avg_price >= 0);

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
on conflict (stock_code) do nothing;

update positions
set status = case when shares > 0 then 'ACTIVE' else 'CLOSED' end,
    updated_at = now();
