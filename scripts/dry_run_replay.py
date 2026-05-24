import argparse
import csv
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.holdings import HOLDING_CODES
from core.signal_snapshot import analyze_ohlcv_snapshot, apply_snapshot_boundaries
from core.signal_validator import validate_snapshots
from core.watchlist import WATCHLIST_CODES
from services.stock_api import get_twse_ohlcv_history


DEFAULT_WATCHLIST = WATCHLIST_CODES


def parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date()


def trading_days(start_date, end_date):
    days = []
    current = start_date

    while current <= end_date:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)

    return days


def default_date_range():
    end = datetime.now().date()

    while end.weekday() >= 5:
        end -= timedelta(days=1)

    days = []
    current = end

    while len(days) < 10:
        if current.weekday() < 5:
            days.append(current)
        current -= timedelta(days=1)

    return min(days), max(days)


def synthetic_history(stock_id, dates):
    seed = sum(ord(ch) for ch in str(stock_id))
    base = 80 + seed % 90
    closes = []
    volumes = []

    for idx, _ in enumerate(dates):
        drift = idx * (0.18 + (seed % 5) * 0.03)
        wave = ((idx % 7) - 3) * 0.35
        close = round(base + drift + wave, 2)

        if idx == len(dates) - 3 and seed % 4 == 0:
            close = round(close * 1.04, 2)
        elif idx == len(dates) - 2 and seed % 4 == 1:
            close = round(close * 1.098, 2)
        elif idx == len(dates) - 1 and seed % 4 == 2:
            close = round(close * 0.97, 2)

        volume_base = 1000 + (seed % 8) * 120
        volume = int(volume_base * (1 + ((idx % 5) - 2) * 0.08))

        if idx == len(dates) - 1 and seed % 3 == 0:
            volume = int(volume * 1.8)
        elif idx == len(dates) - 1 and seed % 3 == 1:
            volume = int(volume * 0.55)

        closes.append(close)
        volumes.append(max(volume, 1))

    return closes, volumes


def history_from_ohlcv(ohlcv_rows, all_days):
    by_date = {
        row["trade_date"]: row
        for row in ohlcv_rows
    }
    closes = []
    volumes = []
    aligned_days = []

    for trade_date in all_days:
        row = by_date.get(trade_date)
        if not row:
            continue
        closes.append(row["close"])
        volumes.append(row["volume"])
        aligned_days.append(trade_date)

    return aligned_days, closes, volumes


def load_history(stock_id, all_days, source):
    if source == "synthetic":
        return all_days, *synthetic_history(stock_id, all_days)

    if source == "twse":
        ohlcv = get_twse_ohlcv_history(
            stock_id,
            min(all_days),
            max(all_days)
        )
        return history_from_ohlcv(ohlcv, all_days)

    raise ValueError(f"Unsupported source: {source}")


def build_replay_rows(stock_ids, start_date, end_date, version, source="synthetic"):
    # 中文註釋：v19.1.3 replay warmup 與 backfill 對齊 90 天，避免同區間 dry-run 樣本不足。
    warmup_start = start_date - timedelta(days=90)
    all_days = trading_days(warmup_start, end_date)
    replay_days = set(trading_days(start_date, end_date))
    histories = {
        stock_id: load_history(stock_id, all_days, source)
        for stock_id in stock_ids
    }
    rows = []

    for trade_date in all_days:
        if trade_date not in replay_days:
            continue

        daily = []

        for stock_id in stock_ids:
            history_days, closes, volumes = histories[stock_id]

            if trade_date not in history_days:
                continue

            cutoff = history_days.index(trade_date) + 1

            if cutoff < 20:
                continue

            # 中文註釋：v19.1.3 replay 每日只傳入當天以前含當天資料，避免未來資料污染回測。
            daily.append(
                analyze_ohlcv_snapshot(
                    stock_id,
                    trade_date.isoformat(),
                    closes[:cutoff],
                    volumes[:cutoff],
                    version
                )
            )

        apply_snapshot_boundaries(daily, HOLDING_CODES)
        rows.extend(daily)

    return rows


def emit_csv(rows):
    fields = [
        "stock_id",
        "trade_date",
        "close",
        "volume_ratio",
        "pattern",
        "market_state",
        "structure_state",
        "position_state",
        "rr",
        "score",
        "heat_level",
        "action",
        "reasons",
        "is_tradeable",
        "is_best_candidate"
    ]

    writer = csv.DictWriter(sys.stdout, fieldnames=fields)
    writer.writeheader()

    for row in rows:
        output = {field: row.get(field) for field in fields}
        output["reasons"] = "|".join(row.get("reasons") or [])
        writer.writerow(output)


def emit_validation(rows, expected_stock_ids=None, expected_trade_dates=None):
    errors = validate_snapshots(rows, expected_stock_ids, expected_trade_dates)

    if not errors:
        print("VALIDATION OK", file=sys.stderr)
        return

    print("VALIDATION FAILED", file=sys.stderr)
    for error in errors[:50]:
        print(f"- {error}", file=sys.stderr)

    if len(errors) > 50:
        print(f"... {len(errors) - 50} more errors", file=sys.stderr)

    raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description="v19 dry-run replay without database writes")
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--stock-id")
    parser.add_argument("--watchlist")
    parser.add_argument("--source", choices=["synthetic", "twse"], default="synthetic")
    parser.add_argument("--version", default="v19.1.3")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()

    if not args.dry_run:
        raise SystemExit("Refusing to run without --dry-run. Formal backfill is intentionally not implemented yet.")

    start_date, end_date = default_date_range()

    if args.start_date:
        start_date = parse_date(args.start_date)

    if args.end_date:
        end_date = parse_date(args.end_date)

    if args.stock_id:
        stock_ids = [args.stock_id]
    elif args.watchlist:
        stock_ids = [item.strip() for item in args.watchlist.split(",") if item.strip()]
    else:
        stock_ids = DEFAULT_WATCHLIST

    rows = build_replay_rows(stock_ids, start_date, end_date, args.version, args.source)
    if args.validate:
        emit_validation(rows, stock_ids, [day.isoformat() for day in trading_days(start_date, end_date)])
    emit_csv(rows)


if __name__ == "__main__":
    main()
