# ================================
# 🔥 analysis.py（FINAL v8.5.1）
# ================================

# ===== 工具 =====
def avg(arr):
    return sum(arr) / len(arr) if arr else 0


# ================================
# 🔥 市場強度（不影響 decision）
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
# 🔥 統一輸出（修正 default）
# ================================
def build_result(**kwargs):

    return {
        "decision": kwargs.get("decision", "WAIT"),
        "decision_type": kwargs.get("decision_type", "none"),

        "buy": kwargs.get("buy"),
        "stop": kwargs.get("stop"),
        "position": kwargs.get("position", 0),

        "risk": round(kwargs.get("risk", 0), 4),
        "rr": round(kwargs.get("rr", 0), 2),

        "market_signal": kwargs.get("market_signal"),
        "trend": kwargs.get("trend"),
        "structure_state": kwargs.get("structure_state"),
        "volume_state": kwargs.get("volume_state"),
        "momentum_state": kwargs.get("momentum_state"),

        # 🔥 新增（顯示用，不影響策略）
        "market_score": kwargs.get("market_score"),
        "market_grade": kwargs.get("market_grade"),

        # ===== event（避免 None）=====
        "event_breakout": kwargs.get("event_breakout", False),
        "event_pullback": kwargs.get("event_pullback", False),

        # ===== edge =====
        "edge_consolidation": kwargs.get("edge_consolidation"),
        "edge_fake_breakout": kwargs.get("edge_fake_breakout"),
        "edge_not_high_zone": kwargs.get("edge_not_high_zone"),  # 🔥補齊
        "edge_first_pullback": kwargs.get("edge_first_pullback"),
        "edge_ma20_trend": kwargs.get("edge_ma20_trend"),
        "edge_structure_hold": kwargs.get("edge_structure_hold"),
    }


# ================================
# 🔥 市場 / 趨勢 / 量能
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


# ================================
# 🔥 結構
# ================================
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


# ================================
# 🔥 支撐 / 壓力
# ================================
def support_resistance(closes):
    support = min(closes[-20:])
    resistance = max(closes[-20:-3])
    return support, resistance


# ================================
# 🔥 Event
# ================================
def event_breakout(price, closes, resistance, volumes):

    avg5 = avg(volumes[-5:])

    return (
        price > resistance and
        closes[-1] > resistance and
        volumes[-1] > avg5 * 1.5
    )


def event_pullback(price, ma5, closes):

    near = abs(price - ma5) / ma5 < 0.03
    rebound = closes[-1] > closes[-2]

    return near and rebound


# ================================
# 🔥 Edge
# ================================
def edge_consolidation(closes):
    return (max(closes[-5:]) - min(closes[-5:])) / closes[-1] < 0.04


def edge_fake_breakout(closes):
    prev_high = max(closes[-21:-1])
    return closes[-2] > prev_high and closes[-1] < prev_high


def edge_first_pullback(closes, ma20):
    return closes[-2] > ma20 and closes[-3] > ma20


def edge_ma20_trend(ma20, closes):
    return ma20 > avg(closes[-20:])


# ================================
# 🔥 風控
# ================================
def risk_control(buy, stop, resistance, decision_type):

    if stop >= buy:
        return False, 0, 0

    risk = (buy - stop) / buy
    if risk > 0.08:
        return False, risk, 0

    if decision_type == "breakout":
        target = buy + (buy - stop) * 2
    else:
        target = resistance

    reward = target - buy
    rr = reward / (buy - stop) if (buy - stop) else 0

    if decision_type == "breakout" and rr < 1.8:
        return False, risk, rr

    if decision_type == "pullback" and rr < 1.5:
        return False, risk, rr

    return True, risk, rr


# ================================
# 🔥 倉位
# ================================
def position_size(risk, market):

    if risk <= 0.03:
        pos = 1.0
    elif risk <= 0.05:
        pos = 0.7
    elif risk <= 0.08:
        pos = 0.5
    else:
        return 0

    if market == "CHOPPY":
        pos *= 0.7

    if market == "WEAK":
        return 0

    return round(pos, 2)


# ================================
# 🔥 🎯 strategy（核心不動）
# ================================
def strategy(price, ma5, ma20, closes, volumes):

    support, resistance = support_resistance(closes)

    market = market_signal(closes, ma20)
    trend = trend_signal(price, ma5, ma20)
    volume = volume_signal(volumes)
    structure = structure_state(closes)

    momentum = "ACCELERATING" if closes[-1] > closes[-3] else "DECELERATING"

    # 🔥 新增（不影響決策）
    m_score = market_score(market, trend, structure, volume, momentum)
    m_grade = market_grade(m_score)

    # ===== 市場 =====
    if market == "WEAK":
        return build_result(decision="NO_TRADE", market_signal=market, market_score=m_score, market_grade=m_grade)

    if trend == "DOWN":
        return build_result(decision="NO_TRADE", trend=trend, market_score=m_score, market_grade=m_grade)

    if volume == "DISTRIBUTION":
        return build_result(decision="NO_TRADE", volume_state=volume, market_score=m_score, market_grade=m_grade)

    if volume == "WEAK":
        return build_result(decision="WAIT", volume_state=volume, market_score=m_score, market_grade=m_grade)

    if structure == "WEAK":
        return build_result(decision="WAIT", structure_state=structure, market_score=m_score, market_grade=m_grade)

    # ===== breakout =====
    e_break = event_breakout(price, closes, resistance, volumes)
    fake = edge_fake_breakout(closes)
    cons = edge_consolidation(closes)
    high_zone = price > resistance * 1.08

    if e_break:

        if fake:
            return build_result(decision="NO_TRADE", edge_fake_breakout=True)

        if high_zone:
            return build_result(
                decision="WAIT",
                event_breakout=True,
                edge_not_high_zone=False
            )

        if not cons:
            return build_result(decision="WAIT", edge_consolidation=False)

        buy = price
        stop = min(ma5, support)

        ok, risk, rr = risk_control(buy, stop, resistance, "breakout")
        if not ok:
            return build_result(decision="NO_TRADE", rr=rr)

        pos = position_size(risk, market)

        return build_result(
            decision="BUY",
            decision_type="breakout",
            buy=buy,
            stop=stop,
            position=pos,
            risk=risk,
            rr=rr,
            market_signal=market,
            trend=trend,
            structure_state=structure,
            volume_state=volume,
            momentum_state=momentum,
            event_breakout=True,
            edge_consolidation=True,
            edge_fake_breakout=False,
            edge_not_high_zone=True,
            market_score=m_score,
            market_grade=m_grade
        )

    # ===== pullback =====
    e_pull = event_pullback(price, ma5, closes)
    first = edge_first_pullback(closes, ma20)
    ma20_up = edge_ma20_trend(ma20, closes)
    hold = structure_hold(closes)

    if trend == "UP" and e_pull:

        if not hold:
            return build_result(decision="NO_TRADE", edge_structure_hold=False)

        if not first or not ma20_up:
            return build_result(
                decision="WAIT",
                event_pullback=True,
                edge_first_pullback=first,
                edge_ma20_trend=ma20_up
            )

        buy = ma5
        stop = min(ma20, support)

        ok, risk, rr = risk_control(buy, stop, resistance, "pullback")
        if not ok:
            return build_result(decision="NO_TRADE", rr=rr)

        pos = position_size(risk, market)

        return build_result(
            decision="BUY",
            decision_type="pullback",
            buy=buy,
            stop=stop,
            position=pos,
            risk=risk,
            rr=rr,
            market_signal=market,
            trend=trend,
            structure_state=structure,
            volume_state=volume,
            momentum_state=momentum,
            event_pullback=True,
            edge_first_pullback=True,
            edge_ma20_trend=True,
            edge_structure_hold=True,
            market_score=m_score,
            market_grade=m_grade
        )

    return build_result(decision="WAIT", market_signal=market, market_score=m_score, market_grade=m_grade)