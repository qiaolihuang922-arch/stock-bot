#!/usr/bin/env python3
"""Validate or explicitly write approved market/theme confirmed evidence rows."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.market_theme_evidence_store import (
    build_market_theme_confirmed_evidence_write_plan,
    build_market_theme_write_client,
    upsert_market_theme_confirmed_evidence,
    validate_market_theme_write_env,
)


def _validate_write_env(env, config_module):
    if config_module is None:
        return validate_market_theme_write_env(env)
    return validate_market_theme_write_env(env, config_module)


def _build_write_client(env, config_module):
    if config_module is None:
        return build_market_theme_write_client(env)
    return build_market_theme_write_client(env, config_module)


def _load_payload(path):
    raw = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    return json.loads(raw)


def _sanitized_preview(rows):
    preview = []
    for row in rows:
        preview.append(
            {
                "trade_date": row.get("trade_date"),
                "as_of": row.get("as_of"),
                "market_index": row.get("market_index"),
                "sector_theme_key": row.get("sector_theme_key"),
                "source_family": row.get("source_family"),
                "source_name": row.get("source_name"),
                "freshness": row.get("freshness"),
                "evidence_status": row.get("evidence_status"),
                "support_level": row.get("support_level"),
            }
        )
    return preview


def _dry_run_output(plan):
    return {
        "mode": "dry-run",
        "target_table": plan["target_table"],
        "write_execution": "disabled",
        "payload_validation": plan["payload_validation"],
        "upsert_conflict_target": plan["upsert_conflict_target"],
        "rows_to_upsert": plan["rows_to_upsert"],
        "upsert_preview": _sanitized_preview(plan["upsert_rows"]),
        "execute_payload": None,
    }


def _blocked_execute_output(plan, env_validation):
    return {
        "mode": "execute",
        "target_table": plan["target_table"],
        "write_execution": "blocked",
        "payload_validation": plan["payload_validation"],
        "env_validation": env_validation,
        "upsert_conflict_target": plan["upsert_conflict_target"],
        "rows_to_upsert": plan["rows_to_upsert"],
        "rows_written": 0,
    }


def _executed_output(plan, env_validation):
    return {
        "mode": "execute",
        "target_table": plan["target_table"],
        "write_execution": "executed",
        "payload_validation": plan["payload_validation"],
        "env_validation": env_validation,
        "upsert_conflict_target": plan["upsert_conflict_target"],
        "rows_to_upsert": plan["rows_to_upsert"],
        "rows_written": plan["rows_to_upsert"],
        "upsert_preview": _sanitized_preview(plan["upsert_rows"]),
    }


def main(argv=None, client=None, env=None, config_module=None):
    parser = argparse.ArgumentParser(
        description=(
            "Dry-run or explicitly execute public.market_theme_confirmed_evidence "
            "upserts from an approved payload."
        )
    )
    parser.add_argument("--payload", required=True, help="Approved payload JSON file, or '-' for stdin.")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Explicitly write via Supabase after validation and write env checks pass.",
    )
    args = parser.parse_args(argv)

    plan = build_market_theme_confirmed_evidence_write_plan(_load_payload(args.payload))
    if not args.execute:
        output = _dry_run_output(plan)
        print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if plan["payload_validation"]["status"] == "passed" else 2

    if plan["payload_validation"]["status"] != "passed":
        output = _blocked_execute_output(
            plan,
            {"status": "skipped", "required": ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"], "missing": []},
        )
        print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    env_validation = _validate_write_env(env, config_module)
    if env_validation["status"] != "passed":
        output = _blocked_execute_output(plan, env_validation)
        print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    write_client = client or _build_write_client(env, config_module)
    upsert_market_theme_confirmed_evidence(plan["upsert_rows"], write_client)
    output = _executed_output(plan, env_validation)
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
