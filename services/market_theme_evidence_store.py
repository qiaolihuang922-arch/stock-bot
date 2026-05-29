import json
import os


TABLE_NAME = "market_theme_confirmed_evidence"
SELECT_FIELDS = (
    "market_index,sector_theme_key,trade_date,as_of,freshness,"
    "evidence_status,support_level,evidence_value,watchlist_breadth,"
    "source_family,source_name,lineage,metadata"
)
ALLOWED_SUPPORT_LEVELS = {"confirmed", "supporting", "weak", "invalidated"}
CONFIRMED_SUPPORT_LEVELS = {"confirmed", "supporting"}
HANDOFF_ALLOWED_SOURCE_FAMILIES = {
    "production_db",
    "owner_approved_persistent",
    "market_data",
}
HANDOFF_FORBIDDEN_SOURCE_FAMILIES = {
    "runtime",
    "runtime_diagnostic",
    "local",
    "cache",
    "worktree",
    "test_fixture",
    "test fixture",
    "report_derived",
    "synthetic",
    "default",
    "fixture",
}
REQUIRED_ROW_FIELDS = {
    "market_index",
    "sector_theme_key",
    "trade_date",
    "as_of",
    "freshness",
    "evidence_status",
    "support_level",
    "evidence_value",
    "watchlist_breadth",
    "source_family",
    "source_name",
    "lineage",
}


def _config_value(name):
    try:
        import config
    except Exception:
        return ""
    return getattr(config, name, "") or ""


def _build_client():
    supabase_url = os.environ.get("SUPABASE_URL") or _config_value("SUPABASE_URL")
    supabase_key = (
        os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        or _config_value("SUPABASE_SERVICE_ROLE_KEY")
        or os.environ.get("SUPABASE_KEY")
        or _config_value("SUPABASE_KEY")
    )
    if not supabase_url or not supabase_key:
        return None

    from supabase import create_client

    return create_client(supabase_url, supabase_key)


def _empty_result(status, reason):
    return {
        "status": status,
        "confirmed": False,
        "source_of_truth": "production_db",
        "source_family": "production_db",
        "source_status": status,
        "reason": reason,
        "sources": [],
        "rows": [],
    }


def _empty_handoff(status, reason):
    return {
        "status": status,
        "confirmed": False,
        "handoff_ready": False,
        "reason": reason,
        "live_write": False,
        "target_table": f"public.{TABLE_NAME}",
        "rows": [],
        "sql": "",
    }


def _missing_fields(row):
    return sorted(
        field
        for field in REQUIRED_ROW_FIELDS
        if field not in row or row.get(field) in (None, "")
    )


def _source_family_forbidden(source_family):
    family = str(source_family or "").lower()
    return (
        family in HANDOFF_FORBIDDEN_SOURCE_FAMILIES
        or family.startswith("runtime")
        or family.startswith("local")
        or family.startswith("cache")
        or family.startswith("worktree")
        or family.startswith("test")
    )


def _normalize_handoff_row(payload):
    row = {
        "trade_date": payload.get("trade_date"),
        "as_of": payload.get("as_of"),
        "market_index": payload.get("market_index"),
        "sector_theme_key": payload.get("sector_theme_key"),
        "source_family": payload.get("source_family"),
        "source_name": payload.get("source_name"),
        "freshness": str(payload.get("freshness") or "").lower(),
        "evidence_value": payload.get("evidence_value"),
        "watchlist_breadth": payload.get("watchlist_breadth"),
        "support_level": str(payload.get("support_level") or "").lower(),
        "evidence_status": str(payload.get("evidence_status") or "").lower(),
        "lineage": payload.get("lineage"),
        "metadata": payload.get("metadata") or {},
        "notes": payload.get("notes"),
    }
    return row


def _validate_handoff_row(row):
    if not isinstance(row, dict):
        return "row must be an object"
    missing = [
        field for field in REQUIRED_ROW_FIELDS
        if field not in row or row.get(field) in (None, "")
    ]
    if missing:
        return f"required fields missing: {', '.join(missing)}"
    source_family = str(row.get("source_family") or "").lower()
    if _source_family_forbidden(source_family):
        return "source_family is local/runtime/synthetic and cannot be handed off"
    if source_family not in HANDOFF_ALLOWED_SOURCE_FAMILIES:
        return "source_family is not an approved true source"
    if row.get("support_level") not in CONFIRMED_SUPPORT_LEVELS:
        return "support_level is not confirmed/supporting"
    if row.get("evidence_status") != "confirmed":
        return "evidence_status is not confirmed"
    if row.get("freshness") != "fresh":
        return "freshness is not fresh"
    if not isinstance(row.get("evidence_value"), dict):
        return "evidence_value must be an object"
    if not isinstance(row.get("watchlist_breadth"), dict):
        return "watchlist_breadth must be an object"
    if not isinstance(row.get("lineage"), dict):
        return "lineage must be an object"
    if not isinstance(row.get("metadata"), dict):
        return "metadata must be an object"
    return None


def _sql_literal(value):
    if value is None:
        return "null"
    return "'" + str(value).replace("'", "''") + "'"


def _jsonb_literal(value):
    return _sql_literal(json.dumps(value or {}, ensure_ascii=False, sort_keys=True)) + "::jsonb"


def render_market_theme_evidence_handoff_sql(rows):
    if not rows:
        return ""
    for row in rows or []:
        reason = _validate_handoff_row(row)
        if reason:
            return ""
    lines = [
        "-- Non-live handoff SQL for public.market_theme_confirmed_evidence.",
        "-- Manual review/execution only. Agents must not run this SQL.",
        "insert into public.market_theme_confirmed_evidence (",
        "    trade_date, as_of, market_index, sector_theme_key,",
        "    source_family, source_name, freshness, evidence_value,",
        "    watchlist_breadth, support_level, evidence_status,",
        "    lineage, metadata, notes",
        ") values",
    ]
    value_lines = []
    for row in rows:
        values = [
            _sql_literal(row.get("trade_date")),
            _sql_literal(row.get("as_of")),
            _sql_literal(row.get("market_index")),
            _sql_literal(row.get("sector_theme_key")),
            _sql_literal(row.get("source_family")),
            _sql_literal(row.get("source_name")),
            _sql_literal(row.get("freshness")),
            _jsonb_literal(row.get("evidence_value")),
            _jsonb_literal(row.get("watchlist_breadth")),
            _sql_literal(row.get("support_level")),
            _sql_literal(row.get("evidence_status")),
            _jsonb_literal(row.get("lineage")),
            _jsonb_literal(row.get("metadata")),
            _sql_literal(row.get("notes")),
        ]
        value_lines.append("    (" + ", ".join(values) + ")")
    lines.append(",\n".join(value_lines) + "\n")
    lines.extend([
        "on conflict (trade_date, market_index, sector_theme_key, source_family, source_name, as_of)",
        "do update set",
        "    freshness = excluded.freshness,",
        "    evidence_value = excluded.evidence_value,",
        "    watchlist_breadth = excluded.watchlist_breadth,",
        "    support_level = excluded.support_level,",
        "    evidence_status = excluded.evidence_status,",
        "    lineage = excluded.lineage,",
        "    metadata = excluded.metadata,",
        "    notes = excluded.notes,",
        "    updated_at = now();",
    ])
    return "\n".join(lines)


def build_market_theme_evidence_handoff(payloads):
    rows = []
    for payload in payloads or []:
        if not isinstance(payload, dict):
            return _empty_handoff("insufficient-data", "payload is not an object")
        row = _normalize_handoff_row(payload)
        reason = _validate_handoff_row(row)
        if reason:
            return _empty_handoff("insufficient-data", reason)
        rows.append(row)

    if not rows:
        return _empty_handoff("absent", "no handoff payload rows")

    return {
        "status": "ready",
        "confirmed": False,
        "handoff_ready": True,
        "reason": "manual SQL handoff generated; no live write performed",
        "live_write": False,
        "target_table": f"public.{TABLE_NAME}",
        "rows": rows,
        "sql": render_market_theme_evidence_handoff_sql(rows),
    }


def _provider_sources_from_row(row):
    theme_key = str(row.get("sector_theme_key") or "market_theme")
    support_level = str(row.get("support_level") or "").lower()
    evidence_value = row.get("evidence_value") or {}
    watchlist_breadth = row.get("watchlist_breadth") or {}
    lineage = row.get("lineage") or {}
    source_name = row.get("source_name") or "market_theme_confirmed_evidence"
    base = {
        "source_family": "production_db",
        "source_name": source_name,
        "as_of": row.get("as_of"),
        "freshness": "fresh",
        "freshness_reason": "same_trade_date",
        "level": "supportive",
        "support_level": support_level,
        "evidence_status": row.get("evidence_status"),
        "trade_date": row.get("trade_date"),
        "theme": theme_key,
        "theme_label": theme_key,
        "source_of_truth": "production_db",
        "lineage": lineage,
        "limitations": ["production confirmed evidence；不改變個股買點"],
    }
    return [
        {
            **base,
            "source_type": "watchlist_breadth",
            "source_name": f"{source_name}:watchlist_breadth",
            "supports_claims": [f"watchlist_breadth supports {theme_key}"],
            "evidence_value": watchlist_breadth,
        },
        {
            **base,
            "source_type": "sector_index",
            "source_name": f"{source_name}:sector_theme",
            "supports_claims": [
                f"{row.get('market_index')} {theme_key} support_level={support_level}"
            ],
            "evidence_value": evidence_value,
        },
    ]


def _confirmed_row(row):
    return (
        str(row.get("support_level") or "").lower() in CONFIRMED_SUPPORT_LEVELS
        and str(row.get("evidence_status") or "").lower() == "confirmed"
        and str(row.get("freshness") or "").lower() == "fresh"
    )


def _result_from_confirmed_row(row):
    sources = _provider_sources_from_row(row)
    return {
        "status": "confirmed",
        "confirmed": True,
        "source_of_truth": "production_db",
        "source_family": "production_db",
        "source_status": "ready",
        "support_level": str(row.get("support_level") or "").lower(),
        "freshness": str(row.get("freshness") or "").lower(),
        "evidence_status": str(row.get("evidence_status") or "").lower(),
        "market_index": row.get("market_index"),
        "sector_theme_key": row.get("sector_theme_key"),
        "trade_date": row.get("trade_date"),
        "as_of": row.get("as_of"),
        "sources": sources,
        "rows": [row],
    }


def _validate_rows(rows):
    for row in rows:
        if not isinstance(row, dict):
            return _empty_result("source-error", "row is not an object")
        support_level = str(row.get("support_level") or "").lower()
        if support_level not in ALLOWED_SUPPORT_LEVELS:
            return _empty_result("source-error", "unexpected support_level")

    confirmed_rows = [
        row for row in rows
        if not _missing_fields(row) and _confirmed_row(row)
    ]
    if confirmed_rows:
        return _result_from_confirmed_row(confirmed_rows[0])

    if any(_missing_fields(row) for row in rows):
        return _empty_result("insufficient-data", "required fields missing")
    return _empty_result("insufficient-data", "no fresh confirmed production row")


def load_confirmed_market_theme_evidence(client=None, trade_date=None, limit=20):
    if client is None:
        try:
            client = _build_client()
        except Exception as exc:
            return _empty_result("source-error", str(exc))
    if client is None:
        return _empty_result("missing-source", "production DB config missing")

    try:
        query = client.table(TABLE_NAME).select(SELECT_FIELDS)
        if trade_date:
            query = query.eq("trade_date", trade_date)
        rows = (
            query
            .order("as_of", desc=True)
            .limit(limit)
            .execute()
            .data
            or []
        )
    except Exception as exc:
        return _empty_result("source-error", str(exc))

    if not rows:
        return _empty_result("absent", "production table returned no rows")
    return _validate_rows(rows)
