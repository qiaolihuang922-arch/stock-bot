from supabase import create_client

import config
from core.watchlist import STOCKS


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
