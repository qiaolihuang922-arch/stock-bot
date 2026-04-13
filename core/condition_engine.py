# ================================
# 🔥 condition_engine.py（FINAL v8.6）
# ================================

"""
用途：
- 拆解 strategy 結果
- 僅做條件映射（不可推論）

嚴格遵守：
- 不改 decision
- 不推論 decision
- 不新增策略
- 所有條件來源必須來自 analysis
"""


# ================================
# 🔥 條件引擎（唯一入口）
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
    # 🔥 NO_TRADE（關鍵修正：避免誤導）
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
    # 🔥 正常流程
    # ================================
    market = result.get("market_signal")
    structure = result.get("structure_state")
    trend = result.get("trend")
    volume = result.get("volume_state")

    event_breakout = result.get("event_breakout")
    event_pullback = result.get("event_pullback")

    edge_consolidation = result.get("edge_consolidation")
    edge_fake_breakout = result.get("edge_fake_breakout")
    edge_first_pullback = result.get("edge_first_pullback")
    edge_ma20_trend = result.get("edge_ma20_trend")

    risk = result.get("risk")
    rr = result.get("rr")
    decision_type = result.get("decision_type")

    # ================================
    # 🔥 條件判斷（只映射）
    # ================================

    # ===== 市場 =====
    if market and market != "WEAK":
        conditions["market"] = True

    # ===== 結構 =====
    if structure in ["STRONG", "NORMAL"]:
        conditions["structure"] = True

    # ===== 趨勢 =====
    if trend == "UP":
        conditions["trend"] = True

    # ===== 量能 =====
    if volume and volume not in ["WEAK", "DISTRIBUTION"]:
        conditions["volume"] = True

    # ================================
    # 🔥 decision_type 防呆（關鍵）
    # ================================
    if decision_type not in ["breakout", "pullback"]:
        return conditions

    # ===== 事件 =====
    if decision_type == "breakout":
        if event_breakout:
            conditions["event"] = True

    elif decision_type == "pullback":
        if event_pullback:
            conditions["event"] = True

    # ===== Edge =====
    if decision_type == "breakout":
        if (
            edge_consolidation is True and
            edge_fake_breakout is False
        ):
            conditions["edge"] = True

    elif decision_type == "pullback":
        if (
            edge_first_pullback is True and
            edge_ma20_trend is True
        ):
            conditions["edge"] = True

    # ===== 風控 =====
    if risk is not None and 0 < risk <= 0.08:
        conditions["risk"] = True

    # ===== RR =====
    if rr is not None:
        if decision_type == "breakout" and rr >= 1.8:
            conditions["rr"] = True
        elif decision_type == "pullback" and rr >= 1.5:
            conditions["rr"] = True

    return conditions


# ================================
# 🔥 顯示用（完全對齊 v8.6）
# ================================
def summarize_conditions(c, decision):

    # ===== BUY：顯示成立條件 =====
    if decision == "BUY":
        return [k for k, v in c.items() if v]

    # ===== WAIT：顯示缺少條件 =====
    elif decision == "WAIT":
        return [k for k, v in c.items() if not v]

    # ===== NO_TRADE：只顯示致命 =====
    elif decision == "NO_TRADE":
        priority = ["market", "trend", "volume"]
        return [k for k in priority if not c.get(k)]

    return []