from datetime import datetime
import json

import pytz
from supabase import create_client

from config import SUPABASE_URL, SUPABASE_KEY
from core.signal_snapshot import STRATEGY_FEATURE_FIELDS, strategy_feature_payload
from core.watchlist import WATCHLIST_CODES, missing_watchlist_codes


tz = pytz.timezone("Asia/Taipei")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
OUTCOME_HORIZONS = [1, 3, 5, 10]


def _num(value):
    try:
        if value in [None, "-"]:
            return None
        return float(value)
    except:
        return None


def _int(value):
    try:
        if value in [None, "-"]:
            return None
        return int(value)
    except:
        return None


def _json_safe(value):
    try:
        return json.loads(
            json.dumps(
                value,
                ensure_ascii=False,
                default=str
            )
        )
    except:
        return {}


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


def should_record_daily(phase, now=None):
    now = now or datetime.now(tz)

    if now.weekday() >= 5:
        return False

    after_close = (
        now.hour > 13
        or (
            now.hour == 13
            and now.minute >= 20
        )
    )

    # 中文註釋：v19.1.3 入庫必須是工作日 13:20 之後，避免早盤手動執行被「盤後」字樣誤寫成收盤樣本。
    return after_close and phase in ["收盤", "盤後"]


def _existing_run(run_date):
    res = supabase.table("signal_runs") \
        .select("id") \
        .eq("run_date", run_date) \
        .eq("run_phase", "daily_close") \
        .limit(1) \
        .execute()

    if res.data:
        return res.data[0]["id"]

    return None


def _holding_decision(data):
    result = data.get("result", {})
    return (
        data.get("holding_decision")
        or result.get("_holding_decision")
        or {}
    )


def _item_payload(run_id, name, data):
    result = data.get("result", {})
    holding = data.get("holding") or {}
    holding_decision = _holding_decision(data)

    strategy_features = strategy_feature_payload({
        **(result or {}),
        "volume_ratio_10": result.get("volume_ratio_10", data.get("volume_ratio")),
        "volume_ratio_20": result.get("volume_ratio_20"),
    })

    return {
        "run_id": run_id,
        "stock_name": name,
        "stock_code": data.get("stock_code"),
        "is_holding": bool(holding),
        "holding_shares": _int(holding.get("shares")),
        "avg_price": _num(holding.get("avg_price")),
        "price": _num(data.get("price")),
        "change_pct": _num(data.get("change")),
        "decision": result.get("decision"),
        "decision_type": result.get("decision_type"),
        "holding_action": holding_decision.get("action"),
        "holding_level": holding_decision.get("level"),
        "action_pct": _num(result.get("action")),
        "rr": _num(result.get("rr")),
        "structure_score": _int(data.get("structure_score")),
        "volume_ratio": _num(data.get("volume_ratio")),
        "strength": _num(result.get("strength")),
        "entry_quality": result.get("entry_quality"),
        "confidence_score": _num(result.get("confidence_score")),
        "market_grade": result.get("market_grade"),
        "trend": result.get("trend"),
        "volume_state": result.get("volume_state"),
        "structure_state": result.get("structure_state"),
        "structure_phase": result.get("structure_phase"),
        "price_behavior": result.get("price_behavior"),
        "heat_state": result.get("heat_state"),
        "trade_state": result.get("trade_state"),
        "breakout_distance": _num(result.get("breakout_distance")),
        **strategy_features,
        # 中文註釋：v19.1.3 raw_result 只存策略核心欄位，不保存完整 K 線，避免免費資料庫膨脹。
        "raw_result": _json_safe({
            "entry_stage": result.get("entry_stage"),
            "entry_profile": result.get("entry_profile"),
            "market_regime": result.get("market_regime"),
            "multi_day_bias": result.get("multi_day_bias"),
            "extended_level": result.get("extended_level"),
            "rank_score": result.get("rank_score"),
            "price_source": data.get("price_source"),
            **strategy_features,
        })
    }


def _legacy_item_payload(row):
    legacy = dict(row)
    for field in STRATEGY_FEATURE_FIELDS:
        legacy.pop(field, None)
    return legacy


def _insert_signal_items(item_payloads):
    try:
        supabase.table("signal_items").insert(item_payloads).execute()
        return {"signal_items_schema_fallback": False}
    except Exception as error:
        if not _is_missing_column_error(error):
            raise
        supabase.table("signal_items").insert(
            [_legacy_item_payload(row) for row in item_payloads]
        ).execute()
        return {
            "signal_items_schema_fallback": True,
            "signal_items_schema_fallback_reason": "signal_items_strategy_feature_columns_missing",
        }


def record_daily_signals(version, phase, message, results_map, best_stock, market_summary, now=None):
    now = now or datetime.now(tz)

    if not should_record_daily(phase, now):
        return {
            "recorded": False,
            "reason": "skip_phase"
        }

    missing = missing_watchlist_codes(results_map, WATCHLIST_CODES)

    if missing:
        return {
            "recorded": False,
            "reason": "incomplete_watchlist",
            "missing_stock_ids": missing
        }

    run_date = now.strftime("%Y-%m-%d")
    existing_id = _existing_run(run_date)

    if existing_id:
        # 中文註釋：v19.1.3 同一天收盤訊號只記一次，避免盤後重跑造成重複樣本。
        update_due_outcomes(results_map, now)
        return {
            "recorded": False,
            "reason": "already_recorded",
            "run_id": existing_id
        }

    run_payload = {
        "run_date": run_date,
        "run_phase": "daily_close",
        "version": version,
        "market_summary": market_summary,
        "best_stock": best_stock,
        "raw_message": message
    }

    run_res = supabase.table("signal_runs").insert(run_payload).execute()

    if not run_res.data:
        return {
            "recorded": False,
            "reason": "insert_run_failed"
        }

    run_id = run_res.data[0]["id"]
    item_payloads = [
        _item_payload(run_id, name, data)
        for name, data in results_map.items()
    ]

    item_write = {"signal_items_schema_fallback": False}
    if item_payloads:
        item_write = _insert_signal_items(item_payloads)

    update_due_outcomes(results_map, now)

    return {
        "recorded": True,
        "run_id": run_id,
        "items": len(item_payloads),
        **item_write,
    }


def _current_price_map(results_map):
    prices = {}

    for name, data in results_map.items():
        price = _num(data.get("price"))

        if price is not None:
            prices[name] = price

    return prices


def _existing_outcome_item_ids(horizon):
    res = supabase.table("signal_outcomes") \
        .select("item_id") \
        .eq("horizon_days", horizon) \
        .execute()

    return {
        row.get("item_id")
        for row in (res.data or [])
    }


def _due_items(horizon, today):
    cutoff = today.strftime("%Y-%m-%d")

    run_res = supabase.table("signal_runs") \
        .select("run_date") \
        .eq("run_phase", "daily_close") \
        .lte("run_date", cutoff) \
        .order("run_date") \
        .execute()

    trading_dates = [
        row.get("run_date")
        for row in (run_res.data or [])
        if row.get("run_date")
    ]

    if len(trading_dates) <= horizon:
        return []

    due_dates = set(trading_dates[:-horizon])

    res = supabase.table("signal_items") \
        .select("id,stock_name,price,signal_runs!inner(run_date)") \
        .in_("signal_runs.run_date", list(due_dates)) \
        .execute()

    items = []

    for row in res.data or []:
        run = row.get("signal_runs") or {}
        run_date = run.get("run_date")

        # 中文註釋：v19.1.3 outcome 以已入庫的收盤交易日序列計算，不用自然日避免週末污染 1/3/5/10 日結果。
        if run_date in due_dates:
            items.append(row)

    return items


def _outcome_label(change_pct):
    if change_pct is None:
        return None

    if change_pct >= 3:
        return "win"

    if change_pct <= -3:
        return "loss"

    return "flat"


def update_due_outcomes(results_map, now=None):
    now = now or datetime.now(tz)
    current_prices = _current_price_map(results_map)
    inserted = 0

    for horizon in OUTCOME_HORIZONS:
        existing_ids = _existing_outcome_item_ids(horizon)
        payloads = []

        for item in _due_items(horizon, now):
            item_id = item.get("id")

            if item_id in existing_ids:
                continue

            start_price = _num(item.get("price"))
            future_price = current_prices.get(item.get("stock_name"))

            if not start_price or future_price is None:
                continue

            change_pct = (future_price - start_price) / start_price * 100

            payloads.append({
                "item_id": item_id,
                "horizon_days": horizon,
                "future_price": future_price,
                "future_change_pct": round(change_pct, 4),
                "max_high_pct": None,
                "max_drawdown_pct": None,
                "outcome": _outcome_label(change_pct)
            })

        if payloads:
            supabase.table("signal_outcomes").insert(payloads).execute()
            inserted += len(payloads)

    return inserted
