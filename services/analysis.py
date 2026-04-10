# ===== 工具 =====
def avg(arr):
    return sum(arr) / len(arr) if len(arr) > 0 else 0


# ===== 統一輸出（高細膩版）=====
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
    breakout_strength=0,
    pullback_depth=0,
    distance_to_resistance=0,

    # 🔥 新增細節
    distance_to_support=0,
    distance_to_breakout=0,
    structure_state=None,
    momentum=0,
    momentum_state=None,
    breakout_quality=None,
    pullback_type=None
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
        "breakout_strength": round(breakout_strength, 2),
        "pullback_depth": round(pullback_depth, 2),
        "distance_to_resistance": round(distance_to_resistance, 3),

        # 🔥 高解析輸出
        "distance_to_support": round(distance_to_support, 3),
        "distance_to_breakout": round(distance_to_breakout, 3),
        "structure_state": structure_state,
        "momentum": round(momentum, 3),
        "momentum_state": momentum_state,
        "breakout_quality": breakout_quality,
        "pullback_type": pullback_type
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


# ===== 結構評分 =====
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


# ===== breakout 強度 =====
def breakout_strength(price, resistance, volumes):
    avg10 = avg(volumes[-10:])
    vol_ratio = volumes[-1] / avg10 if avg10 > 0 else 1
    price_strength = (price - resistance) / resistance
    return vol_ratio * 0.6 + price_strength * 0.4


# ===== pullback 深度 =====
def pullback_depth(price, ma5):
    return abs(price - ma5) / ma5


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


# ===== 🎯 最終策略 =====
def strategy(price, ma5, ma20, closes, volumes):

    support, resistance = support_resistance(closes)

    market = market_signal(closes, ma20)
    trend = trend_signal(price, ma5, ma20)
    vol = volume_signal(volumes)
    struct_score = structure_score(closes)

    # ===== 新增解析資料 =====
    distance_to_support = (price - support) / price if price > 0 else 0
    distance_to_breakout = (resistance - price) / price if price > 0 else 0
    distance_to_res = (resistance - price) / price if price > 0 else 0

    momentum = closes[-1] - closes[-3]

    if struct_score >= 0.7:
        structure_state = "STRONG"
    elif struct_score >= 0.5:
        structure_state = "NORMAL"
    else:
        structure_state = "WEAK"

    if momentum > 0:
        momentum_state = "ACCELERATING"
    else:
        momentum_state = "DECELERATING"

    # ===== 市場 =====
    if market == "WEAK":
        return build_result(
            "NO_TRADE",
            market=market,
            trend=trend,
            structure_score=struct_score,
            structure_state=structure_state,
            momentum=momentum,
            momentum_state=momentum_state
        )

    # ===== 趨勢 =====
    if trend == "DOWN":
        return build_result(
            "NO_TRADE",
            market=market,
            trend=trend
        )

    # ===== 結構 =====
    if struct_score < 0.5:
        return build_result(
            "WAIT",
            market=market,
            trend=trend,
            structure_score=struct_score,
            structure_state=structure_state,
            momentum=momentum,
            momentum_state=momentum_state,
            distance_to_breakout=distance_to_breakout
        )

    # ===== 出貨 =====
    if vol == "DISTRIBUTION":
        return build_result(
            "NO_TRADE",
            market=market,
            trend=trend,
            volume_state=vol
        )

    # ===== breakout =====
    if price > resistance:

        strength = breakout_strength(price, resistance, volumes)

        if strength > 1.2:
            quality = "CLEAN"
        elif strength > 0.8:
            quality = "NORMAL"
        else:
            quality = "WEAK"

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
            "breakout", strength, 0, distance_to_res,
            distance_to_support,
            distance_to_breakout,
            structure_state,
            momentum,
            momentum_state,
            quality,
            None
        )

    # ===== pullback =====
    depth = pullback_depth(price, ma5)

    if depth < 0.01:
        pb_type = "SHALLOW"
    elif depth < 0.03:
        pb_type = "NORMAL"
    else:
        pb_type = "DEEP"

    if trend == "UP" and depth < 0.03:

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
            "pullback", 0, depth, distance_to_res,
            distance_to_support,
            distance_to_breakout,
            structure_state,
            momentum,
            momentum_state,
            None,
            pb_type
        )

    return build_result(
        "WAIT",
        market=market,
        trend=trend,
        structure_score=struct_score,
        structure_state=structure_state,
        volume_state=vol,
        momentum=momentum,
        momentum_state=momentum_state,
        distance_to_breakout=distance_to_breakout,
        distance_to_support=distance_to_support
    )