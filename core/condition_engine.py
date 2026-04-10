# ================================
# 🔥 condition_engine.py（v1乾淨版）
# ================================

"""
用途：
- 拆解 strategy 結果
- 提供顯示層使用

限制（v8）：
- 不可修改 decision
- 不可推論 decision
- 不可新增策略邏輯
- 只讀 strategy 輸出
"""


# ================================
# 🔥 條件引擎
# ================================
def condition_engine(result):

    market = result.get("market")
    trend = result.get("trend")
    volume = result.get("volume_state")

    structure = result.get("structure_state")
    momentum = result.get("momentum_state")

    decision_type = result.get("decision_type")

    breakout_quality = result.get("breakout_quality")
    pullback_type = result.get("pullback_type")

    risk = result.get("risk", 0)
    rr = result.get("rr", 0)

    conditions = {
        "market_ok": False,
        "structure_ok": False,
        "trend_ok": False,
        "volume_ok": False,
        "event_ok": False,
        "risk_ok": False,
        "rr_ok": False
    }

    # ===== 市場 =====
    if market is not None and market != "WEAK":
        conditions["market_ok"] = True

    # ===== 結構 =====
    if structure in ["STRONG", "NORMAL"]:
        conditions["structure_ok"] = True

    # ===== 趨勢 =====
    if trend == "UP":
        conditions["trend_ok"] = True

    # ===== 量能 =====
    if volume not in ["WEAK", "DISTRIBUTION"]:
        conditions["volume_ok"] = True

    # ===== 事件（不推論）=====
    if decision_type == "breakout" and breakout_quality is not None:
        conditions["event_ok"] = True

    elif decision_type == "pullback" and pullback_type is not None:
        conditions["event_ok"] = True

    # ===== 風控 =====
    if 0 < risk <= 0.08:
        conditions["risk_ok"] = True

    # ===== RR =====
    if decision_type == "breakout" and rr >= 1.8:
        conditions["rr_ok"] = True

    elif decision_type == "pullback" and rr >= 1.5:
        conditions["rr_ok"] = True

    return conditions


# ================================
# 🔥 顯示用（可選）
# ================================
def summarize_conditions(c):

    failed = []

    if not c["market_ok"]:
        failed.append("市場")

    if not c["structure_ok"]:
        failed.append("結構")

    if not c["trend_ok"]:
        failed.append("趨勢")

    if not c["volume_ok"]:
        failed.append("量能")

    if not c["event_ok"]:
        failed.append("事件")

    if not c["risk_ok"]:
        failed.append("風控")

    if not c["rr_ok"]:
        failed.append("報酬")

    return failed