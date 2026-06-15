import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from supabase import create_client

import config
from core.holdings import HOLDING_CODES
from core.signal_snapshot import analyze_ohlcv_snapshot, apply_snapshot_boundaries
from scripts.backfill_signals import (
    BACKFILL_WARMUP_DAYS,
    available_coverage,
    partial_coverage_warnings,
    snapshot_to_payload,
    upsert_rows,
    validate_signal_payloads,
)
from scripts.dry_run_replay import DEFAULT_WATCHLIST, history_from_ohlcv, parse_date, trading_days


def _client():
    return create_client(config.SUPABASE_URL, config.SUPABASE_KEY)


def _date(value):
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def fetch_daily_price_ohlcv(client, stock_id, start_date, end_date):
    rows = (
        client.table("daily_price")
        .select("stock_id,trade_date,open,high,low,close,volume,source")
        .eq("stock_id", stock_id)
        .gte("trade_date", start_date.isoformat())
        .lte("trade_date", end_date.isoformat())
        .order("trade_date")
        .execute()
        .data
        or []
    )
    return [
        {
            **row,
            "trade_date": _date(row["trade_date"]),
            "open": row.get("open"),
            "high": row.get("high"),
            "low": row.get("low"),
            "close": row.get("close"),
            "volume": row.get("volume"),
            "source": row.get("source") or "daily_price",
        }
        for row in rows
        if row.get("close") is not None and row.get("volume") is not None
    ]


def build_rows_from_daily_price(client, target_stock_ids, context_stock_ids, start_date, end_date, version):
    warmup_start = start_date - timedelta(days=BACKFILL_WARMUP_DAYS)
    all_days = trading_days(warmup_start, end_date)
    replay_days = set(trading_days(start_date, end_date))
    ohlcv_by_stock = {
        stock_id: fetch_daily_price_ohlcv(client, stock_id, warmup_start, end_date)
        for stock_id in context_stock_ids
    }
    histories = {
        stock_id: history_from_ohlcv(ohlcv_by_stock[stock_id], all_days)
        for stock_id in context_stock_ids
    }

    price_rows = []
    signal_rows = []
    target_set = set(target_stock_ids)

    for trade_date in all_days:
        if trade_date not in replay_days:
            continue

        daily_snapshots = []
        source_rows = {}
        for stock_id in context_stock_ids:
            history_days, closes, volumes = histories[stock_id]
            if trade_date not in history_days:
                continue
            cutoff = history_days.index(trade_date) + 1
            if cutoff < 20:
                continue
            daily_snapshots.append(
                analyze_ohlcv_snapshot(
                    stock_id,
                    trade_date.isoformat(),
                    closes[:cutoff],
                    volumes[:cutoff],
                    version,
                )
            )
            source_rows[stock_id] = next(
                row for row in ohlcv_by_stock[stock_id]
                if row["trade_date"] == trade_date
            )

        apply_snapshot_boundaries(daily_snapshots, HOLDING_CODES)

        for snapshot in daily_snapshots:
            stock_id = snapshot["stock_id"]
            if stock_id not in target_set:
                continue
            source_row = source_rows[stock_id]
            price_rows.append({
                "stock_id": stock_id,
                "trade_date": trade_date.isoformat(),
                "open": source_row.get("open"),
                "high": source_row.get("high"),
                "low": source_row.get("low"),
                "close": source_row.get("close"),
                "volume": source_row.get("volume"),
                "source": source_row.get("source", "daily_price"),
            })
            signal_rows.append(snapshot_to_payload(snapshot))

    return price_rows, signal_rows


def main():
    parser = argparse.ArgumentParser(
        description="Backfill daily_signal_snapshot from existing daily_price rows."
    )
    parser.add_argument("--stock-id", required=True)
    parser.add_argument(
        "--context-watchlist",
        default=",".join(DEFAULT_WATCHLIST),
        help="Comma-separated stocks used to compute daily boundaries/best candidate context.",
    )
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--version", default="v21.1")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--confirm-write", action="store_true")
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()

    if args.write and not args.confirm_write:
        raise SystemExit("Refusing to write without --confirm-write")
    if not args.write and not args.dry_run:
        raise SystemExit("Use --dry-run or --write --confirm-write")

    start_date = parse_date(args.start_date)
    end_date = parse_date(args.end_date)
    warmup_start = start_date - timedelta(days=BACKFILL_WARMUP_DAYS)
    requested_trade_dates = [day.isoformat() for day in trading_days(start_date, end_date)]

    client = _client()
    context_stock_ids = [
        item.strip()
        for item in args.context_watchlist.split(",")
        if item.strip()
    ]
    if args.stock_id not in context_stock_ids:
        context_stock_ids.append(args.stock_id)
    price_rows, signal_rows = build_rows_from_daily_price(
        client,
        [args.stock_id],
        context_stock_ids,
        start_date,
        end_date,
        args.version,
    )
    coverage = available_coverage(signal_rows)
    expected_stock_ids = coverage["stock_ids"] if args.allow_partial else [args.stock_id]
    expected_trade_dates = coverage["trade_dates"] if args.allow_partial else requested_trade_dates
    errors = validate_signal_payloads(signal_rows, expected_stock_ids, expected_trade_dates)
    warnings = partial_coverage_warnings(signal_rows, [args.stock_id], requested_trade_dates)

    result = {
        "mode": "daily_price_snapshot_backfill",
        "stock_id": args.stock_id,
        "version": args.version,
        "source": "daily_price",
        "date_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "warmup_start": warmup_start.isoformat(),
        },
        "context_stock_ids": context_stock_ids,
        "daily_price_rows": len(price_rows),
        "daily_signal_snapshot_rows": len(signal_rows),
        "coverage": coverage,
        "warnings": warnings,
        "validation_errors": errors,
        "write": bool(args.write),
        "live_telegram": False,
        "schema_change": False,
    }

    if errors:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        raise SystemExit(1)

    if args.write:
        result["write_result"] = upsert_rows(price_rows, signal_rows, client=client)
    else:
        result["dry_run_only"] = True

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
