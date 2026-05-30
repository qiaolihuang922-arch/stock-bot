#!/usr/bin/env python3
"""Backfill market/theme evidence from official TWSE OpenAPI sources."""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import requests

from core.watchlist import STOCKS
from services.market_theme_evidence_store import upsert_market_theme_confirmed_evidence


RULE_VERSION = "twse_official_market_theme_v1"
MARKET_INDEX = "TAIEX"
SOURCE_FAMILY = "market_data"
SOURCE_NAME = "twse_openapi_mi_index"
MEMBER_SOURCE_NAME = "twse_openapi_t187ap03_L"
BREADTH_SOURCE_NAME = "twse_openapi_twtazu_od"
HEADERS = {"User-Agent": "Mozilla/5.0"}

TWSE_MI_INDEX_URL = "https://openapi.twse.com.tw/v1/exchangeReport/MI_INDEX"
TWSE_BREADTH_URL = "https://openapi.twse.com.tw/v1/opendata/twtazu_od"
TWSE_COMPANY_PROFILE_URL = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"

OFFICIAL_INDEX_MAP = {
    "發行量加權股價指數": {
        "index_scope": "market",
        "sector_theme_key": None,
        "index_name": "發行量加權股價指數",
    },
    "電子工業類指數": {
        "index_scope": "sector_theme",
        "sector_theme_key": "twse_electronics",
        "index_name": "電子工業類指數",
    },
    "半導體類指數": {
        "index_scope": "sector_theme",
        "sector_theme_key": "twse_semiconductor",
        "index_name": "半導體類指數",
    },
    "電腦及週邊設備類指數": {
        "index_scope": "sector_theme",
        "sector_theme_key": "twse_computer_peripheral",
        "index_name": "電腦及週邊設備類指數",
    },
    "光電類指數": {
        "index_scope": "sector_theme",
        "sector_theme_key": "twse_optoelectronics",
        "index_name": "光電類指數",
    },
    "電子零組件類指數": {
        "index_scope": "sector_theme",
        "sector_theme_key": "twse_electronic_components",
        "index_name": "電子零組件類指數",
    },
    "通信網路類指數": {
        "index_scope": "sector_theme",
        "sector_theme_key": "twse_communications",
        "index_name": "通信網路類指數",
    },
    "電子通路類指數": {
        "index_scope": "sector_theme",
        "sector_theme_key": "twse_electronic_distribution",
        "index_name": "電子通路類指數",
    },
    "資訊服務類指數": {
        "index_scope": "sector_theme",
        "sector_theme_key": "twse_information_services",
        "index_name": "資訊服務類指數",
    },
    "其他電子類指數": {
        "index_scope": "sector_theme",
        "sector_theme_key": "twse_other_electronics",
        "index_name": "其他電子類指數",
    },
}

INDUSTRY_CODE_TO_THEME = {
    "24": "twse_semiconductor",
    "25": "twse_computer_peripheral",
    "26": "twse_optoelectronics",
    "27": "twse_communications",
    "28": "twse_electronic_components",
    "29": "twse_electronic_distribution",
    "30": "twse_information_services",
    "31": "twse_other_electronics",
}


def _twse_date_to_iso(value):
    text = str(value or "").strip()
    if len(text) != 7:
        return ""
    try:
        return f"{int(text[:3]) + 1911:04d}-{int(text[3:5]):02d}-{int(text[5:]):02d}"
    except ValueError:
        return ""


def _num(value):
    text = str(value or "").replace(",", "").strip()
    if text in ("", "-", "--"):
        return None
    try:
        return float(text)
    except ValueError:
        return None


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


def fetch_json(url):
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    return response.json()


def fetch_twse_index_rows():
    return fetch_json(TWSE_MI_INDEX_URL)


def fetch_twse_breadth_rows():
    return fetch_json(TWSE_BREADTH_URL)


def fetch_twse_company_profiles():
    return fetch_json(TWSE_COMPANY_PROFILE_URL)


def build_index_rows(raw_rows, trade_date=None, as_of=None):
    as_of = as_of or _now_iso()
    rows = []
    for raw in raw_rows or []:
        index_name = str(raw.get("指數") or "").strip()
        spec = OFFICIAL_INDEX_MAP.get(index_name)
        if not spec:
            continue
        row_trade_date = _twse_date_to_iso(raw.get("日期"))
        if trade_date and row_trade_date != trade_date:
            continue
        change_pct = _num(raw.get("漲跌百分比"))
        close = _num(raw.get("收盤指數"))
        if not row_trade_date or close is None:
            continue
        rows.append(
            {
                "trade_date": row_trade_date,
                "as_of": as_of,
                "index_scope": spec["index_scope"],
                "market_index": MARKET_INDEX,
                "sector_theme_key": spec["sector_theme_key"],
                "index_name": spec["index_name"],
                "source_family": SOURCE_FAMILY,
                "source_name": SOURCE_NAME,
                "index_method": "external_index",
                "open": None,
                "high": None,
                "low": None,
                "close": close,
                "change_pct": change_pct,
                "volume": None,
                "turnover": None,
                "member_count": None,
                "metadata": {
                    "rule_version": RULE_VERSION,
                    "twse_index_name": index_name,
                    "twse_change_sign": raw.get("漲跌"),
                    "twse_change_points": _num(raw.get("漲跌點數")),
                    "source_url": TWSE_MI_INDEX_URL,
                },
            }
        )
    return rows


def build_market_breadth(raw_rows, trade_date=None):
    for raw in raw_rows or []:
        if raw.get("類型") != "股票":
            continue
        row_trade_date = _twse_date_to_iso(raw.get("出表日期"))
        if trade_date and row_trade_date != trade_date:
            continue
        up = int(_num(raw.get("上漲")) or 0)
        down = int(_num(raw.get("下跌")) or 0)
        flat = int(_num(raw.get("持平")) or 0)
        limit_up = int(_num(raw.get("漲停")) or 0)
        limit_down = int(_num(raw.get("跌停")) or 0)
        denominator = up + down + flat
        return {
            "trade_date": row_trade_date,
            "denominator": denominator,
            "up_count": up,
            "down_count": down,
            "flat_count": flat,
            "limit_up_count": limit_up,
            "limit_down_count": limit_down,
            "up_ratio": round(up / denominator, 4) if denominator else 0,
            "source_name": BREADTH_SOURCE_NAME,
            "source_url": TWSE_BREADTH_URL,
        }
    return {}


def build_member_rows(raw_rows, watchlist_codes=None, as_of=None):
    as_of = as_of or _now_iso()
    watchlist_codes = {str(code) for code in (watchlist_codes or STOCKS.values())}
    rows = []
    for raw in raw_rows or []:
        stock_code = str(raw.get("公司代號") or "").strip()
        industry_code = str(raw.get("產業別") or "").strip()
        theme_key = INDUSTRY_CODE_TO_THEME.get(industry_code)
        if stock_code not in watchlist_codes or not theme_key:
            continue
        rows.append(
            {
                "sector_theme_key": theme_key,
                "stock_code": stock_code,
                "stock_name": raw.get("公司簡稱") or raw.get("公司名稱"),
                "market_index": MARKET_INDEX,
                "weight": None,
                "is_active": True,
                "valid_from": "2026-01-01",
                "valid_to": None,
                "source_family": SOURCE_FAMILY,
                "source_name": MEMBER_SOURCE_NAME,
                "metadata": {
                    "rule_version": RULE_VERSION,
                    "industry_code": industry_code,
                    "source_url": TWSE_COMPANY_PROFILE_URL,
                    "as_of": as_of,
                },
            }
        )
    return rows


def _market_change(index_rows):
    for row in index_rows:
        if row.get("index_scope") == "market":
            return row.get("change_pct")
    return None


def _support_level(theme_change, market_change, breadth):
    up_ratio = breadth.get("up_ratio", 0)
    if theme_change is None:
        return "weak"
    if theme_change >= 3 and up_ratio >= 0.55:
        return "confirmed"
    if market_change is not None and theme_change >= market_change and up_ratio >= 0.5:
        return "supporting"
    if theme_change > 0 and up_ratio >= 0.5:
        return "supporting"
    if theme_change <= -2 or up_ratio < 0.35:
        return "invalidated"
    return "weak"


def build_confirmed_rows(index_rows, breadth, as_of=None):
    as_of = as_of or _now_iso()
    market_change = _market_change(index_rows)
    confirmed = []
    for row in index_rows:
        if row.get("index_scope") != "sector_theme":
            continue
        theme_change = row.get("change_pct")
        support_level = _support_level(theme_change, market_change, breadth)
        confirmed.append(
            {
                "trade_date": row["trade_date"],
                "as_of": as_of,
                "market_index": MARKET_INDEX,
                "sector_theme_key": row["sector_theme_key"],
                "source_family": SOURCE_FAMILY,
                "source_name": SOURCE_NAME,
                "freshness": "fresh" if breadth else "insufficient-data",
                "evidence_value": {
                    "theme_change_pct": theme_change,
                    "market_change_pct": market_change,
                    "relative_change_pct": (
                        round(theme_change - market_change, 4)
                        if theme_change is not None and market_change is not None
                        else None
                    ),
                    "index_method": "external_index",
                    "twse_index_name": row["metadata"]["twse_index_name"],
                    "rule_version": RULE_VERSION,
                },
                "watchlist_breadth": breadth or {},
                "support_level": support_level,
                "evidence_status": "confirmed",
                "lineage": {
                    "rule_version": RULE_VERSION,
                    "source_tables": [
                        "market_theme_index_daily_bars",
                    ],
                    "source_urls": [
                        TWSE_MI_INDEX_URL,
                        TWSE_BREADTH_URL,
                    ],
                    "twse_index_name": row["metadata"]["twse_index_name"],
                    "breadth_source": breadth.get("source_name") if breadth else None,
                },
                "metadata": {
                    "generated_by": "scripts/backfill_market_theme_sources.py",
                    "source_quality": "official_twse_openapi",
                    "external_market_index": True,
                    "sector_member_source": MEMBER_SOURCE_NAME,
                },
                "notes": "Official TWSE index evidence; breadth is official TWSE market-wide stock breadth.",
            }
        )
    return confirmed


def build_source_payloads(index_raw, breadth_raw, profiles_raw, trade_date=None, as_of=None):
    as_of = as_of or _now_iso()
    index_rows = build_index_rows(index_raw, trade_date=trade_date, as_of=as_of)
    if not index_rows:
        return {
            "status": "blocked",
            "reason": "no official TWSE MI_INDEX rows matched",
            "member_rows": build_member_rows(profiles_raw, as_of=as_of),
            "index_rows": [],
            "confirmed_rows": [],
        }
    actual_trade_date = trade_date or index_rows[0]["trade_date"]
    breadth = build_market_breadth(breadth_raw, trade_date=actual_trade_date)
    return {
        "status": "ready",
        "reason": "ready",
        "member_rows": build_member_rows(profiles_raw, as_of=as_of),
        "index_rows": index_rows,
        "confirmed_rows": build_confirmed_rows(index_rows, breadth, as_of=as_of),
    }


def _delete_source_rows(client, table, source_name, trade_date=None):
    query = client.table(table).delete().eq("source_name", source_name)
    if trade_date and table != "sector_theme_members":
        query = query.eq("trade_date", trade_date)
    query.execute()


def upsert_source_payloads(client, payloads, trade_date=None):
    _delete_source_rows(client, "sector_theme_members", MEMBER_SOURCE_NAME)
    _delete_source_rows(client, "market_theme_index_daily_bars", SOURCE_NAME, trade_date)
    _delete_source_rows(client, "market_theme_confirmed_evidence", SOURCE_NAME, trade_date)

    if payloads["member_rows"]:
        client.table("sector_theme_members").insert(payloads["member_rows"]).execute()
    if payloads["index_rows"]:
        client.table("market_theme_index_daily_bars").insert(payloads["index_rows"]).execute()
    if payloads["confirmed_rows"]:
        upsert_market_theme_confirmed_evidence(payloads["confirmed_rows"], client)


def print_summary(trade_date, payloads):
    print("TWSE MARKET THEME SOURCE BACKFILL")
    print(f"trade_date: {trade_date or 'latest-from-source'}")
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
            "market_change_pct": row["evidence_value"]["market_change_pct"],
            "breadth": row["watchlist_breadth"].get("up_ratio"),
        }
        for row in payloads["confirmed_rows"]
    ]
    print(json.dumps(compact, ensure_ascii=False, indent=2, sort_keys=True))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Backfill market/theme source tables and confirmed evidence from official TWSE OpenAPI."
    )
    parser.add_argument("--trade-date", help="YYYY-MM-DD. Defaults to the latest date returned by TWSE.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--confirm-write", action="store_true")
    args = parser.parse_args(argv)

    if args.write and not args.confirm_write:
        raise SystemExit("Refusing to write without --confirm-write")
    if not args.write and not args.dry_run:
        raise SystemExit("Use --dry-run for preview, or --write --confirm-write for DB upsert")

    index_raw = fetch_twse_index_rows()
    breadth_raw = fetch_twse_breadth_rows()
    profiles_raw = fetch_twse_company_profiles()
    payloads = build_source_payloads(
        index_raw,
        breadth_raw,
        profiles_raw,
        trade_date=args.trade_date,
    )
    print_summary(args.trade_date, payloads)

    if payloads["status"] != "ready":
        raise SystemExit(1)
    if args.write:
        client = get_supabase_client()
        trade_date = args.trade_date or (
            payloads["index_rows"][0]["trade_date"] if payloads["index_rows"] else None
        )
        upsert_source_payloads(client, payloads, trade_date=trade_date)
        print("WRITE OK")
    else:
        print("DRY RUN ONLY: no database writes")


if __name__ == "__main__":
    main()
