# ===== 工具 =====
def avg(arr):
    return sum(arr) / len(arr) if len(arr) > 0 else 0


# ===== 量能（判斷型）=====
def volume_signal(volumes):
    avg10 = avg(volumes[-10:])
    ratio = volumes[-1] / avg10 if avg10 > 0 else 1

    vol_up = volumes[-1] > volumes[-2] > volumes[-3]

    if ratio > 1.5 and vol_up:
        return "STRONG"   # 突破有效

    if ratio > 1.5 and not vol_up:
        return "DISTRIBUTION"  # 出貨

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
    # 不再創低
    if not (closes[-1] >= closes[-2] >= closes[-3]):
        return False

    # 無爆量殺盤
    avg10 = avg(volumes[-10:])
    if volumes[-1] > avg10 * 1.8:
        return False

    # 不破結構低點
    if closes[-1] < min(closes[-7:]):
        return False

    return True


# ===== 支撐壓力 =====
def support_resistance(closes):
    return min(closes[-20:]), max(closes[-20:])


# ===== 假突破過濾（V5核心🔥）=====
def fake_breakout_filter(closes, volumes):
    prev_high = max(closes[-21:-1])
    avg10 = avg(volumes[-10:])

    # 昨天突破但收回
    if closes[-2] > prev_high and closes[-1] < prev_high:
        return True

    # 無量突破
    if closes[-1] > prev_high and volumes[-1] < avg10 * 1.1:
        return True

    return False


# ===== 突破策略（主策略🔥）=====
def breakout_entry(price, closes, volumes):
    prev_high = max(closes[-21:-1])
    avg10 = avg(volumes[-10:])

    return (
        price > prev_high and
        closes[-1] > prev_high and
        volumes[-1] > avg10 * 1.3
    )


# ===== 回踩策略（副策略🔥）=====
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


# ===== 風控 =====
def risk_control(buy, stop, resistance):
    if stop >= buy:
        stop = buy * 0.97

    risk = (buy - stop) / buy

    if risk > 0.08:
        return False, "RISK_TOO_HIGH"

    reward = resistance - buy
    if reward <= 0:
        return False, "NO_SPACE"

    rr = reward / (buy - stop)

    if rr < 1.2:
        return False, "RR_LOW"

    return True, "OK"


# ===== 倉位 =====
def position_size(buy, stop):
    risk = (buy - stop) / buy
    pos = min(0.02 / risk, 1.0)
    return int(pos * 100)


# ===== 🎯 最終策略（唯一決策源）=====
def strategy(price, ma5, ma20, closes, volumes):

    support, resistance = support_resistance(closes)

    # ===== 1️⃣ 市場 =====
    if market_signal(closes, ma20) == "WEAK":
        return "WAIT", "-", "-", "0%", "MARKET_WEAK", "HIGH"

    # ===== 2️⃣ 趨勢 =====
    trend = trend_signal(price, ma5, ma20)
    if trend == "DOWN":
        return "NO", "-", "-", "0%", "TREND_DOWN", "HIGH"

    # ===== 3️⃣ 結構 =====
    if not structure_ok(closes, volumes):
        return "WAIT", "-", "-", "0%", "STRUCTURE_BAD", "HIGH"

    # ===== 4️⃣ 量能 =====
    vol = volume_signal(volumes)

    if vol == "DISTRIBUTION":
        return "NO", "-", "-", "0%", "DISTRIBUTION", "HIGH"

    if vol == "WEAK":
        return "WAIT", "-", "-", "0%", "NO_VOLUME", "MID"

    # ===== 5️⃣ 假突破過濾（先擋🔥）=====
    if fake_breakout_filter(closes, volumes):
        return "NO", "-", "-", "0%", "FAKE_BREAKOUT", "HIGH"

    # ===== 6️⃣ 主策略：突破 =====
    if breakout_entry(price, closes, volumes):

        buy = price
        stop = min(ma5, min(closes[-10:]))

        ok, reason = risk_control(buy, stop, resistance)
        if not ok:
            return "NO", "-", "-", "0%", reason, "HIGH"

        pos = position_size(buy, stop)

        return "BUY", round(buy,1), round(stop,1), f"{pos}%", "BREAKOUT", "LOW"

    # ===== 7️⃣ 副策略：回踩 =====
    if trend == "UP" and pullback_entry(price, ma5, closes, volumes):

        buy = ma5
        stop = min(ma20, min(closes[-10:]))

        ok, reason = risk_control(buy, stop, resistance)
        if not ok:
            return "NO", "-", "-", "0%", reason, "MID"

        pos = position_size(buy, stop)

        return "BUY", round(buy,1), round(stop,1), f"{pos}%", "PULLBACK", "MID"

    # ===== 8️⃣ 無機會 =====
    return "WAIT", "-", "-", "0%", "NO_SIGNAL", "MID"