import json
import os
from datetime import datetime


TABLE_NAME = "market_theme_confirmed_evidence"
TARGET_TABLE = f"public.{TABLE_NAME}"
INDEX_SOURCE_TABLE = "market_theme_index_daily_bars"
MEMBER_SOURCE_TABLE = "sector_theme_members"
DEPRECATED_SOURCE_TABLES = (
    "market_index_daily_bars",
    "sector_theme_daily_bars",
    "market_theme_breadth_daily",
)
UPSERT_CONFLICT_TARGET = (
    "trade_date,market_index,sector_theme_key,source_family,source_name,as_of"
)
WRITE_ENV_NAMES = ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY")
WRITE_SERVICE_KEY_CONFIG_ALIASES = ("SERVICE_ROLE_KEY", "SUPABASE_SERVICE_ROLE_KEY")
_CONFIG_MODULE_UNSET = object()
WRITE_COLUMNS = (
    "trade_date",
    "as_of",
    "market_index",
    "sector_theme_key",
    "source_family",
    "source_name",
    "freshness",
    "evidence_value",
    "watchlist_breadth",
    "support_level",
    "evidence_status",
    "lineage",
    "metadata",
    "notes",
)
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
    "report-derived",
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
AUDIT_MODE = "read-only-production-audit"
AUDIT_MISSING_SOURCE_SEMANTICS = [
    "market_theme_index_daily_bars source rows",
    "sector_theme_members mapping rows",
    "confirmed evidence generation rule",
    "market/theme lineage from production DB columns",
]
AUDIT_SOURCE_TABLE_REASONS = {
    "market_theme_confirmed_evidence": "target confirmed evidence table; rows are read-only status only",
    "market_theme_index_daily_bars": "unified market/sector-theme index source table",
    "sector_theme_members": "persistent theme membership mapping source",
}
AUDIT_DIAGNOSTIC_TABLE_REASONS = {
    "daily_signal_snapshot": "stock-level strategy snapshot; diagnostic only, not market/theme source",
    "signal_runs": "report run metadata; diagnostic only, not market/theme source",
    "signal_items": "report item rows; diagnostic only, not market/theme source",
}
MAX_PREVIOUS_TRADE_DATE_GAP_DAYS = 4
EVIDENCE_TREND_LOOKBACK_ROWS = 20


def _config_value(name):
    try:
        import config
    except Exception:
        return ""
    return getattr(config, name, "") or ""


def _load_config_module():
    try:
        import config
    except Exception:
        return None
    return config


def _config_module_value(config_module, name):
    if config_module is None:
        return ""
    return getattr(config_module, name, "") or ""


def resolve_market_theme_write_credentials(env=None, config_module=_CONFIG_MODULE_UNSET):
    source = env if env is not None else os.environ
    config_source = _load_config_module() if config_module is _CONFIG_MODULE_UNSET else config_module

    supabase_url = source.get("SUPABASE_URL")
    url_source = "env" if supabase_url else ""
    if not supabase_url:
        supabase_url = _config_module_value(config_source, "SUPABASE_URL")
        url_source = "config.SUPABASE_URL" if supabase_url else ""

    service_key = source.get("SUPABASE_SERVICE_ROLE_KEY")
    key_source = "env" if service_key else ""
    if not service_key:
        for alias in WRITE_SERVICE_KEY_CONFIG_ALIASES:
            service_key = _config_module_value(config_source, alias)
            if service_key:
                key_source = f"config.{alias}"
                break

    missing = []
    if not supabase_url:
        missing.append("SUPABASE_URL")
    if not service_key:
        missing.append("SUPABASE_SERVICE_ROLE_KEY|SERVICE_ROLE_KEY")

    return {
        "status": "passed" if not missing else "failed",
        "required": ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY|SERVICE_ROLE_KEY"],
        "missing": missing,
        "url_source": url_source,
        "key_source": key_source,
        "credentials": {
            "SUPABASE_URL": supabase_url,
            "SUPABASE_SERVICE_ROLE_KEY": service_key,
        },
    }


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


def _empty_result(status, reason, rows=None):
    return {
        "status": status,
        "confirmed": False,
        "source_of_truth": "production_db",
        "source_family": "production_db",
        "source_status": status,
        "reason": reason,
        "sources": [],
        "rows": rows or [],
    }


def _empty_handoff(status, reason):
    return {
        "status": status,
        "confirmed": False,
        "handoff_ready": False,
        "reason": reason,
        "live_write": False,
        "target_table": TARGET_TABLE,
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
    family = str(source_family or "").strip().lower()
    return (
        family in HANDOFF_FORBIDDEN_SOURCE_FAMILIES
        or family.startswith("runtime")
        or family.startswith("local")
        or family.startswith("cache")
        or family.startswith("worktree")
        or family.startswith("test")
    )


def _source_family_allowed_for_confirmed_loader(source_family):
    family = str(source_family or "").strip().lower()
    return (
        family in HANDOFF_ALLOWED_SOURCE_FAMILIES
        and not _source_family_forbidden(family)
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


def _safe_text(value):
    return "" if value is None else str(value)


def _default_as_of(trade_date):
    return f"{trade_date}T00:00:00+08:00" if trade_date else ""


def _approval_payload_source_families(payload):
    families = []
    if isinstance(payload, dict) and payload.get("source_family"):
        families.append(payload.get("source_family"))
    for row in payload.get("rows", []) if isinstance(payload, dict) else []:
        if isinstance(row, dict) and row.get("source_family"):
            families.append(row.get("source_family"))
    return families


def _approval_source_guard_reason(payload):
    families = _approval_payload_source_families(payload)
    if not families:
        return "missing source_family"
    for family in families:
        normalized = _safe_text(family).strip().lower()
        if _source_family_forbidden(normalized):
            return "forbidden source_family"
        if normalized not in HANDOFF_ALLOWED_SOURCE_FAMILIES:
            return "source_family is not an approved persistent source"
    return None


def normalize_market_theme_approved_payload(payload):
    """Map an Owner-approved payload into existing table-contract rows."""
    if isinstance(payload, list):
        return payload, None
    if not isinstance(payload, dict):
        return [], "payload must be an object"
    if isinstance(payload.get("payloads"), list):
        return payload["payloads"], None

    guard_reason = _approval_source_guard_reason(payload)
    if guard_reason:
        return [], guard_reason

    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        return [], "rows must be a non-empty array"

    trade_date = payload.get("trade_date")
    source_family = _safe_text(payload.get("source_family")).strip().lower()
    source_name = payload.get("source_name") or "owner_approved_market_theme_review"
    freshness = _safe_text(payload.get("freshness")).strip().lower()
    evidence_status = _safe_text(payload.get("evidence_status")).strip().lower()

    normalized = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            return [], f"rows[{index}] must be an object"
        row_source_family = _safe_text(row.get("source_family") or source_family).strip().lower()
        row_source_name = row.get("source_name") or source_name
        theme = row.get("theme") or row.get("sector_theme_key") or payload.get("sector_theme_key")
        evidence_url = row.get("evidence_url")
        reason = row.get("reason")
        symbol = row.get("symbol")
        normalized.append(
            {
                "market_index": payload.get("market_index") or row.get("market_index") or "TAIEX",
                "sector_theme_key": theme,
                "trade_date": trade_date,
                "as_of": payload.get("as_of") or row.get("as_of") or _default_as_of(trade_date),
                "freshness": freshness,
                "evidence_status": evidence_status,
                "support_level": _safe_text(row.get("support_level")).strip().lower(),
                "evidence_value": row.get("evidence_value")
                or {
                    "symbol": symbol,
                    "theme": theme,
                    "evidence_url": evidence_url,
                    "reason": reason,
                },
                "watchlist_breadth": row.get("watchlist_breadth") or payload.get("watchlist_breadth") or {},
                "source_family": row_source_family,
                "source_name": row_source_name,
                "lineage": row.get("lineage")
                or payload.get("lineage")
                or {
                    "source": row_source_name,
                    "approval_package": True,
                    "row_index": index,
                },
                "metadata": row.get("metadata")
                or payload.get("metadata")
                or {
                    "manual_approval_required": True,
                    "write_interface": "scripts/write_market_theme_confirmed_evidence.py",
                },
                "notes": row.get("notes") or reason or "Owner-approved persistent evidence package row",
            }
        )
    return normalized, None


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


def _query_execute(query):
    return query.execute()


def _select_count_rows(client, table, fields="*", filters=None, limit=1000):
    filters = filters or []
    try:
        try:
            query = client.table(table).select(fields, count="exact")
        except TypeError:
            query = client.table(table).select(fields)
        for method_name, args in filters:
            method = getattr(query, method_name)
            query = method(*args)
        if limit:
            query = query.limit(limit)
        result = _query_execute(query)
        rows = result.data or []
        count = getattr(result, "count", None)
        return {
            "status": "ok",
            "rows": rows,
            "row_count": count if count is not None else len(rows),
            "reason": "",
        }
    except Exception as exc:
        return {
            "status": "source-error",
            "rows": [],
            "row_count": 0,
            "reason": str(exc),
        }


def _audit_source_table_entry(table, count_result, **extra):
    entry = {
        "table": table,
        "rows": count_result.get("row_count", 0),
        "usable_for_market_theme_evidence": False,
        "reason": AUDIT_SOURCE_TABLE_REASONS.get(
            table,
            "missing explicit market/theme evidence semantics",
        ),
    }
    if count_result.get("status") != "ok":
        entry["status"] = "source-error"
        entry["reason"] = "read failed; details redacted"
    entry.update({key: value for key, value in extra.items() if value not in (None, "")})
    return entry


def _audit_diagnostic_table_entry(table, count_result, **extra):
    entry = _audit_source_table_entry(table, count_result, **extra)
    entry["diagnostic_only"] = True
    entry["reason"] = AUDIT_DIAGNOSTIC_TABLE_REASONS.get(
        table,
        "diagnostic only; not an approved market/theme source",
    )
    return entry


def _candidate_preview_row(row, trade_date, source_name):
    if not isinstance(row, dict):
        return None
    candidate = {
        "trade_date": row.get("trade_date") or trade_date,
        "as_of": row.get("as_of") or row.get("created_at") or _default_as_of(trade_date),
        "market_index": row.get("market_index"),
        "sector_theme_key": row.get("sector_theme_key"),
        "watchlist_breadth": row.get("watchlist_breadth"),
        "freshness": row.get("freshness") or "fresh",
        "evidence_value": row.get("evidence_value"),
        "support_level": row.get("support_level"),
        "lineage": row.get("lineage"),
        "source_family": row.get("source_family") or "production_db",
        "source_name": row.get("source_name") or source_name,
        "evidence_status": row.get("evidence_status") or "confirmed",
    }
    if _validate_handoff_row({**candidate, "metadata": row.get("metadata") or {}}):
        return None
    return candidate


def _approved_payload_preview_from_confirmed_rows(trade_date, rows_by_table):
    candidates = []
    for row in rows_by_table.get(TABLE_NAME, []):
        candidate = _candidate_preview_row(row, trade_date, TABLE_NAME)
        if candidate:
            candidates.append(candidate)
    if not candidates:
        return None
    validation = validate_market_theme_evidence_ingestion_payload(candidates)
    if not validation.get("valid"):
        return None
    return [
        {field: row.get(field) for field in (
            "trade_date",
            "as_of",
            "market_index",
            "sector_theme_key",
            "watchlist_breadth",
            "freshness",
            "evidence_value",
            "support_level",
            "lineage",
            "source_family",
            "source_name",
            "evidence_status",
        )}
        for row in validation.get("rows", [])
    ]


def build_market_theme_evidence_production_source_audit(client, trade_date, limit=1000):
    """Build a read-only approved-payload gate from production DB source rows."""
    source_tables = []
    diagnostic_tables = []
    rows_by_table = {}

    confirmed_result = _select_count_rows(
        client,
        TABLE_NAME,
        SELECT_FIELDS,
        filters=[("eq", ("trade_date", trade_date))] if trade_date else [],
        limit=limit,
    )
    rows_by_table["market_theme_confirmed_evidence"] = confirmed_result["rows"]
    source_tables.append(
        _audit_source_table_entry("market_theme_confirmed_evidence", confirmed_result)
    )

    index_source_result = _select_count_rows(
        client,
        INDEX_SOURCE_TABLE,
        (
            "trade_date,as_of,index_scope,market_index,sector_theme_key,"
            "source_family,source_name,close,change_pct,metadata"
        ),
        filters=[("eq", ("trade_date", trade_date))] if trade_date else [],
        limit=limit,
    )
    rows_by_table[INDEX_SOURCE_TABLE] = index_source_result["rows"]
    source_tables.append(_audit_source_table_entry(INDEX_SOURCE_TABLE, index_source_result))

    member_source_result = _select_count_rows(
        client,
        MEMBER_SOURCE_TABLE,
        "sector_theme_key,stock_code,stock_name,market_index,is_active,valid_from,valid_to,source_family,source_name",
        filters=[("eq", ("is_active", True))],
        limit=limit,
    )
    rows_by_table[MEMBER_SOURCE_TABLE] = member_source_result["rows"]
    source_tables.append(_audit_source_table_entry(MEMBER_SOURCE_TABLE, member_source_result))

    snapshot_result = _select_count_rows(
        client,
        "daily_signal_snapshot",
        "*",
        filters=[("eq", ("trade_date", trade_date))] if trade_date else [],
        limit=limit,
    )
    rows_by_table["daily_signal_snapshot"] = snapshot_result["rows"]
    diagnostic_tables.append(_audit_diagnostic_table_entry("daily_signal_snapshot", snapshot_result))

    signal_runs_result = _select_count_rows(
        client,
        "signal_runs",
        "id,run_date,run_phase",
        filters=[
            ("eq", ("run_date", trade_date)),
            ("eq", ("run_phase", "daily_close")),
        ] if trade_date else [("eq", ("run_phase", "daily_close"))],
        limit=limit,
    )
    rows_by_table["signal_runs"] = signal_runs_result["rows"]
    diagnostic_tables.append(
        _audit_diagnostic_table_entry(
            "signal_runs",
            signal_runs_result,
            run_type="daily_close",
        )
    )

    run_ids = [
        row.get("id")
        for row in signal_runs_result.get("rows", [])
        if isinstance(row, dict) and row.get("id")
    ]
    signal_item_filters = [("in_", ("run_id", run_ids))] if run_ids else []
    signal_items_result = (
        _select_count_rows(
            client,
            "signal_items",
            "*",
            filters=signal_item_filters,
            limit=limit,
        )
        if run_ids
        else {"status": "ok", "rows": [], "row_count": 0, "reason": ""}
    )
    rows_by_table["signal_items"] = signal_items_result["rows"]
    diagnostic_tables.append(_audit_diagnostic_table_entry("signal_items", signal_items_result))

    preview = _approved_payload_preview_from_confirmed_rows(trade_date, rows_by_table)
    can_generate = bool(preview)
    if can_generate:
        for entry in source_tables:
            if entry["table"] == "market_theme_confirmed_evidence":
                entry["usable_for_market_theme_evidence"] = True
                entry["reason"] = "confirmed market/theme evidence contract columns validated"
    return {
        "mode": AUDIT_MODE,
        "write_execution": "disabled",
        "live_write": False,
        "source_family": "production_db",
        "trade_date": trade_date,
        "source_tables": source_tables,
        "diagnostic_tables": diagnostic_tables,
        "deprecated_tables": list(DEPRECATED_SOURCE_TABLES),
        "can_generate_approved_payload": can_generate,
        "status": "dry-run-preview" if can_generate else "blocked",
        "missing_source_semantics": [] if can_generate else AUDIT_MISSING_SOURCE_SEMANTICS,
        "approved_payload_preview": preview,
    }


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
        "target_table": TARGET_TABLE,
        "rows": rows,
        "sql": render_market_theme_evidence_handoff_sql(rows),
    }


def validate_market_theme_evidence_ingestion_payload(payloads, include_sql=False):
    handoff = build_market_theme_evidence_handoff(payloads)
    valid = handoff["status"] == "ready" and handoff["handoff_ready"]
    result = {
        "valid": valid,
        "status": handoff["status"],
        "reason": handoff["reason"],
        "may_render_manual_sql": valid,
        "live_write": False,
        "target_table": handoff["target_table"],
        "row_count": len(handoff["rows"]),
        "rows": handoff["rows"] if valid else [],
        "sql_rendered": bool(valid and include_sql and handoff["sql"]),
    }
    if valid and include_sql:
        result["manual_sql"] = handoff["sql"]
    return result


def build_market_theme_confirmed_evidence_write_plan(payload):
    rows, normalize_reason = normalize_market_theme_approved_payload(payload)
    validation = validate_market_theme_evidence_ingestion_payload(rows)
    if normalize_reason:
        validation = {
            "valid": False,
            "status": "insufficient-data",
            "reason": normalize_reason,
            "may_render_manual_sql": False,
            "live_write": False,
            "target_table": TARGET_TABLE,
            "row_count": 0,
            "rows": [],
            "sql_rendered": False,
        }

    passed = bool(validation["valid"])
    upsert_rows = [
        {column: row.get(column) for column in WRITE_COLUMNS}
        for row in validation.get("rows", [])
    ] if passed else []
    source_families = sorted(
        {
            str(row.get("source_family") or "").strip().lower()
            for row in upsert_rows
            if row.get("source_family")
        }
    )
    source_names = sorted(
        {
            str(row.get("source_name") or "").strip()
            for row in upsert_rows
            if row.get("source_name")
        }
    )
    if not source_families:
        source_families = sorted(
            {
                str(family or "").strip().lower()
                for family in _approval_payload_source_families(payload)
                if family
            }
        )
    if not source_names and isinstance(payload, dict):
        names = []
        if payload.get("source_name"):
            names.append(str(payload.get("source_name")).strip())
        for row in payload.get("rows", []) if isinstance(payload.get("rows"), list) else []:
            if isinstance(row, dict) and row.get("source_name"):
                names.append(str(row.get("source_name")).strip())
        source_names = sorted({name for name in names if name})
    source_type = (
        "production"
        if source_families == ["production_db"]
        else "approved_persistent_source"
        if source_families and all(family in HANDOFF_ALLOWED_SOURCE_FAMILIES for family in source_families)
        else "forbidden_or_unapproved_source"
        if source_families
        else "missing-source"
    )
    return {
        "target_table": TARGET_TABLE,
        "table": TABLE_NAME,
        "source": {
            "name": ",".join(source_names),
            "type": source_type,
            "families": source_families,
        },
        "upsert_conflict_target": UPSERT_CONFLICT_TARGET,
        "payload_validation": {
            "status": "passed" if passed else "failed",
            "reason": "" if passed else validation.get("reason", "payload validation failed"),
        },
        "rows_to_upsert": len(upsert_rows),
        "upsert_rows": upsert_rows,
    }


def _sanitize_write_credential_resolution(resolution):
    return {
        "status": resolution["status"],
        "required": resolution["required"],
        "missing": resolution["missing"],
        "url_source": resolution["url_source"],
        "key_source": resolution["key_source"],
    }


def validate_market_theme_write_env(env=None, config_module=_CONFIG_MODULE_UNSET):
    return _sanitize_write_credential_resolution(
        resolve_market_theme_write_credentials(env, config_module)
    )


def build_market_theme_write_client(env=None, config_module=_CONFIG_MODULE_UNSET):
    resolution = resolve_market_theme_write_credentials(env, config_module)
    if resolution["status"] != "passed":
        return None
    from supabase import create_client

    credentials = resolution["credentials"]
    return create_client(credentials["SUPABASE_URL"], credentials["SUPABASE_SERVICE_ROLE_KEY"])


def upsert_market_theme_confirmed_evidence(rows, client):
    if not rows:
        raise ValueError("rows are required")
    if client is None:
        raise ValueError("client is required")
    return (
        client.table(TABLE_NAME)
        .upsert(rows, on_conflict=UPSERT_CONFLICT_TARGET)
        .execute()
    )


def build_market_theme_evidence_readonly_smoke(load_result):
    result = load_result if isinstance(load_result, dict) else {}
    status = result.get("status") or "source-error"
    reason = str(result.get("reason") or "")
    rows = result.get("rows") if isinstance(result.get("rows"), list) else []
    source_families = sorted(
        {
            str(row.get("source_family") or "").strip().lower()
            for row in rows
            if isinstance(row, dict) and row.get("source_family")
        }
    )
    source_family = (
        ",".join(source_families)
        or str(result.get("source_family") or "production_db").strip().lower()
    )
    source_family_allowed = bool(rows) and all(
        isinstance(row, dict)
        and _source_family_allowed_for_confirmed_loader(row.get("source_family"))
        for row in rows
    )
    confirmed = bool(result.get("confirmed")) and source_family_allowed

    if status == "missing-source":
        env_status = "missing"
        table_read = "skipped"
        note = "production DB env/config missing"
    elif status == "source-error":
        env_status = "present"
        lowered = reason.lower()
        table_read = "permission-denied" if "permission denied" in lowered or "permission" in lowered else "error"
        note = "read-after-write smoke failed; details redacted"
    else:
        env_status = "present"
        table_read = "ok"
        if rows and not source_family_allowed:
            status = "insufficient-data"
            note = "source_family is not an approved persistent source"
        elif confirmed:
            note = "fresh production confirmed/supporting evidence available"
        elif not rows and status == "absent":
            note = "no production confirmed evidence available"
        elif any(str(row.get("freshness") or "").lower() != "fresh" for row in rows if isinstance(row, dict)):
            note = "production rows are stale or not fresh"
        elif any(
            str(row.get("support_level") or "").lower() not in CONFIRMED_SUPPORT_LEVELS
            for row in rows
            if isinstance(row, dict)
        ):
            note = "production rows do not contain confirmed/supporting support_level"
        else:
            note = reason or "production evidence is insufficient"

    strategy_consumer = "fail-closed"
    if confirmed:
        try:
            from core.market_theme_evidence import build_market_theme_evidence_provider

            consumer_input = result
            if not result.get("sources") and rows:
                consumer_input = _result_from_confirmed_row(rows[0])
            evidence = build_market_theme_evidence_provider(market_theme_evidence=consumer_input)
            if evidence.get("confirmed") and evidence.get("source_status") == "ready":
                strategy_consumer = "pass"
        except Exception:
            strategy_consumer = "fail-closed"

    smoke_status = "ok" if confirmed else status if rows and not source_family_allowed else "fail-closed"

    return {
        "title": "market_theme_confirmed_evidence smoke",
        "mode": "read-only",
        "write": "disabled",
        "schema_decision": "no-schema-change",
        "source": "production",
        "source_family": source_family,
        "target": TARGET_TABLE,
        "env": env_status,
        "table_read": table_read,
        "rows": len(rows),
        "confirmed_evidence_rows": len(rows) if confirmed else 0,
        "sample_fallback": "disabled",
        "runtime_fallback": "disabled",
        "strategy_consumer": strategy_consumer,
        "status": smoke_status,
        "telegram_confirmed": confirmed,
        "source_family_allowed": source_family_allowed,
        "note": note,
    }


def _provider_sources_from_row(row, requested_trade_date=None):
    theme_key = str(row.get("sector_theme_key") or "market_theme")
    support_level = str(row.get("support_level") or "").lower()
    evidence_value = row.get("evidence_value") or {}
    watchlist_breadth = row.get("watchlist_breadth") or {}
    lineage = row.get("lineage") or {}
    source_name = row.get("source_name") or "market_theme_confirmed_evidence"
    row_trade_date = str(row.get("trade_date") or "")
    requested = str(requested_trade_date or "")
    freshness_reason = (
        "previous_trade_date_allowed"
        if requested and row_trade_date and requested != row_trade_date
        else "same_trade_date"
    )
    base = {
        "source_family": "production_db",
        "source_name": source_name,
        "as_of": row.get("as_of"),
        "freshness": "fresh",
        "freshness_reason": freshness_reason,
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
        and _source_family_allowed_for_confirmed_loader(row.get("source_family"))
    )


def _date_gap_days(row_trade_date, requested_trade_date):
    if not row_trade_date or not requested_trade_date:
        return 0
    try:
        row_date = datetime.strptime(str(row_trade_date), "%Y-%m-%d").date()
        requested_date = datetime.strptime(str(requested_trade_date), "%Y-%m-%d").date()
    except ValueError:
        return None
    return (requested_date - row_date).days


def _row_allowed_for_requested_date(row, requested_trade_date=None):
    gap_days = _date_gap_days(row.get("trade_date"), requested_trade_date)
    if gap_days is None:
        return False
    return 0 <= gap_days <= MAX_PREVIOUS_TRADE_DATE_GAP_DAYS


def _trend_from_rows(rows, requested_trade_date=None):
    eligible_rows = [
        row for row in rows
        if (
            isinstance(row, dict)
            and not _missing_fields(row)
            and _confirmed_row(row)
            and _row_allowed_for_requested_date(
                row,
                requested_trade_date=requested_trade_date,
            )
        )
    ]
    by_date = {}
    for row in eligible_rows:
        trade_date = str(row.get("trade_date") or "")
        if not trade_date:
            continue
        bucket = by_date.setdefault(
            trade_date,
            {
                "trade_date": trade_date,
                "supporting_rows": 0,
                "themes": set(),
                "market_indexes": set(),
                "source_names": set(),
            },
        )
        bucket["supporting_rows"] += 1
        if row.get("sector_theme_key"):
            bucket["themes"].add(str(row.get("sector_theme_key")))
        if row.get("market_index"):
            bucket["market_indexes"].add(str(row.get("market_index")))
        if row.get("source_name"):
            bucket["source_names"].add(str(row.get("source_name")))

    days = [
        {
            **bucket,
            "themes": sorted(bucket["themes"]),
            "market_indexes": sorted(bucket["market_indexes"]),
            "source_names": sorted(bucket["source_names"]),
        }
        for _date, bucket in sorted(by_date.items(), reverse=True)
    ]
    observed_days = len(days)
    supporting_days = sum(1 for day in days if day["supporting_rows"] > 0)
    recent_days = days[:3]
    recent_supporting_days = sum(1 for day in recent_days if day["supporting_rows"] > 0)
    support_streak_days = 0
    for day in days:
        if day["supporting_rows"] <= 0:
            break
        support_streak_days += 1

    if observed_days >= 3 and recent_supporting_days >= 3:
        status = "confirmed_trend"
    elif observed_days >= 2 and recent_supporting_days >= 2:
        status = "supporting_trend"
    elif observed_days >= 1:
        status = "single_day"
    else:
        status = "insufficient-history"

    return {
        "status": status,
        "lookback_rows": len(rows),
        "observed_days": observed_days,
        "supporting_days": supporting_days,
        "recent_supporting_days": recent_supporting_days,
        "support_streak_days": support_streak_days,
        "days": days,
        "allowed_effects": ["wording", "排序提示", "detail trace"],
        "forbidden_effects": ["不得放寬買點", "不得覆蓋風控", "不得單獨變 BUY"],
    }


def _result_from_confirmed_row(row, requested_trade_date=None, trend_rows=None):
    sources = _provider_sources_from_row(row, requested_trade_date=requested_trade_date)
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
        "requested_trade_date": requested_trade_date,
        "as_of": row.get("as_of"),
        "sources": sources,
        "rows": [row],
        "evidence_trend": _trend_from_rows(
            trend_rows or [row],
            requested_trade_date=requested_trade_date,
        ),
    }


def _validate_rows(rows, requested_trade_date=None, trend_rows=None):
    for row in rows:
        if not isinstance(row, dict):
            return _empty_result("source-error", "row is not an object")
        support_level = str(row.get("support_level") or "").lower()
        if support_level not in ALLOWED_SUPPORT_LEVELS:
            return _empty_result("source-error", "unexpected support_level")
        if not _source_family_allowed_for_confirmed_loader(row.get("source_family")):
            return _empty_result(
                "insufficient-data",
                "source_family is not an approved persistent source",
                rows=rows,
            )

    confirmed_rows = [
        row for row in rows
        if (
            not _missing_fields(row)
            and _confirmed_row(row)
            and _row_allowed_for_requested_date(
                row,
                requested_trade_date=requested_trade_date,
            )
        )
    ]
    if confirmed_rows:
        return _result_from_confirmed_row(
            confirmed_rows[0],
            requested_trade_date=requested_trade_date,
            trend_rows=trend_rows or rows,
        )

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
        if trade_date and not rows:
            rows = (
                client.table(TABLE_NAME)
                .select(SELECT_FIELDS)
                .lte("trade_date", trade_date)
                .order("trade_date", desc=True)
                .order("as_of", desc=True)
                .limit(limit)
                .execute()
                .data
                or []
            )
        trend_rows = rows
        if trade_date:
            trend_rows = (
                client.table(TABLE_NAME)
                .select(SELECT_FIELDS)
                .lte("trade_date", trade_date)
                .order("trade_date", desc=True)
                .order("as_of", desc=True)
                .limit(max(limit, EVIDENCE_TREND_LOOKBACK_ROWS))
                .execute()
                .data
                or []
            )
    except Exception as exc:
        return _empty_result("source-error", str(exc))

    if not rows:
        return _empty_result("absent", "production table returned no rows")
    return _validate_rows(
        rows,
        requested_trade_date=trade_date,
        trend_rows=trend_rows,
    )
