# Evidence Chain Production Closure Gap Assessment

This assessment is repo-side only. It did not run production SQL, write
Supabase, run formal backfill, change RLS/grants, or send Telegram.

## Schema Decision

schema_decision: no-schema-change

`public.market_theme_confirmed_evidence` is sufficient for the next non-live
steps: Owner manual review, read-only verification, manual backfill template
review, and read-only smoke. Production closure is not complete until Owner
executes the approved production steps and provides read-only production rows.

## Current Table Contract

| contract item | repo evidence | conclusion |
| --- | --- | --- |
| table and required fields | `db/sql/evidence_phase_4_market_theme_confirmed_evidence.sql` defines `trade_date`, `as_of`, `market_index`, `sector_theme_key`, `source_family`, `source_name`, `freshness`, `evidence_value`, `watchlist_breadth`, `support_level`, `evidence_status`, `lineage`, `metadata`, and `notes`. | sufficient |
| loader selected fields | `services/market_theme_evidence_store.py` `SELECT_FIELDS` reads the same fields needed for reconstruction. | sufficient |
| confirmed condition | loader accepts only `support_level in ('confirmed','supporting')`, `evidence_status='confirmed'`, and `freshness='fresh'`. | sufficient |
| unsupported support level | loader treats `support_level='strong'` as `source-error`; ingestion validation also rejects it. | sufficient |
| structured evidence payload | schema stores `evidence_value`, `watchlist_breadth`, `lineage`, and `metadata` as JSONB objects; validation requires object payloads before SQL rendering. | sufficient |
| uniqueness for manual upsert | schema and rendered handoff SQL use `(trade_date, market_index, sector_theme_key, source_family, source_name, as_of)`. | sufficient |

## Required For Read-only Smoke

| requirement | repo artifact | fail-closed behavior |
| --- | --- | --- |
| env | `scripts/smoke_market_theme_evidence_readonly.py` requires `SUPABASE_URL` and `SUPABASE_READONLY_KEY`; it does not fall back to service-role keys. | missing env returns `fail-closed`, `telegram_confirmed: false` |
| permission | smoke calls the loader through a read-only client. | permission errors return `fail-closed`, `table_read: permission-denied` |
| production rows | loader needs at least one row that passes the confirmed condition. | 0 rows, stale rows, unsupported values, and incomplete rows stay unconfirmed |
| output contract | smoke output includes `mode: read-only`, `write: disabled`, `schema_decision: no-schema-change`, row count, status, and `telegram_confirmed`. | non-ok statuses exit 2 |

## Required For Manual Backfill

| requirement | repo artifact | owner/manual boundary |
| --- | --- | --- |
| approved persistent source | `validate_market_theme_evidence_ingestion_payload` allows only `production_db`, `owner_approved_persistent`, or `market_data`. | local/runtime/cache/worktree/report-derived/synthetic/default/test/fixture sources fail closed |
| lineage | validation requires `lineage` as an object. | Owner must provide source lineage before any manual SQL is reviewed |
| freshness and status | validation requires `freshness='fresh'`, `evidence_status='confirmed'`, and support level `confirmed` or `supporting`. | stale/rejected/weak/strong payloads do not render SQL |
| manual SQL | `db/sql/evidence_chain_market_theme_ops_manual_template.sql` and rendered handoff SQL are manual-only artifacts. | agents must not execute them; Owner approval is required |
| verification | SQL template Step D and `docs/handoff/evidence_phase_4_market_theme_confirmed_evidence_readonly_verification.sql` provide read-only verification queries. | results prove only observed state, not production closure |

## Production Closure Matrix

| area | current repo-side status | remaining production gap |
| --- | --- | --- |
| schema | no-schema-change; schema artifact and Owner hard schema PASS are compatible with loader and validation contracts. | Owner must keep production table aligned with the verified schema. |
| ingestion validation | dry-run validation exists and rejects fake/local/runtime/test sources. | no live ingestion provider is enabled in this task. |
| manual backfill | manual SQL template and validation-to-SQL path exist. | Owner must approve source data, placeholders, and execution separately. |
| read-only smoke | smoke exists and uses only `SUPABASE_READONLY_KEY`. | requires Owner-provided read-only env and production rows. |
| RLS / grant | manual SQL template has optional grant/RLS sections and read-only verification. | production role/policy names and execution remain Owner decisions. |
| Telegram confirmed consumption | loader can produce confirmed evidence only from production rows and fails closed otherwise. | Telegram remains unconfirmed until production rows pass the loader contract. |

## Next Manual Steps

1. Owner reviews the no-schema-change evidence matrix above.
2. Owner runs read-only schema verification SQL if production state needs to be
   rechecked.
3. Owner prepares approved payload rows with persistent source, lineage, fresh
   status, and confirmed/supporting support level.
4. Tech/Owner may dry-run validation locally with
   `python scripts/validate_market_theme_evidence_ingestion.py --input payload.json`.
5. Owner manually reviews any generated SQL before execution.
6. GitHub read-only smoke can run only after `SUPABASE_URL` and
   `SUPABASE_READONLY_KEY` are configured.

## Not Done

- no live Supabase write
- no formal backfill
- no production RLS/grant change
- no live Telegram delivery
- no strategy threshold change
- no production closure claim
