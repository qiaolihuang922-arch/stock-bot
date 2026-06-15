from services.analysis import (
    BREAKOUT_THRESHOLD,
    pick_best_stock,
    resistance_levels,
    retest_zone_from_levels,
    strategy,
)
from core.condition_engine import condition_engine, summarize_conditions


def _avg(values):
    return sum(values) / len(values) if values else 0


def _safe_round(value, digits=2):
    try:
        if value is None:
            return None
        return round(float(value), digits)
    except:
        return None


def _volume_ratio(volumes):
    try:
        avg10 = _avg(volumes[-10:])
        if avg10 <= 0:
            return 1
        return round(volumes[-1] / avg10, 2)
    except:
        return 1


def _volume_ratio_window(volumes, window):
    try:
        sample = volumes[-window:]
        avg_volume = _avg(sample)
        if avg_volume <= 0:
            return 1
        return round(volumes[-1] / avg_volume, 2)
    except:
        return 1


def _breakout_distance(price, closes):
    try:
        resistance = max(closes[-20:-3])
        breakout_price = resistance * (1 + BREAKOUT_THRESHOLD)
        return round((breakout_price - price) / price * 100, 2)
    except:
        return None


def _breakout_context(price, closes):
    try:
        levels = resistance_levels(closes)
        retest = retest_zone_from_levels(levels)
        breakout_20 = levels.get("breakout_price_20")
        breakout_60 = levels.get("breakout_price_60")
        return {
            **levels,
            **retest,
            "breakout_distance_20": round((breakout_20 - price) / price * 100, 2) if price and breakout_20 else None,
            "breakout_distance_60": round((breakout_60 - price) / price * 100, 2) if price and breakout_60 else None,
        }
    except:
        return {}


def _position_state(distance):
    if distance is None:
        return "UNKNOWN"
    if distance < 0:
        return "BREAKOUT"
    if distance < 1:
        return "NEAR_BREAKOUT"
    if distance < 4:
        return "WATCH_BREAKOUT"
    return "FAR"


def _reason_labels(result):
    conditions = condition_engine(result)
    decision = result.get("decision")
    items = summarize_conditions(conditions, decision)
    behavior = result.get("price_behavior")

    labels = []
    for item in items:
        if decision == "BUY":
            positive = {
                "market": "市場成立",
                "structure": "結構成立",
                "trend": "趨勢成立",
                "volume": "量能成立",
                "event": "事件成立",
                "edge": "Edge成立",
                "risk": "風控成立",
                "rr": "RR足夠"
            }
            labels.append(positive.get(item, item))
        elif item == "market":
            labels.append("市場弱" if result.get("market_grade") == "D" else "市場未強")
        elif item == "trend":
            labels.append("趨勢未轉強")
        elif item == "volume":
            labels.append("量能不足")
        elif item == "risk":
            labels.append("風控不足")
        elif item == "rr":
            labels.append("RR不足")
        elif item == "structure":
            labels.append("結構不足")
        elif item == "event":
            labels.append("事件不足")
        elif item == "edge":
            labels.append("Edge不足")
        else:
            labels.append(item)

    decision_type = result.get("decision_type")
    if decision_type == "watch_quality_c":
        labels = []
        if result.get("rr", 0) >= 1:
            labels.append("RR足夠")
        if result.get("volume_state") == "WEAK":
            labels.append("低量觀察")
        if result.get("heat_state") == "HOT":
            labels.append("過熱觀察")

    if result.get("heat_state") == "EXTREME":
        labels = ["過熱 Lv.3", "不追高"]

    if behavior == "LIMIT_LOCK" and decision != "BUY" and result.get("heat_state") != "EXTREME":
        labels = ["漲停鎖價", "不追高"]

    if behavior == "LIMIT_REBOUND" and decision != "BUY" and result.get("heat_state") != "EXTREME":
        labels = ["漲停反彈", "隔日確認"]

    if behavior == "WEAK_REBOUND" and decision != "BUY" and result.get("heat_state") != "EXTREME":
        labels = ["弱勢反彈", "隔日確認"]

    if (
        result.get("breakout_state") == "FAIL"
        or result.get("structure_phase") == "FAILED_BREAKOUT"
    ):
        labels.insert(0, "突破失敗")

    if result.get("trade_state") == "NO_VOLUME" and "量能不足" not in labels:
        labels.append("量能不足")

    if result.get("trade_state") == "LATE_ENTRY" and "RR不足" not in labels:
        labels.append("RR不足")

    # 中文註釋：v19.1.3 snapshot reasons 只保留去重後的策略原因，供 dry-run 與 unit test 驗證。
    return list(dict.fromkeys(labels))


def is_tradeable_result(result):
    if result.get("decision") != "BUY":
        return False
    if result.get("action", 0) <= 0:
        return False
    if result.get("entry_quality") in ["C", "D"]:
        return False
    if result.get("heat_state") in ["HOT", "EXTREME"]:
        return False
    if result.get("price_behavior") in ["LIMIT_LOCK", "LIMIT_REBOUND", "WEAK_REBOUND"]:
        return False
    if result.get("structure_phase") == "SHAKEOUT":
        return False
    if result.get("trade_state") in ["AVOID", "NO_VOLUME", "LATE_ENTRY"]:
        return False
    if result.get("market_grade") == "D":
        return False
    if result.get("rr", 0) < 1:
        return False
    return True


def analyze_ohlcv_snapshot(
    stock_id,
    trade_date,
    closes,
    volumes,
    version="v19.3",
    ohlcv_bars=None,
    trend_continuation_evidence=None,
):
    if not closes or not volumes:
        raise ValueError("closes and volumes are required")

    close = closes[-1]
    previous = closes[-2] if len(closes) >= 2 and closes[-2] else close
    change = (close - previous) / previous * 100 if previous else 0
    ma5 = _avg(closes[-5:])
    ma20 = _avg(closes[-20:])

    result = strategy(
        close,
        change,
        ma5,
        ma20,
        closes,
        volumes,
        ohlcv_bars=ohlcv_bars,
        trend_continuation_evidence=trend_continuation_evidence,
        stock_id=stock_id,
    )
    distance = _breakout_distance(close, closes)
    result["breakout_distance"] = distance
    context = _breakout_context(close, closes)
    for key, value in context.items():
        if value is not None:
            result[key] = value
    reasons = _reason_labels(result)
    is_tradeable = is_tradeable_result(result)
    volume_ratio_10 = _volume_ratio(volumes)
    volume_ratio_20 = _volume_ratio_window(volumes, 20)

    return {
        "stock_id": stock_id,
        "trade_date": trade_date,
        "version": version,
        "close": _safe_round(close),
        "volume_ratio": volume_ratio_10,
        "volume_ratio_10": volume_ratio_10,
        "volume_ratio_20": volume_ratio_20,
        "pattern": result.get("structure_phase"),
        "market_state": result.get("market_grade"),
        "structure_state": result.get("structure_state"),
        "position_state": _position_state(distance),
        "rr": _safe_round(result.get("rr")),
        "score": _safe_round(result.get("strength")),
        "heat_level": result.get("extended_level", 0),
        "action": result.get("decision"),
        "reasons": reasons,
        "is_tradeable": is_tradeable,
        "is_best_candidate": False,
        "raw_result": result
    }


def snapshot_from_result(stock_id, trade_date, version, result, close, volume_ratio, position_state=None):
    reasons = _reason_labels(result)
    is_tradeable = is_tradeable_result(result)

    # 中文註釋：v19.1.3 每日正式寫入與 backfill 共用同一個 snapshot 格式，避免兩套口徑分裂。
    return {
        "stock_id": stock_id,
        "trade_date": trade_date,
        "version": version,
        "close": _safe_round(close),
        "volume_ratio": _safe_round(volume_ratio),
        "volume_ratio_10": _safe_round(result.get("volume_ratio_10", volume_ratio)),
        "volume_ratio_20": _safe_round(result.get("volume_ratio_20")),
        "pattern": result.get("structure_phase"),
        "market_state": result.get("market_grade"),
        "structure_state": result.get("structure_state"),
        "position_state": position_state or _position_state(result.get("breakout_distance")),
        "rr": _safe_round(result.get("rr")),
        "score": _safe_round(result.get("strength")),
        "heat_level": result.get("extended_level", 0),
        "action": result.get("decision"),
        "reasons": reasons,
        "is_tradeable": is_tradeable,
        "is_best_candidate": False,
        "raw_result": result
    }


def mark_best_candidate(snapshots):
    for item in snapshots:
        item["is_best_candidate"] = False

    candidates = {
        item["stock_id"]: item["raw_result"]
        for item in snapshots
        if is_tradeable_result(item["raw_result"])
    }
    best, _ = pick_best_stock(candidates)

    for item in snapshots:
        item["is_best_candidate"] = item["stock_id"] == best

    return snapshots


def apply_snapshot_boundaries(snapshots, holding_stock_ids=None):
    holding_stock_ids = set(holding_stock_ids or [])

    for item in snapshots:
        if item.get("stock_id") in holding_stock_ids:
            item["is_tradeable"] = False
            item["is_best_candidate"] = False

    mark_best_candidate([
        item for item in snapshots
        if item.get("stock_id") not in holding_stock_ids
    ])

    return snapshots
