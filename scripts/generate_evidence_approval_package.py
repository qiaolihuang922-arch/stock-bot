#!/usr/bin/env python3
"""Generate a non-live market/theme evidence approval package.

This script creates review artifacts only. It does not connect to Supabase,
execute SQL, run backfills, mutate RLS/grants, or send Telegram.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.market_theme_evidence_store import (
    HANDOFF_ALLOWED_SOURCE_FAMILIES,
    _source_family_forbidden,
    validate_market_theme_evidence_ingestion_payload,
)


FORBIDDEN_SECRET_MARKERS = (
    "service_role",
    "password",
    "apikey",
    "api_key",
    "supabase.co",
    "postgres://",
    "postgresql://",
)


def _load_payload(path):
    raw = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    return json.loads(raw)


def _safe_text(value):
    return "" if value is None else str(value)


def _default_as_of(trade_date):
    return f"{trade_date}T00:00:00+08:00" if trade_date else ""


def _row_source_families(payload):
    families = []
    top_family = payload.get("source_family") if isinstance(payload, dict) else None
    if top_family:
        families.append(top_family)
    for row in payload.get("rows", []) if isinstance(payload, dict) else []:
        if isinstance(row, dict) and row.get("source_family"):
            families.append(row.get("source_family"))
    return families


def _source_guard_reason(payload):
    families = _row_source_families(payload)
    if not families:
        return "missing source_family"
    for family in families:
        normalized = _safe_text(family).strip().lower()
        if _source_family_forbidden(normalized):
            return "forbidden source_family"
        if normalized not in HANDOFF_ALLOWED_SOURCE_FAMILIES:
            return "source_family is not an approved persistent source"
    return None


def _normalize_approval_payload(payload):
    if not isinstance(payload, dict):
        return [], "payload must be an object"
    guard_reason = _source_guard_reason(payload)
    if guard_reason:
        return [], guard_reason

    trade_date = payload.get("trade_date")
    source_family = _safe_text(payload.get("source_family")).strip().lower()
    source_name = payload.get("source_name") or "owner_approved_market_theme_review"
    freshness = _safe_text(payload.get("freshness")).strip().lower()
    evidence_status = _safe_text(payload.get("evidence_status")).strip().lower()
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        return [], "rows must be a non-empty array"

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
                    "write_execution": "disabled",
                },
                "notes": row.get("notes") or reason or "Owner-approved persistent evidence package row",
            }
        )
    return normalized, None


def _contains_secret_marker(text):
    lowered = text.lower()
    return any(marker in lowered for marker in FORBIDDEN_SECRET_MARKERS)


def _sql_file_name(trade_date):
    safe_date = _safe_text(trade_date).replace("/", "-") or "undated"
    return f"market_theme_confirmed_evidence_{safe_date}.sql"


def _markdown_package(package):
    validation = package["payload_validation"]
    lines = [
        "# Market Theme Evidence Approval Package",
        "",
        f"- schema_decision: {package['schema_decision']}",
        f"- mode: {package['mode']}",
        f"- write_execution: {package['write_execution']}",
        f"- payload_validation: {validation['status']}",
        f"- deterministic_sql_path: {package.get('deterministic_sql_path') or 'not-generated'}",
        "",
        "## Risk Summary",
    ]
    for item in package["risk_summary"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Preflight Checklist"])
    for item in package["preflight_checklist"]:
        lines.append(f"- [ ] {item}")
    lines.extend(["", "## Post-run Verification Checklist"])
    for item in package["post_run_verification_checklist"]:
        lines.append(f"- [ ] {item}")
    lines.extend(["", "## Manual Approval Required"])
    for item in package["manual_approval_required"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Not Executed"])
    for item in package["not_executed"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Read-only Smoke Command", "", f"`{package['read_only_smoke_command']}`", ""])
    return "\n".join(lines)


def build_approval_package(payload):
    rows, normalize_reason = _normalize_approval_payload(payload)
    validation = validate_market_theme_evidence_ingestion_payload(rows, include_sql=True)
    if normalize_reason:
        validation = {
            "valid": False,
            "status": "insufficient-data",
            "reason": normalize_reason,
            "may_render_manual_sql": False,
            "live_write": False,
            "target_table": "public.market_theme_confirmed_evidence",
            "row_count": 0,
            "rows": [],
            "sql_rendered": False,
        }

    passed = bool(validation["valid"])
    sql = validation.get("manual_sql") if passed else None
    if sql:
        sql = "\n".join(
            [
                "-- Owner manual approval required.",
                "-- Agent did not execute this SQL.",
                "-- This package is not evidence of production deployment.",
                sql,
            ]
        )
        if _contains_secret_marker(sql):
            passed = False
            validation = {
                **validation,
                "valid": False,
                "status": "insufficient-data",
                "reason": "SQL contains forbidden secret-like marker",
                "may_render_manual_sql": False,
                "sql_rendered": False,
            }
            sql = None

    trade_date = payload.get("trade_date") if isinstance(payload, dict) else None
    source_family = payload.get("source_family") if isinstance(payload, dict) else None
    package = {
        "schema_decision": "no-schema-change",
        "mode": "non-live-approval-package",
        "write_execution": "disabled",
        "payload_validation": {
            "status": "passed" if passed else "failed",
            "reason": "" if passed else validation.get("reason", "payload validation failed"),
            "details": validation,
        },
        "deterministic_sql": sql,
        "deterministic_sql_path": _sql_file_name(trade_date) if sql else None,
        "risk_summary": [
            f"source_family={source_family or 'missing'}",
            f"freshness={payload.get('freshness') if isinstance(payload, dict) else 'missing'}",
            f"trade_date={trade_date or 'missing'}",
            f"row_count={validation.get('row_count', 0)}",
            "manual-only warning: package generation does not write production DB",
        ],
        "preflight_checklist": [
            "Owner confirms payload source is persistent and approved",
            "Owner reviews deterministic SQL before any production execution",
            "Owner confirms no service-role key, password, project URL, or connection string is embedded",
            "Owner separately approves any SQL execution outside this script",
        ],
        "post_run_verification_checklist": [
            "Run read-only smoke after any manually approved SQL execution",
            "Confirm smoke status is ok only when production rows are fresh confirmed/supporting",
            "Confirm Telegram remains fail-closed until production DB read-only result is available",
        ],
        "read_only_smoke_command": (
            "python scripts/smoke_market_theme_evidence_readonly.py"
            + (f" --trade-date {trade_date}" if trade_date else "")
        ),
        "manual_approval_required": [
            "Owner reviews package",
            "Owner approves SQL execution separately",
            "Owner runs read-only verification after manual execution",
        ],
        "not_executed": [
            "live Supabase write",
            "formal backfill",
            "production RLS/grant/policy/role changes",
            "Telegram delivery",
        ],
    }
    return package


def write_approval_package(package, output_dir):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    package_path = output / "approval_package.json"
    markdown_path = output / "approval_package.md"
    package_path.write_text(
        json.dumps(package, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_markdown_package(package), encoding="utf-8")
    sql_path = None
    if package.get("deterministic_sql"):
        sql_path = output / package["deterministic_sql_path"]
        sql_path.write_text(package["deterministic_sql"] + "\n", encoding="utf-8")
    return {
        "package_json": str(package_path),
        "package_markdown": str(markdown_path),
        "deterministic_sql": str(sql_path) if sql_path else None,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate a non-live market/theme evidence approval package."
    )
    parser.add_argument("--payload", required=True, help="Owner-approved payload JSON file, or '-' for stdin.")
    parser.add_argument("--output-dir", help="Directory for package JSON/Markdown/SQL artifacts.")
    args = parser.parse_args(argv)

    package = build_approval_package(_load_payload(args.payload))
    if args.output_dir:
        package["output_paths"] = write_approval_package(package, args.output_dir)
    print(json.dumps(package, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if package["payload_validation"]["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
