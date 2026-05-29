#!/usr/bin/env python3
"""Dry-run validation for market/theme evidence ingestion payloads.

Non-live artifact only:
- does not write Supabase
- does not run production backfill
- does not change production RLS/grants
- does not send Telegram
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.market_theme_evidence_store import (
    validate_market_theme_evidence_ingestion_payload,
)


def _load_payload(path):
    raw = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    if isinstance(data, dict) and isinstance(data.get("payloads"), list):
        return data["payloads"]
    if isinstance(data, dict) and isinstance(data.get("rows"), list):
        return data["rows"]
    if isinstance(data, list):
        return data
    return [data]


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate public.market_theme_confirmed_evidence ingestion payloads without writing DB."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="JSON payload file, or '-' for stdin. Accepts an object, an array, or {'payloads': [...]} / {'rows': [...]}.",
    )
    parser.add_argument(
        "--include-sql",
        action="store_true",
        help="Include manual SQL only when validation passes. Invalid payloads never render SQL.",
    )
    args = parser.parse_args(argv)

    result = validate_market_theme_evidence_ingestion_payload(
        _load_payload(args.input),
        include_sql=args.include_sql,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
