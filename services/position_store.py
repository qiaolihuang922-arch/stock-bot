from datetime import datetime

import pytz
from supabase import create_client

import config
from core.watchlist import STOCKS

tz = pytz.timezone("Asia/Taipei")


CODE_TO_NAME = {
    code: name
    for name, code in STOCKS.items()
}


def _fallback_positions():
    return {
        name: {
            "shares": 0,
            "avg_price": 0,
            "realized_profit_taken_ratio": 0,
            "realized_profit_taken_date": None
        }
        for name in STOCKS
    }


def _client():
    supabase_url = getattr(config, "SUPABASE_URL", "")
    supabase_key = (
        getattr(config, "SUPABASE_SERVICE_ROLE_KEY", "")
        or getattr(config, "SUPABASE_KEY", "")
    )

    if not supabase_url or not supabase_key:
        return None

    return create_client(supabase_url, supabase_key)


def load_positions():
    client = _client()

    if not client:
        return _fallback_positions()

    try:
        res = client.table("positions") \
            .select("stock_code,stock_name,shares,avg_price,realized_profit_taken_ratio,last_realized_profit_date,status") \
            .execute()
    except Exception as exc:
        print(f"⚠ 持倉DB讀取失敗，使用本地fallback：{exc}")
        return _fallback_positions()

    positions = _fallback_positions()

    for row in res.data or []:
        code = row.get("stock_code")
        name = row.get("stock_name") or CODE_TO_NAME.get(code)

        if not name:
            continue

        positions[name] = {
            "shares": int(row.get("shares") or 0),
            "avg_price": float(row.get("avg_price") or 0),
            "realized_profit_taken_ratio": float(row.get("realized_profit_taken_ratio") or 0),
            "realized_profit_taken_date": row.get("last_realized_profit_date")
        }

    return positions


def _empty_event_summary():
    return {
        name: {
            "bought_shares": 0,
            "sold_shares": 0,
            "net_shares": 0,
            "sell_pct": 0,
            "event_count": 0,
            "labels": []
        }
        for name in STOCKS
    }


def load_today_position_events():
    client = _client()

    if not client:
        return _empty_event_summary()

    event_date = datetime.now(tz).date().isoformat()

    try:
        res = client.table("position_events") \
            .select("stock_code,stock_name,event_date,action_label,shares_delta,shares_before,shares_after,created_at") \
            .eq("event_date", event_date) \
            .order("created_at") \
            .execute()
    except Exception as exc:
        print(f"⚠ 今日持倉事件讀取失敗，略過執行統計：{exc}")
        return _empty_event_summary()

    summary = _empty_event_summary()
    first_before = {}

    for row in res.data or []:
        code = row.get("stock_code")
        name = row.get("stock_name") or CODE_TO_NAME.get(code)

        if not name or name not in summary:
            continue

        shares_delta = int(row.get("shares_delta") or 0)
        shares_before = int(row.get("shares_before") or 0)
        item = summary[name]

        if name not in first_before:
            first_before[name] = shares_before

        if shares_delta > 0:
            item["bought_shares"] += shares_delta
        elif shares_delta < 0:
            item["sold_shares"] += abs(shares_delta)

        item["net_shares"] += shares_delta
        item["event_count"] += 1

        label = row.get("action_label")
        if label and label not in item["labels"]:
            item["labels"].append(label)

    for name, item in summary.items():
        base = first_before.get(name, 0)
        if base > 0 and item["sold_shares"] > 0:
            item["sell_pct"] = round(item["sold_shares"] / base * 100)

    return summary
