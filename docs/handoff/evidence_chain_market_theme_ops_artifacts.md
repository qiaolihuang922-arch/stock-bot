# Evidence Chain Market/Theme Ops Artifacts

This handoff is repo-side only. It did not perform live Supabase writes, formal
backfill, production RLS changes, read-only role changes, or Telegram delivery.
It is not evidence that production ingestion is live.

## Boundary

| item | repo artifact | live side effect | Owner approval needed | status |
| --- | --- | --- | --- | --- |
| ingestion payload validation | `scripts/validate_market_theme_evidence_ingestion.py` | none | no, for dry-run validation | ready |
| approval package generator | `scripts/generate_evidence_approval_package.py` | none | yes, before any SQL execution outside the script | ready |
| manual SQL template | `db/sql/evidence_chain_market_theme_ops_manual_template.sql` | none unless Owner manually executes approved sections | yes | ready |
| read-only smoke | `scripts/smoke_market_theme_evidence_readonly.py` | read-only DB query only | yes, when using production env | ready |
| RLS verification SQL | Step D in the SQL template | read-only catalog/table queries | yes, when running in production | ready |
| production closure gap assessment | `docs/handoff/evidence_chain_production_closure_gap_assessment.md` | none | no, for repo-side review | ready |

## Ingestion Payload Dry-run

Example:

```bash
python scripts/validate_market_theme_evidence_ingestion.py --input payload.json
python scripts/validate_market_theme_evidence_ingestion.py --input payload.json --include-sql
```

Valid rows must use a persistent source family such as `production_db`,
`owner_approved_persistent`, or `market_data`, with `freshness=fresh`,
`evidence_status=confirmed`, and `support_level=confirmed` or `supporting`.
Validation failures return `valid=false`, `may_render_manual_sql=false`,
`live_write=false`, and do not render SQL.

Runtime, local, cache, worktree, report-derived, synthetic, default, test, or
fixture-derived sources must fail closed and must not produce confirmed rows.

## Approval Package Generator

Example:

```bash
python scripts/generate_evidence_approval_package.py \
  --payload approved_payload.json \
  --output-dir artifacts/evidence_approval/2026-05-30
```

The generator writes review artifacts only:

- `approval_package.json`
- `approval_package.md`
- `market_theme_confirmed_evidence_<trade_date>.sql` only when validation passes

The package always marks `schema_decision=no-schema-change`,
`mode=non-live-approval-package`, and `write_execution=disabled`. The SQL
header states that Owner manual approval is required, the agent did not execute
the SQL, and the package is not evidence of production deployment.

Forbidden source families, missing `source_family`, and mixed allowed/forbidden
payloads fail closed and do not render SQL.

## Manual SQL

Use `db/sql/evidence_chain_market_theme_ops_manual_template.sql` only after
Owner approval. The file separates:

- Step A: optional read-only role/grant.
- Step B: optional RLS policy.
- Step C: optional backfill/upsert template.
- Step D: read-only verification queries.

Placeholders such as `:READONLY_ROLE_NAME`,
`:OWNER_APPROVED_SOURCE_NAME`, and `:TRADE_DATE` are intentionally unresolved.
Do not replace them by guessing production role names, auth roles, policy names,
or source names.

This is not a one-click SQL file. Run only the section you intend to verify or
execute, and replace placeholders first. Step A/B/C are commented manual
templates. Step D is read-only, but `:TRADE_DATE` still must be replaced before
running it in Supabase SQL editor.

## Read-only Smoke

Example:

```bash
export SUPABASE_URL="owner-provided-project-url"
export SUPABASE_READONLY_KEY="owner-provided-read-only-key"
python scripts/smoke_market_theme_evidence_readonly.py --trade-date 2026-05-29
```

The smoke intentionally uses `SUPABASE_READONLY_KEY` only. It does not fall back
to service-role keys or generic application keys.

Expected fail-closed shape when no confirmed production rows are available:

```text
market_theme_confirmed_evidence smoke
mode: read-only
write: disabled
schema_decision: no-schema-change
env: present
table_read: ok
rows: 0
status: fail-closed
telegram_confirmed: false
note: no production confirmed evidence available
```

Smoke statuses:

| condition | expected status | telegram_confirmed |
| --- | --- | --- |
| missing env/config | fail-closed | false |
| permission denied | fail-closed | false |
| 0 rows | fail-closed | false |
| stale rows | fail-closed | false |
| unsupported support_level | fail-closed | false |
| valid fresh confirmed/supporting rows | ok | true |

The smoke is allowed to read the production table when production env is
provided. It must not write DB rows, run backfill, mutate RLS/grants, or send
Telegram.
