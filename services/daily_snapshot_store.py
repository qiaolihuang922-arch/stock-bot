from datetime import datetime

try:
    import pytz
except ImportError:
    pytz = None

from core.signal_snapshot import apply_snapshot_boundaries, snapshot_from_result
from core.signal_validator import validate_snapshots


tz = pytz.timezone("Asia/Taipei") if pytz else None


def should_record_daily_snapshot(phase, now=None):
    now = now or (datetime.now(tz) if tz else datetime.now())

    if now.weekday() >= 5:
        return False

    after_close = (
        now.hour > 13
        or (
            now.hour == 13
            and now.minute >= 20
        )
    )

    # 中文註釋：v19.0 每日快照與 signal_store 採同一收盤後入庫規則，但避免匯入 DB client 造成測試污染。
    return after_close and phase in ["收盤", "盤後"]


def _num(value):
    try:
        if value in [None, "-"]:
            return None
        return float(value)
    except:
        return None


def _date_text(now):
    return now.strftime("%Y-%m-%d")


def _price_payload(stock_id, trade_date, data):
    ohlcv = data.get("ohlcv") or {}
    required = ["open", "high", "low", "close", "volume"]

    if not all(_num(ohlcv.get(field)) is not None for field in required):
        return None

    # 中文註釋：daily_price 只接受完整 OHLCV，避免每日報文用即時價污染回測價格表。
    return {
        "stock_id": stock_id,
        "trade_date": trade_date,
        "open": _num(ohlcv.get("open")),
        "high": _num(ohlcv.get("high")),
        "low": _num(ohlcv.get("low")),
        "close": _num(ohlcv.get("close")),
        "volume": _num(ohlcv.get("volume")),
        "source": ohlcv.get("source", "daily_close")
    }


def _signal_payload(snapshot):
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


def build_daily_snapshot_payloads(version, phase, results_map, now=None):
    now = now or (datetime.now(tz) if tz else datetime.now())

    if not should_record_daily_snapshot(phase, now):
        return {
            "recorded": False,
            "reason": "skip_phase",
            "price_rows": [],
            "signal_rows": []
        }

    trade_date = _date_text(now)
    snapshots = []
    price_rows = []

    for name, data in results_map.items():
        stock_id = data.get("stock_code")
        result = data.get("result") or {}

        if not stock_id:
            continue

        snapshots.append(
            snapshot_from_result(
                stock_id,
                trade_date,
                version,
                result,
                data.get("price"),
                data.get("volume_ratio")
            )
        )
        price_payload = _price_payload(
            stock_id,
            trade_date,
            data
        )
        if price_payload:
            price_rows.append(price_payload)

    holding_stock_ids = {
        data.get("stock_code")
        for data in results_map.values()
        if data.get("holding")
    }

    # 中文註釋：持倉股只代表持倉管理，不可污染新進場 tradeable / 勝率統計。
    apply_snapshot_boundaries(snapshots, holding_stock_ids)

    errors = validate_snapshots(snapshots)

    if errors:
        return {
            "recorded": False,
            "reason": "validation_failed",
            "errors": errors,
            "price_rows": price_rows,
            "signal_rows": [_signal_payload(item) for item in snapshots]
        }

    # 中文註釋：v19.0 每日 snapshot 寫入前先建 payload 並驗證；daily_price 沒有完整 OHLCV 時不寫。
    return {
        "recorded": True,
        "reason": "ready",
        "price_rows": price_rows,
        "signal_rows": [_signal_payload(item) for item in snapshots]
    }


def get_supabase_client():
    from supabase import create_client
    from config import SUPABASE_KEY, SUPABASE_URL

    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY are required")

    return create_client(SUPABASE_URL, SUPABASE_KEY)


def record_daily_snapshots(version, phase, results_map, now=None):
    payloads = build_daily_snapshot_payloads(
        version,
        phase,
        results_map,
        now
    )

    if not payloads.get("recorded"):
        return payloads

    client = get_supabase_client()
    price_rows = payloads["price_rows"]
    signal_rows = payloads["signal_rows"]

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

    return {
        "recorded": True,
        "price_rows": len(price_rows),
        "signal_rows": len(signal_rows)
    }
