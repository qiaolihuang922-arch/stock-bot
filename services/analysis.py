# ================================
# 🔥 analysis.py（v8.1最終完整版）
# ================================

# ===== 工具 =====
def avg(arr):
    return sum(arr) / len(arr) if len(arr) > 0 else 0


# ===== 統一輸出 =====
def build_result(
    decision,
    decision_type="none",
    buy=None,
    stop=None,
    pos=0,
    risk=0,
    rr=0,
    market=None,
    trend=None,
    structure_score=0,
    volume_state=None,
    event=None,
    edge=None,
    structure_state=None,
    momentum_state=None,
    breakout_quality=None,
    pullback_type=None,
    distance_to_breakout=0,
    distance_to_support=0
):
    return {
        "decision": decision,
        "decision_type": decision_type,
        "buy": buy,
        "stop": stop,
        "position": pos,
        "risk": round(risk, 4),
        "rr": round(rr, 2),
        "market": market,
        "trend": trend,
        "structure_score": round(structure_score, 2),
        "volume_state": volume_state,
        "event": event,
        "edge": edge,
        "structure_state": structure_state,
        "momentum_state": momentum_state,
        "breakout_quality": breakout_quality,
        "pullback_type": pullback_type,
        "distance_to_breakout": round(distance_to_breakout, 3),
        "distance_to_support": round(distance_to_support, 3)
    }


# ===== 市場 =====
def market_signal(closes, ma20):
    momentum = closes[-1] - closes[-3]

    if closes[-1] < ma20 and momentum < 0:
        return "WEAK"

    if (max(closes[-10:]) - min(closes[-10:])) / closes[-1] < 0.04:
        return "CHOPPY"

    if closes[-1] > ma20 and momentum > 0:
        return "STRONG"

    return "NORMAL"


# ===== 趨勢 =====
def trend_signal(price, ma5, ma20):
    if price > ma5 > ma20:
        return "UP"
    if price < ma20:
        return "DOWN"
    return "SIDE"


# ===== 量能 =====
def volume_signal(volumes):
    avg10 = avg(volumes[-10:])
    ratio = volumes[-1] / avg10 if avg10 > 0 else 1

    if ratio > 1.5 and volumes[-1] > volumes[-2]:
        return "STRONG"

    if ratio > 1.5 and volumes[-1] < volumes[-2]:
        return "DISTRIBUTION"

    if ratio < 0.8:
        return "WEAK"

    return "NORMAL"


# ===== 結構 =====
def structure_score(closes):
    score = 0

    if closes[-1] > closes[-2]:
        score += 0.3
    if closes[-2] > closes[-3]:
        score += 0.2
    if closes[-1] > avg(closes[-5:]):
        score += 0.3
    if closes[-1] > min(closes[-10:]):
        score += 0.2

    return score


# ===== 支撐壓力 =====
def support_resistance(closes):
    support = min(closes[-20:])
    resistance = max(closes[-20:-3])
    return support, resistance


# ===== 假突破過濾 =====
def fake_breakout(closes):
    prev_high = max(closes[-21:-1])

    if closes[-2] > prev_high and closes[-1] < prev_high:
        return True

    return False


# ===== 結構未破 =====
def not_break_structure(closes):
    return closes[-1] > min(closes[-5:])


# ===== breakout event =====
def breakout_event(price, closes, resistance, volumes):
    avg10 = avg(volumes[-10:])

    return (
        price > resistance and
        closes[-1] > resistance and
        volumes[-1] > avg10 * 1.5
    )


# ===== pullback event =====
def pullback_event(closes, price, ma5):
    rebound = closes[-1] > closes[-2]
    near = abs(price - ma5) / ma5 < 0.03
    return near and rebound


# ===== breakout edge =====
def breakout_edge(closes, volumes):
    tight = (max(closes[-5:]) - min(closes[-5:])) / closes[-1] < 0.04

    recent_high = max(closes[-30:])
    not_high = closes[-1] < recent_high * 0.95

    vol_ok = volumes[-1] > avg(volumes[-5:])

    return tight and not_high and vol_ok


# ===== pullback edge =====
def pullback_edge(closes, ma20):
    rising = ma20 > avg(closes[-20:])
    first = closes[-2] > ma20 and closes[-3] > ma20
    return rising and first


# ===== 風控 =====
def risk_control(buy, stop, resistance, decision_type):

    if stop >= buy:
        return False, 0, 0

    risk = (buy - stop) / buy
    if risk > 0.08:
        return False, risk, 0

    reward = resistance - buy
    if reward <= 0:
        return False, risk, 0

    rr = reward / (buy - stop)

    if decision_type == "breakout" and rr < 1.8:
        return False, risk, rr

    if decision_type == "pullback" and rr < 1.5:
        return False, risk, rr

    return True, risk, rr


# ===== 倉位 =====
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


# ===== 🎯 strategy =====
def strategy(price, ma5, ma20, closes, volumes):

    support, resistance = support_resistance(closes)

    market = market_signal(closes, ma20)
    trend = trend_signal(price, ma5, ma20)
    vol = volume_signal(volumes)
    struct_score = structure_score(closes)

    structure_state = "STRONG" if struct_score >= 0.7 else "NORMAL" if struct_score >= 0.5 else "WEAK"
    momentum_state = "ACCELERATING" if closes[-1] > closes[-3] else "DECELERATING"

    distance_to_breakout = (resistance - price) / price if price > 0 else 0
    distance_to_support = (price - support) / price if price > 0 else 0

    # ===== 市場 =====
    if market == "WEAK":
        return build_result("NO_TRADE", market=market)

    # ===== 趨勢 =====
    if trend == "DOWN":
        return build_result("NO_TRADE", trend=trend)

    # ===== 量能 =====
    if vol == "DISTRIBUTION":
        return build_result("NO_TRADE", volume_state=vol)

    if vol == "WEAK":
        return build_result("WAIT", volume_state=vol)

    # ===== 結構 =====
    if struct_score < 0.5:
        return build_result("WAIT", structure_score=struct_score)

    # ===== breakout =====
    if breakout_event(price, closes, resistance, volumes):

        if fake_breakout(closes):
            return build_result("NO_TRADE", event="fake_breakout")

        if distance_to_breakout < 0.01 or distance_to_breakout > 0.08:
            return build_result("WAIT", event="breakout", edge=False)

        if not breakout_edge(closes, volumes):
            return build_result("WAIT", event="breakout", edge=False)

        buy = price
        stop = min(ma5, support)

        ok, risk, rr = risk_control(buy, stop, resistance, "breakout")
        if not ok:
            return build_result("NO_TRADE", rr=rr)

        pos = position_size(risk, market)

        return build_result(
            "BUY", "breakout",
            buy, stop, pos, risk, rr,
            market, trend, struct_score, vol,
            "breakout", True,
            structure_state,
            momentum_state,
            "CLEAN",
            None,
            distance_to_breakout,
            distance_to_support
        )

    # ===== pullback =====
    if trend == "UP" and pullback_event(closes, price, ma5):

        if not not_break_structure(closes):
            return build_result("NO_TRADE", event="structure_break")

        if not pullback_edge(closes, ma20):
            return build_result("WAIT", event="pullback", edge=False)

        buy = ma5
        stop = min(ma20, support)

        ok, risk, rr = risk_control(buy, stop, resistance, "pullback")
        if not ok:
            return build_result("NO_TRADE", rr=rr)

        pos = position_size(risk, market)

        return build_result(
            "BUY", "pullback",
            buy, stop, pos, risk, rr,
            market, trend, struct_score, vol,
            "pullback", True,
            structure_state,
            momentum_state,
            None,
            "NORMAL",
            distance_to_breakout,
            distance_to_support
        )

    return build_result("WAIT", market=market)