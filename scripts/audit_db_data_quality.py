import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from supabase import create_client

import config
from core.watchlist import WATCHLIST_CODES
from services.analysis import BREAKOUT_THRESHOLD, resistance_levels, retest_zone_from_levels


PAGE_SIZE = 1000
CURRENT_VERSION = "v21.1"
PRICE_EPSILON = 0.02
RATIO_EPSILON = 0.03
LEVEL_EPSILON = 0.06

DEFAULT_TABLES = [
    "daily_price",
    "daily_signal_snapshot",
    "market_theme_confirmed_evidence",
    "market_theme_index_daily_bars",
    "position_events",
    "positions",
    "sector_theme_members",
    "signal_items",
    "signal_outcomes",
    "signal_runs",
    "trades",
]

BUSINESS_KEYS = {
    "daily_price": ("stock_id", "trade_date"),
    "daily_signal_snapshot": ("stock_id", "trade_date", "version"),
    "market_theme_confirmed_evidence": ("trade_date", "market_index", "sector_theme_key"),
    "market_theme_index_daily_bars": (
        "trade_date",
        "index_scope",
        "market_index",
        "sector_theme_key",
    ),
    "positions": ("stock_code", "status"),
    "sector_theme_members": ("sector_theme_key", "stock_code", "valid_from"),
    "signal_runs": ("run_date", "run_phase"),
}

EXPECTED_CONSTANT_FIELDS = {
    "daily_signal_snapshot": {
        "breakout_reference_type": "strategy contract constant",
        "data_quality_state": "daily backfill quality state",
        "price_data_state": "daily backfill quality state",
        "retest_zone_label": "strategy contract constant",
        "rr_formula": "strategy contract constant",
        "rr_target_basis": "strategy contract constant",
        "version": "current backfill version",
        "volume_basis": "daily close volume basis",
        "volume_data_state": "daily backfill quality state",
    },
    "market_theme_confirmed_evidence": {
        "evidence_status": "confirmed evidence table contract",
        "freshness": "current backfill writes fresh rows",
        "market_index": "project tracks TAIEX only",
        "metadata": "same official source metadata",
        "notes": "same official source note",
        "source_family": "official market data source family",
        "source_name": "official TWSE index source",
    },
    "market_theme_index_daily_bars": {
        "index_method": "official external index source",
        "market_index": "project tracks TAIEX only",
        "source_family": "official market data source family",
        "source_name": "official TWSE index source",
    },
    "position_events": {
        "realized_profit_delta": "events currently do not calculate realized P/L",
        "telegram_chat_id": "single owner chat id",
    },
    "sector_theme_members": {
        "created_at": "single backfill batch",
        "is_active": "current active mapping",
        "market_index": "project tracks TAIEX only",
        "metadata": "same official source metadata",
        "source_family": "official market data source family",
        "source_name": "official member source",
        "updated_at": "single backfill batch",
        "valid_from": "current mapping start",
        "valid_to": "open-ended current mapping",
        "weight": "official source has no project weight",
    },
    "signal_items": {
        "run_id": "current limited stored run sample",
    },
    "signal_outcomes": {
        "max_drawdown_pct": "legacy outcome table did not store drawdown",
        "max_high_pct": "legacy outcome table did not store high watermark",
    },
    "signal_runs": {
        "best_stock": "legacy runs often had no single best stock",
        "run_phase": "stored historical signal runs are daily_close only",
    },
}

EXPECTED_NULL_FIELDS = {
    "daily_signal_snapshot": {
        "intraday_volume_run_rate": "daily backfill cannot infer intraday run rate",
    },
    "market_theme_index_daily_bars": {
        "open": "TWSE sector index source currently consumed as close/change only",
        "high": "TWSE sector index source currently consumed as close/change only",
        "low": "TWSE sector index source currently consumed as close/change only",
        "volume": "TWSE sector index source currently consumed as close/change only",
        "turnover": "TWSE sector index source currently consumed as close/change only",
        "member_count": "member breadth is stored in confirmed evidence",
    },
    "sector_theme_members": {
        "valid_to": "open-ended current mapping",
        "weight": "official source has no project weight",
    },
    "signal_items": {
        "intraday_volume_run_rate": "daily backfill cannot infer intraday run rate",
        "retest_days_since_breakout": "only populated when a retest setup exists",
        "retest_reference_price": "only populated when a retest setup exists",
    },
    "signal_outcomes": {
        "max_drawdown_pct": "legacy outcome table did not store drawdown",
        "max_high_pct": "legacy outcome table did not store high watermark",
    },
}


def _client():
    return create_client(config.SUPABASE_URL, config.SUPABASE_KEY)


def _fetch_all(client, table, page_size=PAGE_SIZE):
    rows = []
    start = 0
    while True:
        chunk = (
            client.table(table)
            .select("*")
            .range(start, start + page_size - 1)
            .execute()
            .data
            or []
        )
        rows.extend(chunk)
        if len(chunk) < page_size:
            break
        start += page_size
    return rows


def _num(value):
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _round(value, digits=4):
    value = _num(value)
    return None if value is None else round(value, digits)


def _stable(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def duplicate_report(rows, key_fields):
    counter = Counter(tuple(row.get(field) for field in key_fields) for row in rows)
    duplicate_groups = [
        {"key": list(key), "count": count}
        for key, count in counter.items()
        if count > 1
    ]
    return {
        "key": list(key_fields),
        "duplicate_groups": len(duplicate_groups),
        "duplicate_extra_rows": sum(item["count"] - 1 for item in duplicate_groups),
        "samples": duplicate_groups[:20],
    }


def constant_field_report(table, rows):
    if len(rows) < 2:
        return []
    columns = sorted({key for row in rows for key in row.keys()})
    expected_constants = EXPECTED_CONSTANT_FIELDS.get(table, {})
    expected_nulls = EXPECTED_NULL_FIELDS.get(table, {})
    reports = []
    for column in columns:
        values = [row.get(column) for row in rows]
        distinct = {_stable(value) for value in values}
        nonnull = [value for value in values if value is not None]
        if len(distinct) != 1:
            continue
        value = values[0] if values else None
        if column in expected_constants:
            classification = "expected_constant"
            note = expected_constants[column]
        elif value is None and column in expected_nulls:
            classification = "expected_null_source_gap"
            note = expected_nulls[column]
        else:
            classification = "review_constant"
            note = "constant across fetched rows; verify whether this is source-limited or stale"
        reports.append(
            {
                "table": table,
                "column": column,
                "classification": classification,
                "nonnull": len(nonnull),
                "rows": len(rows),
                "value": value,
                "note": note,
            }
        )
    return reports


def mostly_null_report(table, rows, threshold=0.95):
    if len(rows) < 2:
        return []
    columns = sorted({key for row in rows for key in row.keys()})
    expected_nulls = EXPECTED_NULL_FIELDS.get(table, {})
    reports = []
    for column in columns:
        values = [row.get(column) for row in rows]
        null_count = sum(1 for value in values if value is None)
        if null_count / max(len(values), 1) < threshold:
            continue
        classification = (
            "expected_null_source_gap"
            if column in expected_nulls
            else "review_mostly_null"
        )
        reports.append(
            {
                "table": table,
                "column": column,
                "classification": classification,
                "nonnull": len(values) - null_count,
                "nulls": null_count,
                "rows": len(rows),
                "note": expected_nulls.get(column) or "mostly null; verify writer/consumer contract",
            }
        )
    return reports


def daily_price_quality(rows):
    issues = []
    by_stock = defaultdict(list)
    for row in rows:
        by_stock[str(row.get("stock_id"))].append(row)
        open_ = _num(row.get("open"))
        high = _num(row.get("high"))
        low = _num(row.get("low"))
        close = _num(row.get("close"))
        volume = _num(row.get("volume"))
        key = {"stock_id": row.get("stock_id"), "trade_date": row.get("trade_date")}
        missing = [
            name
            for name, value in [
                ("open", open_),
                ("high", high),
                ("low", low),
                ("close", close),
                ("volume", volume),
            ]
            if value is None
        ]
        if missing:
            issues.append({"severity": "fix", "type": "daily_price_missing_ohlcv", **key, "fields": missing})
            continue
        if min(open_, high, low, close) <= 0 or volume < 0:
            issues.append({"severity": "fix", "type": "daily_price_nonpositive_ohlcv", **key})
        if high < max(open_, low, close) or low > min(open_, high, close):
            issues.append(
                {
                    "severity": "fix",
                    "type": "daily_price_ohlc_range_invalid",
                    **key,
                    "open": open_,
                    "high": high,
                    "low": low,
                    "close": close,
                }
            )

    coverage = {}
    stale_or_short = []
    for stock_id, stock_rows in sorted(by_stock.items()):
        dates = sorted(str(row.get("trade_date")) for row in stock_rows if row.get("trade_date"))
        coverage[stock_id] = {
            "rows": len(stock_rows),
            "first_trade_date": dates[0] if dates else None,
            "last_trade_date": dates[-1] if dates else None,
        }
        if len(stock_rows) < 250:
            stale_or_short.append({"stock_id": stock_id, "rows": len(stock_rows), "reason": "less_than_one_year_rows"})
    return {"issues": issues, "coverage_by_stock": coverage, "coverage_warnings": stale_or_short}


def _avg(values):
    return sum(values) / len(values) if values else None


def _volume_ratio(values, window):
    sample = values[-window:]
    avg = _avg(sample)
    if not avg or avg <= 0:
        return None
    return round(values[-1] / avg, 2)


def _signal_expected_values(price_rows_by_stock, stock_id, trade_date):
    stock_rows = sorted(
        price_rows_by_stock.get(str(stock_id), []),
        key=lambda row: str(row.get("trade_date")),
    )
    eligible = [row for row in stock_rows if str(row.get("trade_date")) <= str(trade_date)]
    if not eligible:
        return None
    closes = [_num(row.get("close")) for row in eligible if _num(row.get("close")) is not None]
    volumes = [_num(row.get("volume")) for row in eligible if _num(row.get("volume")) is not None]
    latest = eligible[-1]
    expected = {
        "close": _round(latest.get("close"), 2),
        "volume_ratio_10": _volume_ratio(volumes, 10) if volumes else None,
        "volume_ratio_20": _volume_ratio(volumes, 20) if volumes else None,
    }
    if len(closes) >= 20:
        levels = resistance_levels(closes)
        retest = retest_zone_from_levels(levels)
        price = closes[-1]
        breakout_20 = levels.get("breakout_price_20")
        breakout_60 = levels.get("breakout_price_60")
        expected.update(
            {
                "resistance_20": _round(levels.get("resistance_20"), 2),
                "resistance_60": _round(levels.get("resistance_60"), 2),
                "breakout_price_20": _round(breakout_20, 2),
                "breakout_price_60": _round(breakout_60, 2),
                "breakout_distance_20": (
                    _round((breakout_20 - price) / price * 100, 2)
                    if price and breakout_20
                    else None
                ),
                "breakout_distance_60": (
                    _round((breakout_60 - price) / price * 100, 2)
                    if price and breakout_60
                    else None
                ),
                "retest_zone_low": _round(retest.get("retest_zone_low"), 2),
                "retest_zone_high": _round(retest.get("retest_zone_high"), 2),
            }
        )
    return expected


def _diff_issue(row, field, actual, expected, epsilon):
    if actual is None or expected is None:
        return None
    if abs(float(actual) - float(expected)) <= epsilon:
        return None
    return {
        "severity": "fix",
        "type": "daily_signal_snapshot_mismatch",
        "stock_id": row.get("stock_id"),
        "trade_date": row.get("trade_date"),
        "version": row.get("version"),
        "field": field,
        "actual": _round(actual, 4),
        "expected_from_daily_price": _round(expected, 4),
    }


def signal_snapshot_consistency(signal_rows, price_rows):
    issues = []
    price_by_key = {
        (str(row.get("stock_id")), str(row.get("trade_date"))): row
        for row in price_rows
    }
    price_rows_by_stock = defaultdict(list)
    for row in price_rows:
        price_rows_by_stock[str(row.get("stock_id"))].append(row)

    current_rows = [row for row in signal_rows if row.get("version") == CURRENT_VERSION]
    for row in current_rows:
        key = (str(row.get("stock_id")), str(row.get("trade_date")))
        price_row = price_by_key.get(key)
        if not price_row:
            issues.append(
                {
                    "severity": "fix",
                    "type": "daily_signal_snapshot_missing_daily_price",
                    "stock_id": row.get("stock_id"),
                    "trade_date": row.get("trade_date"),
                    "version": row.get("version"),
                }
            )
            continue
        expected = _signal_expected_values(price_rows_by_stock, row.get("stock_id"), row.get("trade_date"))
        if not expected:
            continue
        checks = [
            ("close", PRICE_EPSILON),
            ("volume_ratio", RATIO_EPSILON),
            ("volume_ratio_10", RATIO_EPSILON),
            ("volume_ratio_20", RATIO_EPSILON),
            ("resistance_20", LEVEL_EPSILON),
            ("resistance_60", LEVEL_EPSILON),
            ("breakout_price_20", LEVEL_EPSILON),
            ("breakout_price_60", LEVEL_EPSILON),
            ("breakout_distance_20", LEVEL_EPSILON),
            ("breakout_distance_60", LEVEL_EPSILON),
            ("retest_zone_low", LEVEL_EPSILON),
            ("retest_zone_high", LEVEL_EPSILON),
        ]
        expected.setdefault("volume_ratio", expected.get("volume_ratio_10"))
        for field, epsilon in checks:
            issue = _diff_issue(row, field, _num(row.get(field)), expected.get(field), epsilon)
            if issue:
                issues.append(issue)
    return {
        "current_version_rows": len(current_rows),
        "issues": issues,
    }


def snapshot_coverage(signal_rows, price_rows, coverage_start_date=None):
    signals = {
        (str(row.get("stock_id")), str(row.get("trade_date")))
        for row in signal_rows
        if row.get("version") == CURRENT_VERSION
    }
    missing = []
    current_window_missing = []
    by_stock = defaultdict(list)
    for row in price_rows:
        by_stock[str(row.get("stock_id"))].append(row)
    for stock_id, rows in sorted(by_stock.items()):
        sorted_rows = sorted(rows, key=lambda row: str(row.get("trade_date")))
        for index, row in enumerate(sorted_rows):
            if index < 19:
                continue
            key = (stock_id, str(row.get("trade_date")))
            if key not in signals:
                item = {"stock_id": stock_id, "trade_date": row.get("trade_date")}
                missing.append(item)
                if coverage_start_date and str(row.get("trade_date")) >= str(coverage_start_date):
                    current_window_missing.append(item)
    return {
        "eligible_daily_price_rows_after_warmup": sum(max(len(rows) - 19, 0) for rows in by_stock.values()),
        "missing_current_snapshot_rows": len(missing),
        "sample_missing_current_snapshot_rows": missing[:20],
        "coverage_start_date": coverage_start_date,
        "missing_current_window_snapshot_rows": len(current_window_missing),
        "sample_missing_current_window_snapshot_rows": current_window_missing[:20],
    }


def table_profiles(rows_by_table):
    profiles = {}
    for table, rows in sorted(rows_by_table.items()):
        duplicate = None
        key = BUSINESS_KEYS.get(table)
        if key and rows and all(field in rows[0] for field in key):
            duplicate = duplicate_report(rows, key)
        profiles[table] = {
            "rows": len(rows),
            "business_key_duplicate": duplicate,
            "constant_fields": constant_field_report(table, rows),
            "mostly_null_fields": mostly_null_report(table, rows),
        }
    return profiles


def build_quality_audit(rows_by_table, coverage_start_date=None):
    price_rows = rows_by_table.get("daily_price", [])
    signal_rows = rows_by_table.get("daily_signal_snapshot", [])
    price = daily_price_quality(price_rows)
    signal = signal_snapshot_consistency(signal_rows, price_rows)
    coverage = snapshot_coverage(signal_rows, price_rows, coverage_start_date=coverage_start_date)
    profiles = table_profiles(rows_by_table)
    fix_issues = []
    fix_issues.extend(price["issues"])
    fix_issues.extend(signal["issues"])
    for table, profile in profiles.items():
        duplicate = profile.get("business_key_duplicate") or {}
        if duplicate.get("duplicate_extra_rows"):
            fix_issues.append(
                {
                    "severity": "fix",
                    "type": "business_key_duplicate",
                    "table": table,
                    "key": duplicate.get("key"),
                    "duplicate_extra_rows": duplicate.get("duplicate_extra_rows"),
                }
            )
    review_items = []
    for table, profile in profiles.items():
        review_items.extend(
            item for item in profile.get("constant_fields", []) if item["classification"] == "review_constant"
        )
        review_items.extend(
            item for item in profile.get("mostly_null_fields", []) if item["classification"] == "review_mostly_null"
        )
    return {
        "mode": "db_data_quality_audit",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "read_only": True,
        "db_write": False,
        "schema_change": False,
        "live_telegram": False,
        "version": CURRENT_VERSION,
        "tables": profiles,
        "daily_price": price,
        "daily_signal_snapshot": {
            **signal,
            "coverage_against_daily_price": coverage,
        },
        "fix_issues": fix_issues,
        "review_items": review_items,
        "summary": {
            "tables_checked": len(rows_by_table),
            "fix_issue_count": len(fix_issues),
            "review_item_count": len(review_items),
            "safe_to_delete_rows": 0,
            "delete_plan": "none; use prune/backfill scripts only after a dedicated dry-run plan",
            "current_window_missing_snapshot_rows": coverage["missing_current_window_snapshot_rows"],
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Read-only production DB data-quality audit.")
    parser.add_argument("--tables", default=",".join(DEFAULT_TABLES))
    parser.add_argument(
        "--coverage-start-date",
        default=(datetime.now(timezone.utc).date() - timedelta(days=730)).isoformat(),
        help="Lower bound for current strategy-consumed snapshot coverage.",
    )
    parser.add_argument("--output")
    args = parser.parse_args()

    client = _client()
    rows_by_table = {}
    errors = []
    for table in [item.strip() for item in args.tables.split(",") if item.strip()]:
        try:
            rows_by_table[table] = _fetch_all(client, table)
        except Exception as error:
            errors.append({"table": table, "error": str(error)})
            rows_by_table[table] = []

    artifact = build_quality_audit(rows_by_table, coverage_start_date=args.coverage_start_date)
    artifact["errors"] = errors
    text = json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
