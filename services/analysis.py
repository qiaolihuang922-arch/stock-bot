# ================================
# 🔥 analysis.py（FINAL v9.7｜最強股版）
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
# 🔥 🔥 強度分數（新增）
# ================================
def strength_score(result):

    score = 0

    # ✅ decision 權重最大
    if result.get("decision") == "BUY":
        score += 5
    elif result.get("decision") == "WAIT":
        score += 2

    # ✅ 市場分數
    m = result.get("market_score") or 0
    score += m * 0.5

    # ✅ RR
    rr = result.get("rr") or 0
    score += rr

    # ✅ 趨勢 / 結構 / 量能
    if result.get("trend") == "UP":
        score += 1

    if result.get("structure_state") == "STRONG":
        score += 1

    if result.get("volume_state") == "STRONG":
        score += 1

    return round(score, 2)


# ================================
# 🔥 市場強度（原樣保留）
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
# 🔥 統一輸出（升級）
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

    # 🔥 加入強度分數
    result["strength"] = strength_score(result)

    return result


# ================================
# 🔥 原邏輯（100%保留）
# ================================
def market_signal(closes, ma20):
    momentum = closes[-1] - closes[-3]

    if closes[-1] < ma20 and momentum < 0:
        return "WEAK"

    if (max(closes[-10:]) - min(closes[-10:])) / closes[-1] < 0.04:
        return "CHOPPY"

    if closes[-1] > ma20 and momentum > 0:
        return "STRONG"

    return "NORMAL"


def trend_signal(price, ma5, ma20):
    if price > ma5 > ma20:
        return "UP"
    if price < ma20:
        return "DOWN"
    return "SIDE"


def volume_signal(volumes):
    avg10 = avg(volumes[-10:])
    ratio = volumes[-1] / avg10 if avg10 else 1

    if ratio > 1.5 and volumes[-1] > volumes[-2]:
        return "STRONG"

    if ratio > 1.5 and volumes[-1] < volumes[-2]:
        return "DISTRIBUTION"

    if ratio < 0.8:
        return "WEAK"

    return "NORMAL"


def structure_state(closes):

    score = 0
    if closes[-1] > closes[-2]:
        score += 1
    if closes[-2] > closes[-3]:
        score += 1
    if closes[-1] > avg(closes[-5:]):
        score += 1

    if score >= 3:
        return "STRONG"
    elif score == 2:
        return "NORMAL"
    return "WEAK"


def structure_hold(closes):
    return closes[-1] > min(closes[-5:])


def support_resistance(closes):
    return min(closes[-20:]), max(closes[-20:-1])


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


def risk_control(buy, stop, resistance, mode):

    if stop >= buy:
        return False, 0, 0

    risk = (buy - stop) / buy
    if risk > 0.08:
        return False, risk, 0

    target = buy + (buy - stop) * 2 if mode == "breakout" else resistance
    rr = (target - buy) / (buy - stop) if (buy - stop) else 0

    if mode == "breakout" and rr < 1.5:
        return False, risk, rr
    if mode == "pullback" and rr < 1.3:
        return False, risk, rr

    return True, risk, rr


def base_position(market, trend, structure, volume):

    pos = 0

    if market == "STRONG":
        pos += 0.3
    elif market == "CHOPPY":
        pos += 0.2
    elif market == "NORMAL":
        pos += 0.1

    if trend == "UP":
        pos += 0.2

    if structure == "STRONG":
        pos += 0.2

    if volume == "STRONG":
        pos += 0.2
    elif volume == "NORMAL":
        pos += 0.1

    return round(min(pos, 0.5), 2)


def position_size(risk, market):

    if risk <= 0.03:
        pos = 1.0
    elif risk <= 0.05:
        pos = 0.7
    elif risk <= 0.08:
        pos = 0.5
    else:
        return 0

    cap = 1.0 if market == "STRONG" else 0.7 if market == "CHOPPY" else 0.5
    return min(pos, cap)


# ================================
# 🔥 strategy（完全保留）
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

    if market == "WEAK" or trend == "DOWN" or volume == "DISTRIBUTION":
        return build_result(decision="NO_TRADE", position=0)

    if volume == "WEAK":
        return build_result(decision="WAIT", position=base_pos)

    if structure == "WEAK" and not cons:
        return build_result(decision="WAIT", position=base_pos)

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

    if trend == "UP" and event_pullback(price, ma5, closes):

        if not structure_hold(closes):
            return build_result(decision="NO_TRADE")

        if not edge_first_pullback(closes, ma20):
            return build_result(decision="WAIT", position=max(base_pos, 0.3))

        buy, stop = ma5, min(ma20, support)
        ok, risk, rr = risk_control(buy, stop, resistance, "pullback")

        if ok:
            return build_result(
                decision="BUY",
                decision_type="pullback",
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

    if cons and volume == "NORMAL" and closes[-1] > closes[-2]:

        buy, stop = price, min(ma5, support)
        ok, risk, rr = risk_control(buy, stop, resistance, "pullback")

        if ok:
            return build_result(
                decision="BUY",
                decision_type="early",
                buy=buy,
                stop=stop,
                position=max(base_pos, 0.3),
                risk=risk,
                rr=rr,
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


# ================================
# 🔥 🔥 選出最強股票（新增）
# ================================
def pick_best_stock(results_dict):

    best_name = None
    best_score = -999

    for name, result in results_dict.items():
        score = result.get("strength", 0)

        if score > best_score:
            best_score = score
            best_name = name

    return best_name, best_score