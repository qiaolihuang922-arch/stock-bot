# ================================
# 🔥 condition_engine.py（FINAL v8.5+）
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

    # ===== 直接讀取 analysis 結果 =====
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
    # 🔥 條件判斷（只映射，不推論）
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

    # ===== 量能（修正 None 問題）=====
    if volume and volume not in ["WEAK", "DISTRIBUTION"]:
        conditions["volume"] = True

    # ================================
    # 🔥 decision_type 防呆（關鍵修正）
    # ================================
    if decision_type not in ["breakout", "pullback"]:
        return conditions

    # ===== 事件（嚴格來自 analysis）=====
    if decision_type == "breakout":
        if event_breakout:
            conditions["event"] = True

    elif decision_type == "pullback":
        if event_pullback:
            conditions["event"] = True

    # ===== Edge（不得簡化）=====
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
# 🔥 顯示用（符合 v8）
# ================================
def summarize_conditions(c, decision):

    # ===== BUY：顯示成立條件 =====
    if decision == "BUY":
        return [k for k, v in c.items() if v]

    # ===== WAIT：顯示缺少條件 =====
    elif decision == "WAIT":
        return [k for k, v in c.items() if not v]

    # ===== NO_TRADE：只顯示致命條件 =====
    elif decision == "NO_TRADE":
        priority = ["market", "trend", "volume"]
        return [k for k in priority if not c.get(k)]

    return []