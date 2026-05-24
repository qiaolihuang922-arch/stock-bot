# ================================
# condition_engine.py（v19.0｜WATCH 條件映射層）
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

    # 🔥 v19.0：只映射 analysis.py 的結果，不反推 decision
    market_grade = result.get("market_grade")
    structure = result.get("structure_state")
    trend = result.get("trend")
    volume = result.get("volume_state")

    decision_type = result.get("decision_type")
    risk = result.get("risk")
    rr = result.get("rr")
    heat_state = result.get("heat_state")
    price_behavior = result.get("price_behavior")
    structure_phase = result.get("structure_phase")
    entry_quality = result.get("entry_quality")
    entry_profile = result.get("entry_profile")

    if price_behavior in ["LIMIT_LOCK", "LIMIT_REBOUND"]:
        # 中文註釋：v19.0 漲停鎖價 / 漲停反彈是已辨識價格行為，不再顯示事件與 Edge 全缺。
        conditions["event"] = True
        conditions["edge"] = True

    if structure_phase in ["SHAKEOUT", "HEALTHY_PULLBACK"]:
        # 中文註釋：v19.0 洗盤 / 健康回踩屬於持倉觀察條件，量能弱不直接視為交易錯誤。
        conditions["event"] = True
        conditions["edge"] = True

    if entry_quality in ["A+", "A", "B"]:
        # 中文註釋：v19.0 入場品質達 B 以上代表證據鏈已成形，條件映射不再只看單一 RR。
        conditions["edge"] = True

    if entry_profile in [
        "WAIT_LIMIT_REBOUND",
        "WAIT_WEAK_REBOUND",
        "WAIT_DISTANCE"
    ]:
        conditions["risk"] = False

    if decision_type == "watch_quality_c":
        # 中文註釋：v19.0 C 品質觀察是已辨識的策略狀態，RR 足夠時不再顯示 RR 不足。
        return {
            **conditions,
            "market": bool(market_grade and market_grade != "D"),
            "structure": structure in ["STRONG", "NORMAL"],
            "trend": trend == "UP",
            "volume": bool(volume and volume not in ["WEAK", "DISTRIBUTION"]),
            "event": True,
            "edge": True,
            "risk": bool(risk is not None and 0 < risk <= 0.08),
            "rr": bool(rr is not None and rr >= 1.0)
        }

    if heat_state == "EXTREME":
        # 中文註釋：v19.0 禁追由過熱主導，不再把風控 / RR 顯示成主要缺口。
        return {
            **conditions,
            "market": bool(market_grade and market_grade != "D"),
            "structure": structure in ["STRONG", "NORMAL"],
            "trend": trend == "UP",
            "volume": bool(volume and volume not in ["WEAK", "DISTRIBUTION"]),
            "event": True,
            "edge": True,
            "risk": True,
            "rr": True
        }

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
    # 🔥 基礎映射（v19.0）
    # ================================
    if market_grade and market_grade in ["A+", "A", "B"]:
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
    if decision_type in [
        "breakout",
        "pre_breakout",
        "strong_follow",
        "wait_breakout_low_rr",
        "wait_breakout_confirm",
        "wait_pre_breakout_low_rr",
        "wait_pre_breakout",
        "add_on"
    ]:
        conditions["event"] = True
        conditions["edge"] = True

    if decision_type in [
        "fake_breakout",
        "extended"
    ]:
        # 中文註釋：v19.0 假突破 / 過熱屬於已辨識事件，不再顯示事件與 Edge 全缺。
        conditions["event"] = True
        conditions["edge"] = True

    if decision_type == "pullback":
        conditions["event"] = True
        conditions["edge"] = True

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
        if decision_type in [
            "breakout",
            "strong_follow",
            "wait_breakout_low_rr",
            "add_on"
        ] and rr >= 1.5:
            conditions["rr"] = True
        elif decision_type in [
            "pre_breakout",
            "wait_pre_breakout_low_rr"
        ] and rr >= 1.0:
            conditions["rr"] = True
        elif decision_type == "pullback" and rr >= 1.3:
            conditions["rr"] = True
        elif decision_type == "early":
            conditions["rr"] = True

    if rr is not None and rr >= 1.0:
        # 中文註釋：v19.0 RR 數值已足夠時，不再因 WAIT 類型未命中特定分支而顯示 RR 不足。
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
