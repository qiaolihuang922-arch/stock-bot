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
from core.generator import entry_blockers, is_valid_entry, unheld_funnel_state
from core.holdings import HOLDING_CODES
from core.signal_snapshot import analyze_ohlcv_snapshot, apply_snapshot_boundaries
from core.watchlist import STOCKS, WATCHLIST_CODES
from scripts.dry_run_replay import history_from_ohlcv, parse_date, trading_days


VERSION = "v21.1"
DEFAULT_LOOKBACK_DAYS = 730
WARMUP_DAYS = 90


def _client():
    return create_client(config.SUPABASE_URL, config.SUPABASE_KEY)


def _date(value):
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def _num(value):
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_round(value, digits=4):
    value = _num(value)
    return None if value is None else round(value, digits)


def _stock_name_by_id():
    return {str(code): name for name, code in STOCKS.items()}


def fetch_daily_price_rows(client, stock_id, start_date, end_date, page_size=1000):
    rows = []
    start = 0
    while True:
        page = (
            client.table("daily_price")
            .select("stock_id,trade_date,open,high,low,close,volume,source")
            .eq("stock_id", stock_id)
            .gte("trade_date", start_date.isoformat())
            .lte("trade_date", end_date.isoformat())
            .order("trade_date")
            .range(start, start + page_size - 1)
            .execute()
            .data
            or []
        )
        rows.extend(page)
        if len(page) < page_size:
            break
        start += page_size
    return [
        {
            **row,
            "trade_date": _date(row["trade_date"]),
            "close": _num(row.get("close")),
            "volume": _num(row.get("volume")),
            "source": row.get("source") or "daily_price",
        }
        for row in rows
        if row.get("trade_date") and _num(row.get("close")) is not None and _num(row.get("volume")) is not None
    ]


def recent_daily_price_points(rows, trade_date, max_points=8):
    points = []
    for row in rows:
        if row["trade_date"] > trade_date:
            continue
        points.append({
            "trade_date": row["trade_date"].isoformat(),
            "close": row["close"],
            "source": "daily_price",
        })
    return points[-max_points:]


def cross_day_context(rows, trade_date, stock_id):
    points = recent_daily_price_points(rows, trade_date)
    return {
        "source_status": "ready" if points else "insufficient-data",
        "source_of_truth": ["daily_price"] if points else [],
        "stock_code": str(stock_id),
        "recent_daily_price_points": points,
        "previous_state": "unknown",
        "previous_action": "unknown",
        "consecutive_observe_days": 0,
        "repair_status": "unknown",
        "failure_status": "unknown",
        "historical_evidence_weight": 0,
    }


def payload_from_snapshot(stock_id, stock_name, snapshot, rows, trade_date, history_days, closes, volumes):
    cutoff = history_days.index(trade_date) + 1
    result = dict(snapshot.get("raw_result") or {})
    result["is_tradeable"] = bool(snapshot.get("is_tradeable"))
    result["is_best_candidate"] = bool(snapshot.get("is_best_candidate"))
    return {
        "stock_code": str(stock_id),
        "stock_name": stock_name,
        "price": snapshot.get("close"),
        "change": result.get("live_change"),
        "volume_ratio": snapshot.get("volume_ratio"),
        "closes": closes[:cutoff],
        "volumes": volumes[:cutoff],
        "result": result,
        "cross_day_context": cross_day_context(rows, trade_date, stock_id),
        "holding": None,
    }


def primary_blocker(result, state):
    blockers = entry_blockers(result)
    if blockers:
        return str(blockers[0])
    if state in {"可買", "趨勢延續", "可準備"}:
        return state
    if result.get("entry_quality") not in {None, "A+", "A", "B"}:
        return f"買點品質{result.get('entry_quality')}"
    if result.get("decision") != "BUY":
        return result.get("decision") or "NO_BUY_DECISION"
    return "unknown"


def replay_from_daily_price(rows_by_stock, start_date, end_date, version=VERSION):
    stock_names = _stock_name_by_id()
    replay_days = set(trading_days(start_date, end_date))
    histories = {}
    for stock_id, rows in rows_by_stock.items():
        all_days = trading_days(min(row["trade_date"] for row in rows), max(row["trade_date"] for row in rows))
        histories[stock_id] = history_from_ohlcv(rows, all_days)

    events = []
    snapshots_by_day = defaultdict(list)
    snapshots_by_stock_day = {}
    for trade_date in sorted(replay_days):
        daily = []
        source = {}
        for stock_id, rows in rows_by_stock.items():
            history_days, closes, volumes = histories[stock_id]
            if trade_date not in history_days:
                continue
            cutoff = history_days.index(trade_date) + 1
            if cutoff < 20:
                continue
            snapshot = analyze_ohlcv_snapshot(
                stock_id,
                trade_date.isoformat(),
                closes[:cutoff],
                volumes[:cutoff],
                version,
            )
            daily.append(snapshot)
            source[stock_id] = (history_days, closes, volumes)

        apply_snapshot_boundaries(daily, HOLDING_CODES)
        for snapshot in daily:
            stock_id = str(snapshot["stock_id"])
            snapshots_by_day[trade_date].append(snapshot)
            snapshots_by_stock_day[(stock_id, trade_date)] = snapshot
            history_days, closes, volumes = source[stock_id]
            payload = payload_from_snapshot(
                stock_id,
                stock_names.get(stock_id, stock_id),
                snapshot,
                rows_by_stock[stock_id],
                trade_date,
                history_days,
                closes,
                volumes,
            )
            state = unheld_funnel_state(stock_names.get(stock_id, stock_id), payload)
            result = payload["result"]
            valid_entry = is_valid_entry(result)
            events.append({
                "trade_date": trade_date.isoformat(),
                "stock_id": stock_id,
                "stock_name": stock_names.get(stock_id, stock_id),
                "close": _safe_round(snapshot.get("close"), 4),
                "funnel_state": state,
                "snapshot_is_tradeable": bool(snapshot.get("is_tradeable")),
                "valid_entry": bool(valid_entry),
                "decision": result.get("decision"),
                "decision_type": result.get("decision_type"),
                "action": _safe_round(result.get("action"), 4),
                "entry_quality": result.get("entry_quality"),
                "market_grade": result.get("market_grade"),
                "volume_state": result.get("volume_state"),
                "heat_state": result.get("heat_state"),
                "trade_state": result.get("trade_state"),
                "price_behavior": result.get("price_behavior"),
                "structure_phase": result.get("structure_phase"),
                "rr": _safe_round(result.get("rr"), 4),
                "breakout_distance": _safe_round(result.get("breakout_distance"), 4),
                "volume_ratio_10": _safe_round(snapshot.get("volume_ratio_10"), 4),
                "volume_ratio_20": _safe_round(snapshot.get("volume_ratio_20"), 4),
                "primary_blocker": primary_blocker(result, state),
            })
    return events


def transition_after_state(events, source_state="等回測"):
    by_stock = defaultdict(list)
    for event in events:
        by_stock[event["stock_id"]].append(event)
    transitions = Counter()
    examples = []
    for stock_events in by_stock.values():
        stock_events.sort(key=lambda item: item["trade_date"])
        for left, right in zip(stock_events, stock_events[1:]):
            if left["funnel_state"] != source_state:
                continue
            transitions[right["funnel_state"]] += 1
            if len(examples) < 20:
                examples.append({
                    "from_date": left["trade_date"],
                    "to_date": right["trade_date"],
                    "stock_id": left["stock_id"],
                    "stock_name": left["stock_name"],
                    "from_state": left["funnel_state"],
                    "to_state": right["funnel_state"],
                    "to_primary_blocker": right["primary_blocker"],
                    "from_close": left["close"],
                    "to_close": right["close"],
                })
    return {
        "from_state": source_state,
        "next_state_counts": dict(transitions.most_common()),
        "examples": examples,
    }


def summarize(events, rows_by_stock, start_date, end_date, version):
    state_counts = Counter(event["funnel_state"] for event in events)
    blocker_counts = Counter(event["primary_blocker"] for event in events if event["funnel_state"] not in {"可買", "趨勢延續"})
    buy_like = [event for event in events if event["funnel_state"] in {"可買", "趨勢延續", "可準備"}]
    buyable = [event for event in events if event["funnel_state"] in {"可買", "趨勢延續"}]
    snapshot_tradeable = [event for event in events if event["snapshot_is_tradeable"]]
    false_negative = [
        event for event in events
        if event["snapshot_is_tradeable"] and event["funnel_state"] not in {"可買", "趨勢延續", "可準備"}
    ]
    by_stock = defaultdict(Counter)
    for event in events:
        by_stock[event["stock_id"]][event["funnel_state"]] += 1
    stock_summary = {
        stock_id: {
            "stock_name": next((event["stock_name"] for event in events if event["stock_id"] == stock_id), stock_id),
            "state_counts": dict(counter.most_common()),
            "buy_like_days": sum(counter.get(state, 0) for state in ["可買", "趨勢延續", "可準備"]),
        }
        for stock_id, counter in sorted(by_stock.items())
    }
    coverage = {
        stock_id: {
            "rows": len(rows),
            "first_date": min(row["trade_date"] for row in rows).isoformat() if rows else None,
            "last_date": max(row["trade_date"] for row in rows).isoformat() if rows else None,
        }
        for stock_id, rows in sorted(rows_by_stock.items())
    }
    return {
        "mode": "strategy_buy_path_db_replay",
        "version": version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "read_only": True,
        "db_write": False,
        "schema_change": False,
        "live_telegram": False,
        "source": "Supabase daily_price read-only",
        "date_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "coverage": coverage,
        "totals": {
            "events": len(events),
            "stocks": len(coverage),
            "buyable_or_trend_days": len(buyable),
            "buy_like_days_including_prepare": len(buy_like),
            "snapshot_tradeable_days": len(snapshot_tradeable),
            "snapshot_tradeable_blocked_by_funnel_days": len(false_negative),
        },
        "state_counts": dict(state_counts.most_common()),
        "primary_blocker_counts": dict(blocker_counts.most_common()),
        "wait_retest_next_state": transition_after_state(events, "等回測"),
        "stock_summary": stock_summary,
        "first_buy_like_examples": buy_like[:30],
        "first_snapshot_tradeable_blocked_examples": false_negative[:30],
        "diagnosis": {
            "has_real_buyable_path": bool(buyable),
            "has_prepare_path": bool(buy_like),
            "funnel_blocks_snapshot_tradeable": bool(false_negative),
            "deadlock_suspected": len(events) > 0 and not buy_like,
        },
    }


def default_dates():
    end = datetime.now().date()
    while end.weekday() >= 5:
        end -= timedelta(days=1)
    return end - timedelta(days=DEFAULT_LOOKBACK_DAYS), end


def main():
    parser = argparse.ArgumentParser(description="Read-only DB replay audit for v21 buy-path gates.")
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--stock-id", action="append")
    parser.add_argument("--version", default=VERSION)
    parser.add_argument("--output")
    parser.add_argument("--lookback-days", type=int, default=DEFAULT_LOOKBACK_DAYS)
    args = parser.parse_args()

    default_start, default_end = default_dates()
    end_date = parse_date(args.end_date) if args.end_date else default_end
    start_date = parse_date(args.start_date) if args.start_date else end_date - timedelta(days=args.lookback_days)
    warmup_start = start_date - timedelta(days=WARMUP_DAYS)
    stock_ids = [str(item) for item in (args.stock_id or WATCHLIST_CODES)]

    client = _client()
    rows_by_stock = {
        stock_id: fetch_daily_price_rows(client, stock_id, warmup_start, end_date)
        for stock_id in stock_ids
    }
    rows_by_stock = {
        stock_id: rows
        for stock_id, rows in rows_by_stock.items()
        if rows
    }
    events = replay_from_daily_price(rows_by_stock, start_date, end_date, version=args.version)
    artifact = summarize(events, rows_by_stock, start_date, end_date, args.version)

    text = json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
