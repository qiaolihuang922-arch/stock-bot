-- Read-only schema verification for public.market_theme_confirmed_evidence.
-- Run this in Supabase SQL editor only when connected to the intended
-- production project. Return every result set to the reviewer.
-- This file only reads metadata from information_schema and pg_catalog.
-- Important: this script helps collect and summarize schema metadata, but the
-- raw check constraints result set is the source of truth for allowed values.
-- Do not declare production schema pass from the summary rows alone if raw
-- constraints include extra allowed values not present in the SQL artifact.

select
    'table exists' as item,
    'public.market_theme_confirmed_evidence' as expected,
    to_regclass('public.market_theme_confirmed_evidence')::text as observed,
    case
        when to_regclass('public.market_theme_confirmed_evidence') is null then 'fail'
        else 'pass'
    end as result;

select
    'columns' as item,
    column_name,
    data_type,
    udt_name,
    is_nullable,
    column_default,
    ordinal_position
from information_schema.columns
where table_schema = 'public'
  and table_name = 'market_theme_confirmed_evidence'
order by ordinal_position;

select
    'expected columns' as item,
    expected.ordinal_position,
    expected.column_name,
    expected.data_type,
    expected.is_nullable,
    expected.column_default_pattern
from (
    values
        (1, 'id', 'bigint', 'NO', 'nextval'),
        (2, 'trade_date', 'date', 'NO', null),
        (3, 'as_of', 'timestamp with time zone', 'NO', null),
        (4, 'market_index', 'text', 'NO', null),
        (5, 'sector_theme_key', 'text', 'NO', null),
        (6, 'source_family', 'text', 'NO', null),
        (7, 'source_name', 'text', 'NO', null),
        (8, 'freshness', 'text', 'NO', null),
        (9, 'evidence_value', 'jsonb', 'NO', '''{}''::jsonb'),
        (10, 'watchlist_breadth', 'jsonb', 'NO', '''{}''::jsonb'),
        (11, 'support_level', 'text', 'NO', null),
        (12, 'evidence_status', 'text', 'NO', '''confirmed''::text'),
        (13, 'lineage', 'jsonb', 'NO', '''{}''::jsonb'),
        (14, 'metadata', 'jsonb', 'NO', '''{}''::jsonb'),
        (15, 'notes', 'text', 'YES', null),
        (16, 'created_at', 'timestamp with time zone', 'NO', 'now()'),
        (17, 'updated_at', 'timestamp with time zone', 'NO', 'now()')
) as expected(ordinal_position, column_name, data_type, is_nullable, column_default_pattern)
order by expected.ordinal_position;

select
    'column comparison' as item,
    expected.ordinal_position,
    expected.column_name,
    expected.data_type as expected_type,
    observed.data_type as observed_type,
    expected.is_nullable as expected_nullable,
    observed.is_nullable as observed_nullable,
    expected.column_default_pattern as expected_default_pattern,
    observed.column_default as observed_default,
    case
        when observed.column_name is null then 'fail: missing column'
        when observed.data_type <> expected.data_type then 'fail: type mismatch'
        when observed.is_nullable <> expected.is_nullable then 'fail: nullability mismatch'
        when expected.column_default_pattern is not null
            and coalesce(observed.column_default, '') not like '%' || expected.column_default_pattern || '%'
            then 'fail: default mismatch'
        else 'pass'
    end as result
from (
    values
        (1, 'id', 'bigint', 'NO', 'nextval'),
        (2, 'trade_date', 'date', 'NO', null),
        (3, 'as_of', 'timestamp with time zone', 'NO', null),
        (4, 'market_index', 'text', 'NO', null),
        (5, 'sector_theme_key', 'text', 'NO', null),
        (6, 'source_family', 'text', 'NO', null),
        (7, 'source_name', 'text', 'NO', null),
        (8, 'freshness', 'text', 'NO', null),
        (9, 'evidence_value', 'jsonb', 'NO', '''{}''::jsonb'),
        (10, 'watchlist_breadth', 'jsonb', 'NO', '''{}''::jsonb'),
        (11, 'support_level', 'text', 'NO', null),
        (12, 'evidence_status', 'text', 'NO', '''confirmed''::text'),
        (13, 'lineage', 'jsonb', 'NO', '''{}''::jsonb'),
        (14, 'metadata', 'jsonb', 'NO', '''{}''::jsonb'),
        (15, 'notes', 'text', 'YES', null),
        (16, 'created_at', 'timestamp with time zone', 'NO', 'now()'),
        (17, 'updated_at', 'timestamp with time zone', 'NO', 'now()')
) as expected(ordinal_position, column_name, data_type, is_nullable, column_default_pattern)
left join information_schema.columns observed
  on observed.table_schema = 'public'
 and observed.table_name = 'market_theme_confirmed_evidence'
 and observed.column_name = expected.column_name
order by expected.ordinal_position;

select
    'unexpected columns' as item,
    observed.ordinal_position,
    observed.column_name,
    observed.data_type,
    observed.is_nullable,
    observed.column_default
from information_schema.columns observed
where observed.table_schema = 'public'
  and observed.table_name = 'market_theme_confirmed_evidence'
  and observed.column_name not in (
      'id',
      'trade_date',
      'as_of',
      'market_index',
      'sector_theme_key',
      'source_family',
      'source_name',
      'freshness',
      'evidence_value',
      'watchlist_breadth',
      'support_level',
      'evidence_status',
      'lineage',
      'metadata',
      'notes',
      'created_at',
      'updated_at'
  )
order by observed.ordinal_position;

select
    'check constraints' as item,
    c.conname,
    pg_get_constraintdef(c.oid) as constraint_def
from pg_constraint c
join pg_class t on t.oid = c.conrelid
join pg_namespace n on n.oid = t.relnamespace
where n.nspname = 'public'
  and t.relname = 'market_theme_confirmed_evidence'
  and c.contype = 'c'
order by c.conname;

select
    'freshness values' as item,
    array['fresh', 'stale', 'missing-source', 'source-error', 'insufficient-data'] as expected_values,
    case
        when exists (
            select 1
            from pg_constraint c
            join pg_class t on t.oid = c.conrelid
            join pg_namespace n on n.oid = t.relnamespace
            where n.nspname = 'public'
              and t.relname = 'market_theme_confirmed_evidence'
              and c.contype = 'c'
              and pg_get_constraintdef(c.oid) like '%freshness%'
              and pg_get_constraintdef(c.oid) like '%fresh%'
              and pg_get_constraintdef(c.oid) like '%stale%'
              and pg_get_constraintdef(c.oid) like '%missing-source%'
              and pg_get_constraintdef(c.oid) like '%source-error%'
              and pg_get_constraintdef(c.oid) like '%insufficient-data%'
        ) then 'pass'
        else 'fail'
    end as result;

select
    'support_level values' as item,
    array['confirmed', 'supporting', 'weak', 'invalidated'] as expected_values,
    case
        when exists (
            select 1
            from pg_constraint c
            join pg_class t on t.oid = c.conrelid
            join pg_namespace n on n.oid = t.relnamespace
            where n.nspname = 'public'
              and t.relname = 'market_theme_confirmed_evidence'
              and c.contype = 'c'
              and pg_get_constraintdef(c.oid) like '%support_level%'
              and pg_get_constraintdef(c.oid) like '%confirmed%'
              and pg_get_constraintdef(c.oid) like '%supporting%'
              and pg_get_constraintdef(c.oid) like '%weak%'
              and pg_get_constraintdef(c.oid) like '%invalidated%'
        ) then 'pass'
        else 'fail'
    end as result;

select
    'evidence_status values' as item,
    array['confirmed', 'rejected', 'superseded'] as expected_values,
    case
        when exists (
            select 1
            from pg_constraint c
            join pg_class t on t.oid = c.conrelid
            join pg_namespace n on n.oid = t.relnamespace
            where n.nspname = 'public'
              and t.relname = 'market_theme_confirmed_evidence'
              and c.contype = 'c'
              and pg_get_constraintdef(c.oid) like '%evidence_status%'
              and pg_get_constraintdef(c.oid) like '%confirmed%'
              and pg_get_constraintdef(c.oid) like '%rejected%'
              and pg_get_constraintdef(c.oid) like '%superseded%'
        ) then 'pass'
        else 'fail'
    end as result;

select
    'indexes' as item,
    indexname,
    indexdef
from pg_indexes
where schemaname = 'public'
  and tablename = 'market_theme_confirmed_evidence'
order by indexname;

select
    'expected indexes' as item,
    expected.indexname,
    expected.required_terms
from (
    values
        ('uq_market_theme_evidence_observation', array['trade_date', 'market_index', 'sector_theme_key', 'source_family', 'source_name', 'as_of']),
        ('idx_market_theme_evidence_trade_date', array['trade_date']),
        ('idx_market_theme_evidence_market_trade_date', array['market_index', 'trade_date']),
        ('idx_market_theme_evidence_theme_trade_date', array['sector_theme_key', 'trade_date']),
        ('idx_market_theme_evidence_source_trade_date', array['source_family', 'source_name', 'trade_date']),
        ('idx_market_theme_evidence_trade_date_as_of', array['trade_date', 'as_of']),
        ('idx_market_theme_evidence_latest_confirmed', array['trade_date', 'market_index', 'sector_theme_key', 'as_of', 'evidence_status', 'freshness', 'support_level'])
) as expected(indexname, required_terms)
order by expected.indexname;

select
    'index comparison' as item,
    expected.indexname,
    observed.indexdef,
    case
        when observed.indexname is null then 'fail: missing index'
        when exists (
            select 1
            from unnest(expected.required_terms) as term(required_term)
            where observed.indexdef not like '%' || term.required_term || '%'
        ) then 'fail: missing expected term'
        else 'pass'
    end as result
from (
    values
        ('uq_market_theme_evidence_observation', array['trade_date', 'market_index', 'sector_theme_key', 'source_family', 'source_name', 'as_of']),
        ('idx_market_theme_evidence_trade_date', array['trade_date']),
        ('idx_market_theme_evidence_market_trade_date', array['market_index', 'trade_date']),
        ('idx_market_theme_evidence_theme_trade_date', array['sector_theme_key', 'trade_date']),
        ('idx_market_theme_evidence_source_trade_date', array['source_family', 'source_name', 'trade_date']),
        ('idx_market_theme_evidence_trade_date_as_of', array['trade_date', 'as_of']),
        ('idx_market_theme_evidence_latest_confirmed', array['trade_date', 'market_index', 'sector_theme_key', 'as_of', 'evidence_status', 'freshness', 'support_level'])
) as expected(indexname, required_terms)
left join pg_indexes observed
  on observed.schemaname = 'public'
 and observed.tablename = 'market_theme_confirmed_evidence'
 and observed.indexname = expected.indexname
order by expected.indexname;

select
    'latest confirmed partial index' as item,
    observed.indexdef as observed,
    case
        when observed.indexname is null then 'fail: missing index'
        when lower(observed.indexdef) like '%idx_market_theme_evidence_latest_confirmed%'
         and lower(observed.indexdef) like '%as_of desc%'
         and lower(observed.indexdef) like '%evidence_status = ''confirmed''%'
         and lower(observed.indexdef) like '%freshness = ''fresh''%'
         and lower(observed.indexdef) like '%support_level = any%'
         and lower(observed.indexdef) like '%confirmed%'
         and lower(observed.indexdef) like '%supporting%'
            then 'pass'
        else 'fail'
    end as result
from (values ('idx_market_theme_evidence_latest_confirmed')) as expected(indexname)
left join pg_indexes observed
  on observed.schemaname = 'public'
 and observed.tablename = 'market_theme_confirmed_evidence'
 and observed.indexname = expected.indexname;

select
    'comments' as item,
    'table' as comment_scope,
    obj_description(to_regclass('public.market_theme_confirmed_evidence')::oid, 'pg_class') as observed_comment;

select
    'comments' as item,
    c.ordinal_position,
    c.column_name,
    col_description(to_regclass('public.market_theme_confirmed_evidence')::oid, c.ordinal_position) as observed_comment
from information_schema.columns c
where c.table_schema = 'public'
  and c.table_name = 'market_theme_confirmed_evidence'
order by c.ordinal_position;

select
    'verification summary' as item,
    'Use result sets above to fill the TASK.md verification matrix. A fail row in hard schema, constraints, or indexes means blocked. Missing comments are warning only unless the SQL contract changes.' as reviewer_instruction;
