import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.holdings import HOLDING_CODES
from core.signal_snapshot import analyze_ohlcv_snapshot, apply_snapshot_boundaries
from core.signal_validator import validate_snapshots
from scripts.dry_run_replay import (
    DEFAULT_WATCHLIST,
    history_from_ohlcv,
    load_history,
    parse_date,
    trading_days
)
from services.stock_api import get_twse_ohlcv_history
from services.strategy_evidence import (
    build_audit_rows,
    calculate_outcome_metrics,
    feature_rows_from_signal_rows,
    market_rows_from_price_rows
)


def resolve_stock_ids(args):
    if args.stock_id:
        return [args.stock_id]

    if args.watchlist:
        return [
            item.strip()
            for item in args.watchlist.split(",")
            if item.strip()
        ]

    return DEFAULT_WATCHLIST


def build_rows(stock_ids, start_date, end_date, version, source):
    warmup_start = start_date - timedelta(days=90)
    all_days = trading_days(warmup_start, end_date)
    replay_days = set(trading_days(start_date, end_date))

    if source == "twse":
        ohlcv_by_stock = {
            stock_id: get_twse_ohlcv_history(
                stock_id,
                min(all_days),
                max(all_days)
            )
            for stock_id in stock_ids
        }
        histories = {
            stock_id: history_from_ohlcv(ohlcv_by_stock[stock_id], all_days)
            for stock_id in stock_ids
        }
    else:
        ohlcv_by_stock = {}
        histories = {
            stock_id: load_history(stock_id, all_days, source)
            for stock_id in stock_ids
        }

    price_rows = []
    signal_rows = []

    for trade_date in all_days:
        if trade_date not in replay_days:
            continue

        daily_snapshots = []

        for stock_id in stock_ids:
            history_days, closes, volumes = histories[stock_id]

            if trade_date not in history_days:
                continue

            cutoff = history_days.index(trade_date) + 1

            if cutoff < 20:
                continue

            # Pass only data available up to the backfill date to avoid lookahead bias.
            snapshot = analyze_ohlcv_snapshot(
                stock_id,
                trade_date.isoformat(),
                closes[:cutoff],
                volumes[:cutoff],
                version
            )
            daily_snapshots.append(snapshot)

            source_row = None
            if source == "twse":
                source_row = next(
                    (
                        row for row in ohlcv_by_stock[stock_id]
                        if row["trade_date"] == trade_date
                    ),
                    None
                )

            price_rows.append({
                "stock_id": stock_id,
                "trade_date": trade_date.isoformat(),
                "open": source_row.get("open") if source_row else None,
                "high": source_row.get("high") if source_row else None,
                "low": source_row.get("low") if source_row else None,
                "close": source_row.get("close") if source_row else snapshot["close"],
                "volume": source_row.get("volume") if source_row else volumes[cutoff - 1],
                "source": source
            })

        apply_snapshot_boundaries(daily_snapshots, HOLDING_CODES)

        for snapshot in daily_snapshots:
            signal_rows.append(snapshot_to_payload(snapshot))

    return price_rows, signal_rows


def build_rows_from_ohlcv(stock_id, ohlcv_rows, start_date, end_date, version):
    all_days = trading_days(start_date - timedelta(days=90), end_date)
    replay_days = set(trading_days(start_date, end_date))
    history_days, closes, volumes = history_from_ohlcv(ohlcv_rows, all_days)
    price_rows = []
    snapshots = []

    for trade_date in all_days:
        if trade_date not in replay_days or trade_date not in history_days:
            continue

        cutoff = history_days.index(trade_date) + 1

        if cutoff < 20:
            continue

        snapshot = analyze_ohlcv_snapshot(
            stock_id,
            trade_date.isoformat(),
            closes[:cutoff],
            volumes[:cutoff],
            version
        )
        snapshots.append(snapshot)

        source_row = next(
            row for row in ohlcv_rows
            if row["trade_date"] == trade_date
        )
        price_rows.append({
            "stock_id": stock_id,
            "trade_date": trade_date.isoformat(),
            "open": source_row.get("open"),
            "high": source_row.get("high"),
            "low": source_row.get("low"),
            "close": source_row.get("close"),
            "volume": source_row.get("volume"),
            "source": source_row.get("source", "twse")
        })

    apply_snapshot_boundaries(snapshots, HOLDING_CODES)
    return price_rows, [snapshot_to_payload(item) for item in snapshots]


def snapshot_to_payload(snapshot):
    return {
        "stock_id": snapshot["stock_id"],
        "trade_date": snapshot["trade_date"],
        "version": snapshot["version"],
        "close": snapshot["close"],
        "volume_ratio": snapshot["volume_ratio"],
        "pattern": snapshot["pattern"],
        "market_state": snapshot["market_state"],
        "structure_state": snapshot["structure_state"],
        "position_state": snapshot["position_state"],
        "rr": snapshot["rr"],
        "score": snapshot["score"],
        "heat_level": snapshot["heat_level"],
        "action": snapshot["action"],
        "reasons": snapshot["reasons"],
        "is_tradeable": snapshot["is_tradeable"],
        "is_best_candidate": snapshot["is_best_candidate"]
    }


def validate_signal_payloads(signal_rows, expected_stock_ids=None, expected_trade_dates=None):
    snapshots = [
        {
            **row,
            "raw_result": {}
        }
        for row in signal_rows
    ]
    return validate_snapshots(snapshots, expected_stock_ids, expected_trade_dates)


def get_supabase_client():
    from supabase import create_client
    from config import SUPABASE_KEY, SUPABASE_URL

    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY are required")

    return create_client(SUPABASE_URL, SUPABASE_KEY)


def build_evidence_rows(price_rows, signal_rows):
    market_rows = market_rows_from_price_rows(price_rows)
    feature_rows = feature_rows_from_signal_rows(signal_rows)
    outcome_rows = calculate_outcome_metrics(feature_rows, price_rows)
    audit_rows = build_audit_rows(feature_rows)
    return market_rows, feature_rows, outcome_rows, audit_rows


def upsert_rows(price_rows, signal_rows, evidence_rows=None):
    client = get_supabase_client()

    if price_rows:
        client.table("daily_price").upsert(
            price_rows,
            on_conflict="stock_id,trade_date"
        ).execute()

    if signal_rows:
        client.table("daily_signal_snapshot").upsert(
            signal_rows,
            on_conflict="stock_id,trade_date,version"
        ).execute()

    if evidence_rows:
        market_rows, feature_rows, outcome_rows, audit_rows = evidence_rows

        if market_rows:
            client.table("market_daily_bars").upsert(
                market_rows,
                on_conflict="stock_id,trade_date,source"
            ).execute()

        if feature_rows:
            client.table("strategy_feature_snapshots").upsert(
                feature_rows,
                on_conflict="stock_id,trade_date,strategy_version"
            ).execute()

        if outcome_rows:
            client.table("strategy_outcome_metrics").upsert(
                outcome_rows,
                on_conflict="stock_id,trade_date,strategy_version,horizon_days"
            ).execute()

        if audit_rows:
            client.table("strategy_classification_audit").upsert(
                audit_rows,
                on_conflict="stock_id,trade_date,strategy_version,distortion_type"
            ).execute()


def print_summary(price_rows, signal_rows, validation_errors, evidence_rows=None):
    tradeable = sum(1 for row in signal_rows if row.get("is_tradeable"))
    best = sum(1 for row in signal_rows if row.get("is_best_candidate"))
    evidence_rows = evidence_rows or ([], [], [], [])
    market_rows, feature_rows, outcome_rows, audit_rows = evidence_rows

    print("BACKFILL PLAN")
    print(f"daily_price rows: {len(price_rows)}")
    print(f"daily_signal_snapshot rows: {len(signal_rows)}")
    print(f"market_daily_bars rows: {len(market_rows)}")
    print(f"strategy_feature_snapshots rows: {len(feature_rows)}")
    print(f"strategy_outcome_metrics rows: {len(outcome_rows)}")
    print(f"strategy_classification_audit rows: {len(audit_rows)}")
    print(f"tradeable rows: {tradeable}")
    print(f"best candidate rows: {best}")

    if validation_errors:
        print("VALIDATION FAILED")
        for error in validation_errors[:50]:
            print(f"- {error}")
    else:
        print("VALIDATION OK")


def main():
    parser = argparse.ArgumentParser(description="v19 guarded backfill for daily price and signal snapshots")
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--stock-id")
    parser.add_argument("--watchlist")
    parser.add_argument("--source", choices=["synthetic", "twse"], default="twse")
    parser.add_argument("--version", default="v19.1.3")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--confirm-write", action="store_true")
    args = parser.parse_args()

    if args.write and not args.confirm_write:
        raise SystemExit("Refusing to write without --confirm-write")

    if not args.write and not args.dry_run:
        raise SystemExit("Use --dry-run for preview, or --write --confirm-write for DB upsert")

    stock_ids = resolve_stock_ids(args)
    start_date = parse_date(args.start_date)
    end_date = parse_date(args.end_date)
    price_rows, signal_rows = build_rows(
        stock_ids,
        start_date,
        end_date,
        args.version,
        args.source
    )
    validation_errors = validate_signal_payloads(
        signal_rows,
        stock_ids,
        [day.isoformat() for day in trading_days(start_date, end_date)]
    )
    evidence_rows = build_evidence_rows(price_rows, signal_rows)
    print_summary(price_rows, signal_rows, validation_errors, evidence_rows)

    if validation_errors:
        raise SystemExit(1)

    if args.write:
        # 中文註釋：v19.1.3 正式寫入必須通過 validation 且同時帶 --write --confirm-write。
        upsert_rows(price_rows, signal_rows, evidence_rows)
        print("WRITE OK")
    else:
        print("DRY RUN ONLY: no database writes")


if __name__ == "__main__":
    main()
