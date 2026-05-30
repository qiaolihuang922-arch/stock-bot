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
from services.market_theme_evidence_store import (
    HANDOFF_ALLOWED_SOURCE_FAMILIES,
    REQUIRED_ROW_FIELDS,
    load_confirmed_market_theme_evidence,
    _source_family_forbidden,
    upsert_market_theme_confirmed_evidence,
)


RULE_VERSION = "twse_official_market_theme_v1"
MARKET_INDEX = "TAIEX"
SOURCE_FAMILY = "market_data"
SOURCE_NAME = "twse_openapi_mi_index"
MEMBER_SOURCE_NAME = "twse_openapi_t187ap03_L"
BREADTH_SOURCE_NAME = "twse_openapi_twtazu_od"
HEADERS = {"User-Agent": "Mozilla/5.0"}
DEFAULT_START_DATE = "2026-05-01"
DEFAULT_END_DATE = "2026-05-29"
ALLOWED_LINEAGE_SOURCE_TABLES = {
    "market_theme_confirmed_evidence",
    "market_theme_index_daily_bars",
    "sector_theme_members",
}
FORBIDDEN_LINEAGE_SOURCE_TABLES = {
    "daily_signal_snapshot",
    "report",
    "runtime",
    "local",
    "chat",
}
FORBIDDEN_SOURCE_FAMILIES = {
    "daily_signal_snapshot",
    "report",
    "runtime",
    "local",
    "chat",
}

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


def _empty_coverage():
    return {"first_trade_date": None, "last_trade_date": None, "trade_dates": 0}


def _coverage(rows):
    dates = sorted({row.get("trade_date") for row in rows or [] if row.get("trade_date")})
    if not dates:
        return _empty_coverage()
    return {
        "first_trade_date": dates[0],
        "last_trade_date": dates[-1],
        "trade_dates": len(dates),
    }


def _row_dates_outside_range(rows, start_date, end_date):
    return [
        row.get("trade_date")
        for row in rows or []
        if not row.get("trade_date") or row.get("trade_date") < start_date or row.get("trade_date") > end_date
    ]


def _confirmed_row_validation_errors(row, start_date, end_date):
    if not isinstance(row, dict):
        return ["row must be an object"]
    errors = []
    missing = sorted(
        field
        for field in REQUIRED_ROW_FIELDS
        if field not in row or row.get(field) in (None, "")
    )
    if missing:
        errors.append(f"required fields missing: {', '.join(missing)}")
    trade_date = row.get("trade_date")
    if trade_date and (trade_date < start_date or trade_date > end_date):
        errors.append("source date outside requested May range")
    source_family = str(row.get("source_family") or "").strip().lower()
    if source_family in FORBIDDEN_SOURCE_FAMILIES or _source_family_forbidden(source_family):
        errors.append("forbidden source_family")
    elif source_family not in HANDOFF_ALLOWED_SOURCE_FAMILIES:
        errors.append("source_family is not an approved persistent source")
    if row.get("freshness") != "fresh":
        errors.append("partial-coverage")
    if row.get("evidence_status") != "confirmed":
        errors.append("evidence_status is not confirmed")
    if not isinstance(row.get("evidence_value"), dict):
        errors.append("evidence_value must be an object")
    if not isinstance(row.get("watchlist_breadth"), dict):
        errors.append("watchlist_breadth must be an object")
    lineage = row.get("lineage")
    if not isinstance(lineage, dict):
        errors.append("lineage must be an object")
    else:
        source_tables = lineage.get("source_tables")
        if not isinstance(source_tables, list) or not source_tables:
            errors.append("lineage.source_tables missing")
        else:
            normalized_tables = {str(table or "").strip().lower() for table in source_tables}
            if normalized_tables & FORBIDDEN_LINEAGE_SOURCE_TABLES:
                errors.append("forbidden lineage source_tables")
            if not normalized_tables.issubset(ALLOWED_LINEAGE_SOURCE_TABLES):
                errors.append("lineage.source_tables is not an approved market/theme source")
    return errors


def _validated_confirmed_rows(payloads, start_date, end_date):
    rows = list(payloads.get("confirmed_rows") or [])
    if payloads.get("status") != "ready":
        return [], "missing-source"
    if not rows:
        return [], "missing-source"
    errors = []
    for row in rows:
        for error in _confirmed_row_validation_errors(row, start_date, end_date):
            if error and error not in errors:
                errors.append(error)
    if errors:
        return [], "; ".join(errors)
    return rows, ""


def _report_table(
    table,
    source_of_truth,
    historical_source_status,
    consumer_path,
    candidate_rows=0,
    validated_rows=0,
    written_rows=0,
    skipped_rows=0,
    duplicate_conflicts=0,
    coverage=None,
    pollution_guard="blocked",
    read_after_write="not-run",
    status="blocked",
    blocked_reasons=None,
):
    return {
        "table": table,
        "source_of_truth": source_of_truth,
        "historical_source_status": historical_source_status,
        "consumer_path": consumer_path,
        "candidate_rows": candidate_rows,
        "validated_rows": validated_rows,
        "written_rows": written_rows,
        "skipped_rows": skipped_rows,
        "coverage": coverage or _empty_coverage(),
        "duplicate_conflicts": duplicate_conflicts,
        "pollution_guard": pollution_guard,
        "read_after_write": read_after_write,
        "status": status,
        "blocked_reasons": blocked_reasons or [],
    }


def build_market_theme_history_backfill_report(
    payloads,
    start_date=DEFAULT_START_DATE,
    end_date=DEFAULT_END_DATE,
    write_execution="dry-run",
    written_confirmed_rows=0,
    read_after_write_result=None,
):
    confirmed_rows, confirmed_reason = _validated_confirmed_rows(payloads, start_date, end_date)
    confirmed_candidate_rows = len(payloads.get("confirmed_rows") or [])
    read_after_write = "not-run"
    if write_execution == "executed":
        read_after_write = (
            "passed"
            if isinstance(read_after_write_result, dict) and read_after_write_result.get("confirmed")
            else "blocked"
        )
    confirmed_table = _report_table(
        "market_theme_confirmed_evidence",
        "production DB market_theme_confirmed_evidence rows after validation",
        "partial" if confirmed_rows else "missing",
        "market_theme_evidence_store.evidence_trend",
        candidate_rows=confirmed_candidate_rows,
        validated_rows=len(confirmed_rows),
        written_rows=written_confirmed_rows,
        skipped_rows=max(confirmed_candidate_rows - len(confirmed_rows), 0),
        coverage=_coverage(confirmed_rows),
        pollution_guard="passed" if confirmed_rows else "blocked",
        read_after_write=read_after_write,
        status=(
            "executed"
            if write_execution == "executed" and written_confirmed_rows
            else "ready"
            if confirmed_rows
            else "blocked"
        ),
        blocked_reasons=[] if confirmed_rows else [confirmed_reason or "missing-source"],
    )

    index_rows = list(payloads.get("index_rows") or [])
    index_bad_dates = _row_dates_outside_range(index_rows, start_date, end_date)
    index_reasons = []
    if not index_rows:
        index_reasons.append("missing official historical index bars source")
    if index_bad_dates:
        index_reasons.append("source date outside requested May range")
    index_reasons.append("DB source table is not a direct strategy/report consumer in this script")
    index_table = _report_table(
        "market_theme_index_daily_bars",
        "official_or_owner_approved_historical_market_theme_bars",
        "not-consumed" if index_rows and not index_bad_dates else "missing",
        "confirmed evidence generation uses fetched official rows; DB table write skipped",
        candidate_rows=len(index_rows),
        validated_rows=0,
        skipped_rows=len(index_rows),
        coverage=_coverage(index_rows if not index_bad_dates else []),
        pollution_guard="passed" if index_rows and not index_bad_dates else "blocked",
        status="skipped",
        blocked_reasons=index_reasons,
    )

    member_rows = list(payloads.get("member_rows") or [])
    member_table = _report_table(
        "sector_theme_members",
        "official_or_owner_approved_historical_membership",
        "missing",
        "watchlist breadth generation requires dated membership; latest company profile is not May membership",
        candidate_rows=len(member_rows),
        validated_rows=0,
        skipped_rows=len(member_rows),
        coverage=_empty_coverage(),
        pollution_guard="blocked",
        status="blocked" if member_rows else "skipped",
        blocked_reasons=[
            "only latest company profile membership available; cannot prove May daily membership"
        ],
    )

    trend = (
        read_after_write_result.get("evidence_trend", {})
        if isinstance(read_after_write_result, dict)
        else {}
    )
    uses_history = bool(
        isinstance(read_after_write_result, dict)
        and read_after_write_result.get("confirmed")
        and trend.get("observed_days", 0) > 0
    )
    blocked_reasons = []
    for table in (confirmed_table, index_table, member_table):
        for reason in table.get("blocked_reasons", []):
            if reason not in blocked_reasons:
                blocked_reasons.append(reason)

    return {
        "mode": "market-theme-history-backfill",
        "date_range": {"start": start_date, "end": end_date},
        "write_execution": write_execution,
        "live_telegram": False,
        "schema_change": False,
        "tables": [confirmed_table, index_table, member_table],
        "daily_price_signal_snapshot_rewrite": "forbidden_as_primary_result",
        "strategy_consumption_check": {
            "uses_market_theme_confirmed_evidence_history": uses_history,
            "uses_only_daily_signal_snapshot": False,
            "observed_days": trend.get("observed_days", 0),
            "recent_supporting_days": trend.get("recent_supporting_days", 0),
            "support_streak_days": trend.get("support_streak_days", 0),
        },
        "blocked_reasons": blocked_reasons,
    }


def upsert_source_payloads(client, payloads, start_date=DEFAULT_START_DATE, end_date=DEFAULT_END_DATE):
    confirmed_rows, reason = _validated_confirmed_rows(payloads, start_date, end_date)
    if not confirmed_rows:
        raise ValueError(f"market_theme_confirmed_evidence blocked: {reason or 'missing-source'}")
    upsert_market_theme_confirmed_evidence(confirmed_rows, client)
    return {"market_theme_confirmed_evidence": len(confirmed_rows)}


def print_summary(report):
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Backfill market/theme source tables and confirmed evidence from official TWSE OpenAPI."
    )
    parser.add_argument("--trade-date", help="YYYY-MM-DD. Defaults to the latest date returned by TWSE.")
    parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    parser.add_argument("--end-date", default=DEFAULT_END_DATE)
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
    report = build_market_theme_history_backfill_report(
        payloads,
        start_date=args.start_date,
        end_date=args.end_date,
        write_execution="dry-run",
    )
    if args.write:
        client = get_supabase_client()
        write_counts = upsert_source_payloads(
            client,
            payloads,
            start_date=args.start_date,
            end_date=args.end_date,
        )
        requested_trade_date = args.trade_date or (
            payloads["confirmed_rows"][0]["trade_date"] if payloads["confirmed_rows"] else None
        )
        read_after_write = load_confirmed_market_theme_evidence(
            client=client,
            trade_date=requested_trade_date,
        )
        report = build_market_theme_history_backfill_report(
            payloads,
            start_date=args.start_date,
            end_date=args.end_date,
            write_execution="executed",
            written_confirmed_rows=write_counts.get("market_theme_confirmed_evidence", 0),
            read_after_write_result=read_after_write,
        )
    print_summary(report)
    confirmed_table = report["tables"][0]
    if confirmed_table["status"] == "blocked":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
