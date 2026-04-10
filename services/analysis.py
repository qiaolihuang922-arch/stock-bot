# ===== 工具 =====
def avg(arr):
    return sum(arr) / len(arr) if len(arr) > 0 else 0


# ===== 統一輸出（v6核心🔥）=====
def build_result(decision, decision_type="none", buy=None, stop=None, pos=0, risk=0, rr=0):
    return {
        "decision": decision,
        "decision_type": decision_type,
        "buy": buy,
        "stop": stop,
        "position": pos,
        "risk": round(risk, 4),
        "rr": round(rr, 2)
    }


# ===== 量能 =====
def volume_signal(volumes):
    avg10 = avg(volumes[-10:])
    ratio = volumes[-1] / avg10 if avg10 > 0 else 1

    vol_up = volumes[-1] > volumes[-2] > volumes[-3]

    if ratio > 1.5 and vol_up:
        return "STRONG"

    if ratio > 1.5 and not vol_up:
        return "DISTRIBUTION"

    if ratio < 0.8:
        return "WEAK"

    return "NORMAL"


# ===== 趨勢 =====
def trend_signal(price, ma5, ma20):
    if price > ma5 > ma20:
        return "UP"

    if price < ma20:
        return "DOWN"

    return "SIDE"


# ===== 市場 =====
def market_signal(closes, ma20):
    if closes[-1] < ma20 and closes[-1] < closes[-2] < closes[-3]:
        return "WEAK"
    return "NORMAL"


# ===== 結構 =====
def structure_ok(closes, volumes):
    if not (closes[-1] >= closes[-2] >= closes[-3]):
        return False

    avg10 = avg(volumes[-10:])
    if volumes[-1] > avg10 * 1.8:
        return False

    if closes[-1] < min(closes[-7:]):
        return False

    return True


# ===== 支撐壓力（優化版）=====
def support_resistance(closes):
    support = min(closes[-20:])
    resistance = max(closes[-20:-3])  # 避免最新高點污染
    return support, resistance


# ===== 假突破過濾 =====
def fake_breakout_filter(closes, volumes):
    prev_high = max(closes[-21:-1])
    avg10 = avg(volumes[-10:])

    if closes[-2] > prev_high and closes[-1] < prev_high:
        return True

    if closes[-1] > prev_high and volumes[-1] < avg10 * 1.1:
        return True

    return False


# ===== 突破 =====
def breakout_entry(price, closes, volumes):
    prev_high = max(closes[-21:-1])
    avg10 = avg(volumes[-10:])

    return (
        price > prev_high and
        closes[-1] > prev_high and
        volumes[-1] > avg10 * 1.5
    )


# ===== 回踩 =====
def pullback_entry(price, ma5, closes, volumes):
    avg10 = avg(volumes[-10:])
    ratio = volumes[-1] / avg10 if avg10 > 0 else 1

    near_ma5 = abs(price - ma5) / ma5 <= 0.02
    rebound = closes[-1] > closes[-2]

    return (
        near_ma5 and
        rebound and
        ratio < 1.2
    )


# ===== 風控（v6輸出🔥）=====
def risk_control(buy, stop, resistance):
    if stop >= buy:
        stop = buy * 0.97

    risk = (buy - stop) / buy

    if risk > 0.08:
        return False, risk, 0

    reward = resistance - buy
    if reward <= 0:
        return False, risk, 0

    rr = reward / (buy - stop)

    if rr < 1.2:
        return False, risk, rr

    return True, risk, rr


# ===== 倉位 =====
def position_size(buy, stop):
    risk = (buy - stop) / buy
    if risk == 0:
        return 0
    pos = min(0.02 / risk, 1.0)
    return int(pos * 100)


# ===== 🎯 最終策略 =====
def strategy(price, ma5, ma20, closes, volumes):

    support, resistance = support_resistance(closes)

    # ===== 市場 =====
    if market_signal(closes, ma20) == "WEAK":
        return build_result("WAIT")

    # ===== 趨勢 =====
    trend = trend_signal(price, ma5, ma20)
    if trend == "DOWN":
        return build_result("NO_TRADE")

    # ===== 結構 =====
    if not structure_ok(closes, volumes):
        return build_result("WAIT")

    # ===== 量能 =====
    vol = volume_signal(volumes)

    if vol == "DISTRIBUTION":
        return build_result("NO_TRADE")

    if vol == "WEAK":
        return build_result("WAIT")

    # ===== 假突破 =====
    if fake_breakout_filter(closes, volumes):
        return build_result("NO_TRADE")

    # ===== 突破 =====
    if breakout_entry(price, closes, volumes):

        buy = price
        stop = min(ma5, min(closes[-10:]))

        ok, risk, rr = risk_control(buy, stop, resistance)
        if not ok:
            return build_result("NO_TRADE")

        pos = position_size(buy, stop)

        return build_result("BUY", "breakout", buy, stop, pos, risk, rr)

    # ===== 回踩 =====
    if trend == "UP" and structure_ok(closes, volumes) and pullback_entry(price, ma5, closes, volumes):

        buy = ma5
        stop = min(ma20, min(closes[-10:]))

        ok, risk, rr = risk_control(buy, stop, resistance)
        if not ok:
            return build_result("NO_TRADE")

        pos = position_size(buy, stop)

        return build_result("BUY", "pullback", buy, stop, pos, risk, rr)

    # ===== 無機會 =====
    return build_result("WAIT")