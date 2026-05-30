#!/usr/bin/env python3
"""Read-only smoke for public.market_theme_confirmed_evidence.

Non-live artifact only:
- reads through the existing read-only loader
- does not write Supabase
- does not run production backfill
- does not change production RLS/grants
- does not send Telegram
"""

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.market_theme_evidence_store import (
    build_market_theme_evidence_production_source_audit,
    build_market_theme_evidence_readonly_smoke,
    load_confirmed_market_theme_evidence,
)

_CONFIG_MODULE_UNSET = object()


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


def resolve_readonly_smoke_credentials(env=None, config_module=_CONFIG_MODULE_UNSET):
    source = env if env is not None else os.environ
    config_source = _load_config_module() if config_module is _CONFIG_MODULE_UNSET else config_module

    url = source.get("SUPABASE_URL") or _config_module_value(config_source, "SUPABASE_URL")
    key = (
        source.get("SUPABASE_READONLY_KEY")
        or source.get("SUPABASE_KEY")
        or _config_module_value(config_source, "SUPABASE_READONLY_KEY")
        or _config_module_value(config_source, "SUPABASE_KEY")
    )

    missing = []
    if not url or not key:
        if not url:
            missing.append("SUPABASE_URL")
        if not key:
            missing.append("SUPABASE_READONLY_KEY|SUPABASE_KEY")
        return {
            "status": "failed",
            "missing": missing,
            "credentials": {},
        }

    return {
        "status": "passed",
        "missing": [],
        "credentials": {
            "SUPABASE_URL": url,
            "SUPABASE_READONLY_KEY": key,
        },
    }


def _build_readonly_client(env=None, config_module=_CONFIG_MODULE_UNSET, client_factory=None):
    resolution = resolve_readonly_smoke_credentials(env, config_module)
    if resolution["status"] != "passed":
        return None

    if client_factory is None:
        from supabase import create_client

        client_factory = create_client

    credentials = resolution["credentials"]
    return client_factory(credentials["SUPABASE_URL"], credentials["SUPABASE_READONLY_KEY"])


def _render(smoke):
    return "\n".join(
        [
            smoke["title"],
            f"mode: {smoke['mode']}",
            f"write: {smoke['write']}",
            f"schema_decision: {smoke['schema_decision']}",
            f"source: {smoke['source']}",
            f"source_family: {smoke['source_family']}",
            f"target: {smoke['target']}",
            f"env: {smoke['env']}",
            f"table_read: {smoke['table_read']}",
            f"rows: {smoke['rows']}",
            f"confirmed_evidence_rows: {smoke['confirmed_evidence_rows']}",
            f"sample_fallback: {smoke['sample_fallback']}",
            f"runtime_fallback: {smoke['runtime_fallback']}",
            f"strategy_consumer: {smoke['strategy_consumer']}",
            f"source_family_allowed: {str(smoke['source_family_allowed']).lower()}",
            f"status: {smoke['status']}",
            f"telegram_confirmed: {str(smoke['telegram_confirmed']).lower()}",
            f"note: {smoke['note']}",
        ]
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run a read-only market/theme evidence smoke without DB writes or Telegram delivery."
    )
    parser.add_argument("--trade-date", help="Optional YYYY-MM-DD trade_date filter.")
    parser.add_argument("--limit", type=int, default=20, help="Read limit for the smoke query.")
    parser.add_argument(
        "--production-source-audit-json",
        action="store_true",
        help="Output read-only production source audit JSON for approved payload gating.",
    )
    args = parser.parse_args(argv)

    client = _build_readonly_client()
    if client is None:
        if args.production_source_audit_json:
            audit = {
                "mode": "read-only-production-audit",
                "write_execution": "disabled",
                "live_write": False,
                "source_family": "production_db",
                "trade_date": args.trade_date,
                "source_tables": [],
                "can_generate_approved_payload": False,
                "status": "blocked",
                "missing_source_semantics": [
                    "production DB read credentials",
                    "market_index",
                    "sector_theme_key",
                    "watchlist_breadth definition",
                    "evidence_value meaning",
                    "support_level rule",
                    "lineage from production DB columns",
                ],
                "approved_payload_preview": None,
            }
            print(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True))
            return 2
        load_result = {
            "status": "missing-source",
            "confirmed": False,
            "reason": "missing required Supabase read credentials",
            "rows": [],
        }
    else:
        if args.production_source_audit_json:
            audit = build_market_theme_evidence_production_source_audit(
                client=client,
                trade_date=args.trade_date,
                limit=args.limit,
            )
            print(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True))
            return 0 if audit["can_generate_approved_payload"] else 2
        load_result = load_confirmed_market_theme_evidence(
            client=client,
            trade_date=args.trade_date,
            limit=args.limit,
        )
    smoke = build_market_theme_evidence_readonly_smoke(load_result)
    print(_render(smoke))
    return 0 if smoke["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
