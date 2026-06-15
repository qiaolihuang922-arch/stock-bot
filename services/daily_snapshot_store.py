from datetime import datetime

try:
    import pytz
except ImportError:
    pytz = None

from core.signal_snapshot import (
    STRATEGY_FEATURE_FIELDS,
    apply_snapshot_boundaries,
    snapshot_from_result,
)
from core.signal_validator import validate_snapshots
from core.watchlist import WATCHLIST_CODES, missing_watchlist_codes


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

    # 中文註釋：v19.1.3 每日快照與 signal_store 採同一收盤後入庫規則，但避免匯入 DB client 造成測試污染。
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
        "is_best_candidate": snapshot["is_best_candidate"],
        "raw_result": snapshot.get("raw_result") or {},
        **{
            field: snapshot.get(field)
            for field in STRATEGY_FEATURE_FIELDS
            if field in snapshot
        },
    }


def _legacy_signal_payload(row):
    legacy = dict(row)
    legacy.pop("raw_result", None)
    for field in STRATEGY_FEATURE_FIELDS:
        legacy.pop(field, None)
    return legacy


def _is_missing_column_error(error):
    text = str(error).lower()
    return (
        "column" in text
        and (
            "could not find" in text
            or "does not exist" in text
            or "schema cache" in text
        )
    )


def _upsert_daily_signal_snapshot(client, signal_rows):
    try:
        client.table("daily_signal_snapshot").upsert(
            signal_rows,
            on_conflict="stock_id,trade_date,version"
        ).execute()
        return {"schema_fallback": False}
    except Exception as error:
        if not _is_missing_column_error(error):
            raise
        client.table("daily_signal_snapshot").upsert(
            [_legacy_signal_payload(row) for row in signal_rows],
            on_conflict="stock_id,trade_date,version"
        ).execute()
        return {
            "schema_fallback": True,
            "reason": "daily_signal_snapshot_strategy_feature_columns_missing",
        }


def build_daily_snapshot_payloads(version, phase, results_map, now=None, expected_stock_ids=None):
    now = now or (datetime.now(tz) if tz else datetime.now())

    if not should_record_daily_snapshot(phase, now):
        return {
            "recorded": False,
            "reason": "skip_phase",
            "price_rows": [],
            "signal_rows": []
        }

    expected_stock_ids = expected_stock_ids or WATCHLIST_CODES
    missing = missing_watchlist_codes(results_map, expected_stock_ids)

    if missing:
        return {
            "recorded": False,
            "reason": "incomplete_watchlist",
            "missing_stock_ids": missing,
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

    errors = validate_snapshots(snapshots, expected_stock_ids=[str(item) for item in expected_stock_ids])

    if errors:
        return {
            "recorded": False,
            "reason": "validation_failed",
            "errors": errors,
            "price_rows": price_rows,
            "signal_rows": [_signal_payload(item) for item in snapshots]
        }

    # 中文註釋：v19.1.3 每日 snapshot 寫入前先建 payload 並驗證；daily_price 沒有完整 OHLCV 時不寫。
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
        now,
        expected_stock_ids=WATCHLIST_CODES
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

    signal_write = {"schema_fallback": False}
    if signal_rows:
        signal_write = _upsert_daily_signal_snapshot(client, signal_rows)

    return {
        "recorded": True,
        "price_rows": len(price_rows),
        "signal_rows": len(signal_rows),
        **signal_write,
    }


def read_daily_signal_snapshot_status(client, trade_date, version, expected_stock_ids=None):
    expected = {str(item) for item in (expected_stock_ids or WATCHLIST_CODES)}
    result = (
        client.table("daily_signal_snapshot")
        .select("stock_id,trade_date,version")
        .eq("trade_date", trade_date)
        .eq("version", version)
        .execute()
    )
    rows = result.data or []
    seen = {
        str(row.get("stock_id"))
        for row in rows
        if isinstance(row, dict)
    }
    missing = sorted(expected - seen)
    return {
        "source": "daily_signal_snapshot",
        "trade_date": trade_date,
        "version": version,
        "row_count": len(rows),
        "expected_rows": len(expected),
        "read_after_write": "ok" if not missing and len(rows) >= len(expected) else "fail",
        "missing_stock_ids": missing,
    }
