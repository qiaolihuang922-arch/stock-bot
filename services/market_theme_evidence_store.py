import os


TABLE_NAME = "market_theme_confirmed_evidence"
SELECT_FIELDS = (
    "market_index,sector_theme_key,trade_date,as_of,freshness,"
    "evidence_status,support_level,evidence_value,watchlist_breadth,"
    "source_family,source_name,lineage,metadata"
)
ALLOWED_SUPPORT_LEVELS = {"confirmed", "supporting", "weak", "invalidated"}
CONFIRMED_SUPPORT_LEVELS = {"confirmed", "supporting"}
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


def _missing_fields(row):
    return sorted(
        field
        for field in REQUIRED_ROW_FIELDS
        if field not in row or row.get(field) in (None, "")
    )


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
