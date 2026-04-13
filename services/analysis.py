# ================================
# 🔥 analysis.py（FINAL v9.8｜觸發優化版）
# ================================

# ===== 工具 =====
def avg(arr):
    return sum(arr) / len(arr) if arr else 0


# ================================
# 🔥 行動引擎（核心）
# ================================
def action_mapper(decision, position):

    if decision == "BUY":
        return {
            "action": round(position, 2),
            "action_type": "BUY"
        }

    if decision == "NO_TRADE":
        return {
            "action": -1.0,
            "action_type": "SELL_ALL"
        }

    return {
        "action": 0.0,
        "action_type": "HOLD"
    }


# ================================
# 🔥 🔥 強度分數（保留）
# ================================
def strength_score(result):

    score = 0

    if result.get("decision") == "BUY":
        score += 5
    elif result.get("decision") == "WAIT":
        score += 2

    m = result.get("market_score") or 0
    score += m * 0.5

    rr = result.get("rr") or 0
    score += rr

    if result.get("trend") == "UP":
        score += 1

    if result.get("structure_state") == "STRONG":
        score += 1

    if result.get("volume_state") == "STRONG":
        score += 1

    return round(score, 2)


# ================================
# 🔥 市場強度（保留）
# ================================
def market_score(market, trend, structure, volume, momentum):

    score = 0

    if market == "STRONG":
        score += 2
    elif market == "CHOPPY":
        score += 1
    elif market == "WEAK":
        score -= 2

    if trend == "UP":
        score += 2
    elif trend == "DOWN":
        score -= 2

    if structure == "STRONG":
        score += 2
    elif structure == "WEAK":
        score -= 1

    if volume == "STRONG":
        score += 2
    elif volume == "DISTRIBUTION":
        score -= 2

    if momentum == "ACCELERATING":
        score += 1
    else:
        score -= 0.5

    return score


def market_grade(score):
    if score >= 6:
        return "A"
    elif score >= 3:
        return "B"
    elif score >= 0:
        return "C"
    return "D"


# ================================
# 🔥 統一輸出（保留）
# ================================
def build_result(**kwargs):

    decision = kwargs.get("decision", "WAIT")
    position = kwargs.get("position", 0)

    action_data = action_mapper(decision, position)

    risk = kwargs.get("risk", 0)
    rr = kwargs.get("rr", 0)

    if decision == "NO_TRADE":
        risk = 0
        rr = 0
        position = 0

    result = {
        "decision": decision,
        "decision_type": kwargs.get("decision_type", "none"),

        "buy": kwargs.get("buy"),
        "stop": kwargs.get("stop"),

        "position": round(position, 2),

        "action": action_data["action"],
        "action_type": action_data["action_type"],

        "risk": round(risk, 4),
        "rr": round(rr, 2),

        "market_signal": kwargs.get("market_signal"),
        "trend": kwargs.get("trend"),
        "structure_state": kwargs.get("structure_state"),
        "volume_state": kwargs.get("volume_state"),

        "market_score": kwargs.get("market_score"),
        "market_grade": kwargs.get("market_grade"),
    }

    result["strength"] = strength_score(result)

    return result


# ================================
# 🔥 訊號層（微調）
# ================================
def support_resistance(closes):
    # 🔥 修改：避免抓到「最新高點」→ 更容易觸發突破
    return min(closes[-20:]), max(closes[-20:-3])  # ← 修改


def event_breakout(price, closes, resistance, volumes):
    avg5 = avg(volumes[-5:])
    near = closes[-1] > resistance * 0.99
    return near and volumes[-1] > avg5 * 1.2


def event_pullback(price, ma5, closes):
    near = abs(price - ma5) / ma5 < 0.03
    rebound = closes[-1] > closes[-2]
    return near and rebound


def edge_consolidation(closes):
    return (max(closes[-5:]) - min(closes[-5:])) / closes[-1] < 0.04


def edge_fake_breakout(closes):
    prev_high = max(closes[-21:-1])
    return closes[-2] > prev_high and closes[-1] < prev_high


def edge_first_pullback(closes, ma20):
    return closes[-2] > ma20 and closes[-3] > ma20


# ================================
# 🔥 風控（微調）
# ================================
def risk_control(buy, stop, resistance, mode):

    if stop >= buy:
        return False, 0, 0

    risk = (buy - stop) / buy
    if risk > 0.08:
        return False, risk, 0

    target = buy + (buy - stop) * 2 if mode == "breakout" else resistance
    rr = (target - buy) / (buy - stop) if (buy - stop) else 0

    # 🔥 修改：放寬 RR
    if mode == "breakout" and rr < 1.5:
        return False, risk, rr
    if mode == "pullback" and rr < 1.3:
        return False, risk, rr

    return True, risk, rr


# ================================
# 🔥 strategy（核心升級）
# ================================
def strategy(price, ma5, ma20, closes, volumes):

    support, resistance = support_resistance(closes)

    market = market_signal(closes, ma20)
    trend = trend_signal(price, ma5, ma20)
    volume = volume_signal(volumes)
    structure = structure_state(closes)

    momentum = "ACCELERATING" if closes[-1] > closes[-3] else "DECELERATING"

    m_score = market_score(market, trend, structure, volume, momentum)
    m_grade = market_grade(m_score)

    cons = edge_consolidation(closes)
    base_pos = base_position(market, trend, structure, volume)

    # ================================
    # ❌ 直接排除
    # ================================
    if market == "WEAK" or trend == "DOWN" or volume == "DISTRIBUTION":
        return build_result(decision="NO_TRADE", position=0)

    if volume == "WEAK":
        return build_result(decision="WAIT", position=base_pos)

    if structure == "WEAK" and not cons:
        return build_result(decision="WAIT", position=base_pos)

    # ================================
    # 🔥🔥 新增：準突破試單（核心升級）
    # ================================
    if trend == "UP" and volume != "WEAK" and price > resistance * 0.97:
        return build_result(
            decision="BUY",
            decision_type="pre_breakout",  # ← 新類型
            buy=price,
            stop=min(ma5, support),
            position=0.3,  # 小倉試單
            market_score=m_score,
            market_grade=m_grade,
            trend=trend,
            volume_state=volume,
            structure_state=structure
        )

    # ================================
    # 🔥 突破
    # ================================
    if event_breakout(price, closes, resistance, volumes):

        if edge_fake_breakout(closes):
            return build_result(decision="NO_TRADE")

        buy, stop = price, min(ma5, support)
        ok, risk, rr = risk_control(buy, stop, resistance, "breakout")

        if ok:
            return build_result(
                decision="BUY",
                decision_type="breakout",
                buy=buy,
                stop=stop,
                position=position_size(risk, market),
                risk=risk,
                rr=rr,
                market_score=m_score,
                market_grade=m_grade,
                trend=trend,
                volume_state=volume,
                structure_state=structure
            )

    # ================================
    # 🔥 提前卡位（放寬）
    # ================================
    if cons and volume == "NORMAL" and closes[-1] > closes[-2] and trend == "UP":

        # 🔥 修改：early 不再卡 RR（讓系統會進場）
        return build_result(
            decision="BUY",
            decision_type="early",
            buy=price,
            stop=min(ma5, support),
            position=max(base_pos, 0.3),
            market_score=m_score,
            market_grade=m_grade,
            trend=trend,
            volume_state=volume,
            structure_state=structure
        )

    return build_result(
        decision="WAIT",
        position=base_pos,
        market_score=m_score,
        market_grade=m_grade,
        trend=trend,
        volume_state=volume,
        structure_state=structure
    )