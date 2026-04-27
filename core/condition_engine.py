# ================================
# 🔥 condition_engine.py（FINAL v9.1｜對齊 v15）
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

    # 🔥 v15：改用 market_grade
    market_grade = result.get("market_grade")
    structure = result.get("structure_state")
    trend = result.get("trend")
    volume = result.get("volume_state")

    decision_type = result.get("decision_type")
    risk = result.get("risk")
    rr = result.get("rr")

    # ================================
    # 🔥 NO_TRADE（對齊）
    # ================================
    if decision == "NO_TRADE":

        if market_grade and market_grade != "D":
            conditions["market"] = True

        if trend == "UP":
            conditions["trend"] = True

        if volume and volume not in ["WEAK", "DISTRIBUTION"]:
            conditions["volume"] = True

        return conditions

    # ================================
    # 🔥 基礎映射（v15）
    # ================================
    if market_grade and market_grade in ["A", "B"]:
        conditions["market"] = True

    if structure in ["STRONG", "NORMAL"]:
        conditions["structure"] = True

    if trend == "UP":
        conditions["trend"] = True

    if volume and volume not in ["WEAK", "DISTRIBUTION"]:
        conditions["volume"] = True

    # ================================
    # 🔥 decision_type 對齊
    # ================================
    if decision_type in ["breakout", "pre_breakout", "add_on"]:
        conditions["event"] = True

    if decision_type == "pullback":
        conditions["event"] = True

    if decision_type == "early":
        conditions["edge"] = True

    # ================================
    # 🔥 風控（保留）
    # ================================
    if risk is not None and 0 < risk <= 0.08:
        conditions["risk"] = True

    # ================================
    # 🔥 RR（保留）
    # ================================
    if rr is not None:
        if decision_type in ["breakout", "pre_breakout", "add_on"] and rr >= 1.5:
            conditions["rr"] = True
        elif decision_type == "pullback" and rr >= 1.3:
            conditions["rr"] = True
        elif decision_type == "early":
            conditions["rr"] = True

    return conditions


# ================================
# 🔥 summarize（不動）
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