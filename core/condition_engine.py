# ================================
# 🔥 condition_engine.py（FINAL v9.0｜對齊策略版）
# ================================

def condition_engine(result):

    conditions = {
        "market": False,
        "structure": False,
        "trend": False,
        "volume": False,
        "event": False,
        "edge": False,
        "risk": False,
        "rr": False
    }

    decision = result.get("decision")

    # ================================
    # 🔥 NO_TRADE（保留）
    # ================================
    if decision == "NO_TRADE":

        market = result.get("market_signal")
        trend = result.get("trend")
        volume = result.get("volume_state")

        if market and market != "WEAK":
            conditions["market"] = True

        if trend == "UP":
            conditions["trend"] = True

        if volume and volume not in ["WEAK", "DISTRIBUTION"]:
            conditions["volume"] = True

        return conditions

    # ================================
    # 🔥 基礎映射（保留）
    # ================================
    market = result.get("market_signal")
    structure = result.get("structure_state")
    trend = result.get("trend")
    volume = result.get("volume_state")

    decision_type = result.get("decision_type")
    risk = result.get("risk")
    rr = result.get("rr")

    if market and market != "WEAK":
        conditions["market"] = True

    if structure in ["STRONG", "NORMAL"]:
        conditions["structure"] = True

    if trend == "UP":
        conditions["trend"] = True

    if volume and volume not in ["WEAK", "DISTRIBUTION"]:
        conditions["volume"] = True

    # ================================
    # 🔥 修正 1：支援新 decision_type
    # ================================
    # breakout / pullback / early / pre_breakout 都納入

    if decision_type in ["breakout", "pre_breakout"]:
        conditions["event"] = True

    if decision_type in ["pullback"]:
        conditions["event"] = True

    if decision_type in ["early"]:
        conditions["edge"] = True

    # ================================
    # 🔥 修正 2：風控（對齊策略）
    # ================================
    if risk is not None and 0 < risk <= 0.08:
        conditions["risk"] = True

    # ================================
    # 🔥 修正 3：RR 對齊 strategy
    # ================================
    if rr is not None:
        if decision_type in ["breakout", "pre_breakout"] and rr >= 1.5:
            conditions["rr"] = True
        elif decision_type == "pullback" and rr >= 1.3:
            conditions["rr"] = True
        elif decision_type == "early":
            conditions["rr"] = True  # 🔥 early 不再限制

    return conditions


# ================================
# 🔥 summarize（保留）
# ================================
def summarize_conditions(c, decision):

    if decision == "BUY":
        return [k for k, v in c.items() if v]

    elif decision == "WAIT":
        return [k for k, v in c.items() if not v]

    elif decision == "NO_TRADE":
        priority = ["market", "trend", "volume"]
        return [k for k in priority if not c.get(k)]

    return []