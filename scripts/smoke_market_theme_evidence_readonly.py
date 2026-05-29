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
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.market_theme_evidence_store import (
    build_market_theme_evidence_readonly_smoke,
    load_confirmed_market_theme_evidence,
)


def _build_readonly_client():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_READONLY_KEY")
    if not url or not key:
        return None

    from supabase import create_client

    return create_client(url, key)


def _render(smoke):
    return "\n".join(
        [
            smoke["title"],
            f"mode: {smoke['mode']}",
            f"write: {smoke['write']}",
            f"env: {smoke['env']}",
            f"table_read: {smoke['table_read']}",
            f"rows: {smoke['rows']}",
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
    args = parser.parse_args(argv)

    client = _build_readonly_client()
    if client is None:
        load_result = {
            "status": "missing-source",
            "confirmed": False,
            "reason": "SUPABASE_URL or SUPABASE_READONLY_KEY missing",
            "rows": [],
        }
    else:
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
