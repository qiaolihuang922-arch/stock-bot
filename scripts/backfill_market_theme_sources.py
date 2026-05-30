#!/usr/bin/env python3
"""Backfill market/theme source rows from persistent production DB data.

This script intentionally derives evidence only from production DB tables and
repo-owned theme membership rules. It does not use runtime chat state, local
cache, synthetic fixtures, or Telegram text.
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.watchlist import STOCKS
from services.market_theme_evidence_store import upsert_market_theme_confirmed_evidence


RULE_VERSION = "market_theme_source_v1"
MARKET_INDEX = "WATCHLIST_TW"
SOURCE_NAME = "daily_price_equal_weight_theme_backfill"

THEME_MEMBERS = {
    "ai_server": ["3231", "2356", "2376", "2301"],
    "memory": ["2344", "2408", "2337"],
    "semiconductor": ["2303", "3035"],
    "pc_display": ["2324", "3481"],
    "cooling_components": ["2421"],
}

THEME_NAMES = {
    "ai_server": "AI Server / Electronics Supply Chain",
    "memory": "Memory",
    "semiconductor": "Semiconductor",
    "pc_display": "PC / Display",
    "cooling_components": "Cooling Components",
}

CODE_TO_NAME = {code: name for name, code in STOCKS.items()}


def _num(value):
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _avg(values):
    values = [value for value in values if value is not None]
    if not values:
        return None
    return round(sum(values) / len(values), 4)


def _sum(values):
    values = [value for value in values if value is not None]
    if not values:
        return None
    return round(sum(values), 4)


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def get_supabase_client():
    from supabase import create_client

    try:
        import config
    except Exception:
        config = None

    url = os.environ.get("SUPABASE_URL") or getattr(config, "SUPABASE_URL", "")
    key = (
        os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        or getattr(config, "SUPABASE_SERVICE_ROLE_KEY", "")
        or getattr(config, "SERVICE_ROLE_KEY", "")
        or os.environ.get("SUPABASE_KEY")
        or getattr(config, "SUPABASE_KEY", "")
    )
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY|SUPABASE_KEY are required")
    return create_client(url, key)


def theme_member_rows(as_of=None):
    as_of = as_of or _now_iso()
    rows = []
    for theme_key, stock_codes in THEME_MEMBERS.items():
        for stock_code in stock_codes:
            rows.append(
                {
                    "sector_theme_key": theme_key,
                    "stock_code": stock_code,
                    "stock_name": CODE_TO_NAME.get(stock_code),
                    "market_index": MARKET_INDEX,
                    "weight": 1,
                    "is_active": True,
                    "valid_from": "2026-01-01",
                    "valid_to": None,
                    "source_family": "owner_approved_persistent",
                    "source_name": "repo_theme_members_v1",
                    "metadata": {
                        "rule_version": RULE_VERSION,
                        "as_of": as_of,
                        "source": "core.watchlist + repo theme membership map",
                    },
                }
            )
    return rows


def _price_key(row):
    return str(row.get("stock_id")), str(row.get("trade_date"))


def group_price_rows(price_rows):
    by_stock = defaultdict(list)
    for row in price_rows:
        stock_id = str(row.get("stock_id") or "")
        if not stock_id:
            continue
        by_stock[stock_id].append(row)
    for rows in by_stock.values():
        rows.sort(key=lambda item: str(item.get("trade_date") or ""))
    return by_stock


def _latest_and_previous(by_stock, trade_date):
    current = {}
    previous = {}
    for stock_id, rows in by_stock.items():
        before = [row for row in rows if str(row.get("trade_date") or "") < trade_date]
        today = [row for row in rows if str(row.get("trade_date") or "") == trade_date]
        if today:
            current[stock_id] = today[-1]
        if before:
            previous[stock_id] = before[-1]
    return current, previous


def _member_return(stock_id, current, previous):
    current_close = _num((current.get(stock_id) or {}).get("close"))
    previous_close = _num((previous.get(stock_id) or {}).get("close"))
    if current_close is None or previous_close in (None, 0):
        return None
    return (current_close / previous_close - 1) * 100


def _build_index_row(trade_date, as_of, index_scope, theme_key, stock_codes, current, previous):
    member_rows = [current[code] for code in stock_codes if code in current]
    returns = [_member_return(code, current, previous) for code in stock_codes]
    returns = [value for value in returns if value is not None]
    if not member_rows:
        return None
    return {
        "trade_date": trade_date,
        "as_of": as_of,
        "index_scope": index_scope,
        "market_index": MARKET_INDEX,
        "sector_theme_key": theme_key,
        "index_name": THEME_NAMES.get(theme_key) if theme_key else "Watchlist Taiwan",
        "source_family": "production_db",
        "source_name": SOURCE_NAME,
        "index_method": "owner_defined_basket",
        "open": _avg([_num(row.get("open")) for row in member_rows]),
        "high": _avg([_num(row.get("high")) for row in member_rows]),
        "low": _avg([_num(row.get("low")) for row in member_rows]),
        "close": _avg([_num(row.get("close")) for row in member_rows]),
        "change_pct": _avg(returns),
        "volume": _sum([_num(row.get("volume")) for row in member_rows]),
        "turnover": None,
        "member_count": len(member_rows),
        "metadata": {
            "rule_version": RULE_VERSION,
            "member_codes": stock_codes,
            "members_with_price": len(member_rows),
            "members_with_return": len(returns),
            "source_tables": ["daily_price", "sector_theme_members"],
        },
    }


def _support_level(theme_return, market_return, breadth):
    if theme_return is None or breadth["denominator"] <= 0:
        return "weak"
    if theme_return >= 3 and breadth["up_ratio"] >= 0.6:
        return "confirmed"
    if market_return is not None and theme_return >= market_return + 1 and breadth["up_ratio"] >= 0.5:
        return "supporting"
    if theme_return > 0 and breadth["up_ratio"] >= 0.5:
        return "supporting"
    if theme_return <= -3 or breadth["up_ratio"] < 0.35:
        return "invalidated"
    return "weak"


def _breadth(stock_codes, current, previous):
    returns = {
        code: _member_return(code, current, previous)
        for code in stock_codes
        if code in current
    }
    usable = {code: value for code, value in returns.items() if value is not None}
    denominator = len(usable)
    up_count = sum(1 for value in usable.values() if value > 0)
    strong_count = sum(1 for value in usable.values() if value >= 3)
    down_count = sum(1 for value in usable.values() if value < 0)
    return {
        "denominator": denominator,
        "up_count": up_count,
        "down_count": down_count,
        "strong_count": strong_count,
        "up_ratio": round(up_count / denominator, 4) if denominator else 0,
        "member_returns": {code: round(value, 4) for code, value in usable.items()},
    }


def build_source_payloads(price_rows, trade_date, as_of=None):
    as_of = as_of or _now_iso()
    by_stock = group_price_rows(price_rows)
    current, previous = _latest_and_previous(by_stock, trade_date)
    all_codes = sorted({code for codes in THEME_MEMBERS.values() for code in codes})
    market_row = _build_index_row(
        trade_date,
        as_of,
        "market",
        None,
        all_codes,
        current,
        previous,
    )
    if market_row is None:
        return {
            "status": "blocked",
            "reason": "no current daily_price rows for watchlist",
            "member_rows": theme_member_rows(as_of),
            "index_rows": [],
            "confirmed_rows": [],
        }

    # Only persist sector_theme rows for now. Broad market is used as the
    # same-run benchmark but not upserted because nullable sector_theme_key
    # broad-market rows need a separate DB conflict contract.
    index_rows = []
    confirmed_rows = []
    market_return = market_row.get("change_pct")
    for theme_key, stock_codes in THEME_MEMBERS.items():
        theme_row = _build_index_row(
            trade_date,
            as_of,
            "sector_theme",
            theme_key,
            stock_codes,
            current,
            previous,
        )
        if theme_row is None:
            continue
        index_rows.append(theme_row)
        breadth = _breadth(stock_codes, current, previous)
        support_level = _support_level(theme_row.get("change_pct"), market_return, breadth)
        freshness = "fresh" if breadth["denominator"] else "insufficient-data"
        confirmed_rows.append(
            {
                "trade_date": trade_date,
                "as_of": as_of,
                "market_index": MARKET_INDEX,
                "sector_theme_key": theme_key,
                "source_family": "production_db",
                "source_name": SOURCE_NAME,
                "freshness": freshness,
                "evidence_value": {
                    "theme_change_pct": theme_row.get("change_pct"),
                    "market_change_pct": market_return,
                    "relative_change_pct": (
                        round(theme_row.get("change_pct") - market_return, 4)
                        if theme_row.get("change_pct") is not None and market_return is not None
                        else None
                    ),
                    "index_method": "owner_defined_basket",
                    "theme_name": THEME_NAMES.get(theme_key),
                    "rule_version": RULE_VERSION,
                },
                "watchlist_breadth": breadth,
                "support_level": support_level,
                "evidence_status": "confirmed",
                "lineage": {
                    "rule_version": RULE_VERSION,
                    "source_tables": [
                        "daily_price",
                        "sector_theme_members",
                        "market_theme_index_daily_bars",
                    ],
                    "market_index_source_name": SOURCE_NAME,
                    "stock_codes": stock_codes,
                },
                "metadata": {
                    "generated_by": "scripts/backfill_market_theme_sources.py",
                    "source_quality": "production_db_derived",
                    "external_market_index": False,
                },
                "notes": "Derived from persistent daily_price rows and repo-approved theme membership.",
            }
        )
    return {
        "status": "ready",
        "reason": "ready",
        "member_rows": theme_member_rows(as_of),
        "index_rows": index_rows,
        "confirmed_rows": confirmed_rows,
    }


def fetch_price_rows(client, trade_date, lookback_limit=3600):
    return (
        client.table("daily_price")
        .select("stock_id,trade_date,open,high,low,close,volume,source")
        .lte("trade_date", trade_date)
        .order("trade_date", desc=True)
        .limit(lookback_limit)
        .execute()
        .data
        or []
    )


def latest_trade_date(client):
    rows = (
        client.table("daily_price")
        .select("trade_date")
        .order("trade_date", desc=True)
        .limit(1)
        .execute()
        .data
        or []
    )
    return str(rows[0].get("trade_date")) if rows else ""


def upsert_source_payloads(client, payloads):
    if payloads["member_rows"]:
        client.table("sector_theme_members").upsert(
            payloads["member_rows"],
            on_conflict="sector_theme_key,stock_code,valid_from,source_family,source_name",
        ).execute()
    if payloads["index_rows"]:
        trade_dates = sorted({row["trade_date"] for row in payloads["index_rows"]})
        for trade_date in trade_dates:
            (
                client.table("market_theme_index_daily_bars")
                .delete()
                .eq("trade_date", trade_date)
                .eq("source_family", "production_db")
                .eq("source_name", SOURCE_NAME)
                .execute()
            )
        client.table("market_theme_index_daily_bars").insert(payloads["index_rows"]).execute()
    if payloads["confirmed_rows"]:
        upsert_market_theme_confirmed_evidence(payloads["confirmed_rows"], client)


def print_summary(trade_date, payloads):
    print("MARKET THEME SOURCE BACKFILL")
    print(f"trade_date: {trade_date}")
    print(f"status: {payloads['status']}")
    print(f"reason: {payloads['reason']}")
    print(f"sector_theme_members rows: {len(payloads['member_rows'])}")
    print(f"market_theme_index_daily_bars rows: {len(payloads['index_rows'])}")
    print(f"market_theme_confirmed_evidence rows: {len(payloads['confirmed_rows'])}")
    compact = [
        {
            "theme": row["sector_theme_key"],
            "support_level": row["support_level"],
            "freshness": row["freshness"],
            "theme_change_pct": row["evidence_value"]["theme_change_pct"],
            "breadth": row["watchlist_breadth"]["up_ratio"],
        }
        for row in payloads["confirmed_rows"]
    ]
    print(json.dumps(compact, ensure_ascii=False, indent=2, sort_keys=True))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Backfill unified market/theme source tables and confirmed evidence from production DB daily_price."
    )
    parser.add_argument("--trade-date", help="YYYY-MM-DD. Defaults to latest daily_price trade_date.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--confirm-write", action="store_true")
    args = parser.parse_args(argv)

    if args.write and not args.confirm_write:
        raise SystemExit("Refusing to write without --confirm-write")
    if not args.write and not args.dry_run:
        raise SystemExit("Use --dry-run for preview, or --write --confirm-write for DB upsert")

    client = get_supabase_client()
    trade_date = args.trade_date or latest_trade_date(client)
    if not trade_date:
        raise SystemExit("No trade_date supplied and daily_price has no rows")

    price_rows = fetch_price_rows(client, trade_date)
    payloads = build_source_payloads(price_rows, trade_date)
    print_summary(trade_date, payloads)

    if payloads["status"] != "ready":
        raise SystemExit(1)
    if args.write:
        upsert_source_payloads(client, payloads)
        print("WRITE OK")
    else:
        print("DRY RUN ONLY: no database writes")


if __name__ == "__main__":
    main()
