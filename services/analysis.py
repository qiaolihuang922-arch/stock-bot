# ===== 量能（🔥強化版）=====
def volume_model(volumes, closes):
    vol = volumes[-1]
    avg10 = sum(volumes[-10:]) / 10
    ratio = vol / avg10

    price_up = closes[-1] > closes[-2]

    if volumes[-1] < volumes[-2] < volumes[-3] and closes[-1] > sum(closes[-20:]) / 20:
        return "縮量整理（健康上升）"

    if ratio > 2 and not price_up:
        return "爆量（出貨⚠⚠）"

    vol_trend = volumes[-1] > volumes[-2] > volumes[-3]
    accumulation = sum(volumes[-3:]) > avg10 * 3

    if ratio > 2:
        level = "爆量"
    elif ratio > 1.5:
        level = "強放量"
    elif ratio > 1.2:
        level = "放量"
    elif ratio < 0.7:
        level = "縮量"
    else:
        level = "正常"

    if price_up and ratio > 1.3 and vol_trend and accumulation:
        return f"{level}（主升✔）"

    if ratio > 1.3 and not price_up:
        return f"{level}（出貨⚠）"

    if price_up and ratio < 1:
        return f"{level}（假突破⚠）"

    return level


# ===== 趨勢（🔥強化版）=====
def trend_model(price, ma5, ma20, closes, volumes):

    if closes[-2] < ma20 and price > ma20:
        return "🚀轉強起漲"

    ma20_prev = sum(closes[-21:-1]) / 20
    slope = ma20 - ma20_prev

    recent_high = max(closes[-5:])
    prev_high = max(closes[-10:-5])
    recent_low = min(closes[-5:])
    prev_low = min(closes[-10:-5])

    higher_high = recent_high > prev_high
    higher_low = recent_low > prev_low

    resistance = max(closes[-10:])
    near_res = price >= resistance * 0.97

    if price > ma5 > ma20 and slope > 0 and higher_high and higher_low:
        if price > recent_high * 0.98:
            return "🔥主升段"
        return "👍多頭結構"

    if near_res and slope < 0:
        return "⚠高位轉弱"

    if near_res:
        return "⚠高位震盪"

    if price > ma20 and slope > 0:
        return "多頭"

    if price < ma20 and slope < 0:
        return "空頭"

    return "震盪"


# ===== 支撐壓力 =====
def support_resistance(closes):
    return round(min(closes[-10:]), 1), round(max(closes[-10:]), 1)


# ===== 策略（🔥統一決策引擎版）=====
def strategy(price, ma5, ma20, closes, volumes):

    support, resistance = support_resistance(closes)

    vol = volumes[-1]
    avg10 = sum(volumes[-10:]) / 10

    volume_ok = vol > avg10 * 1.2
    volume_strong = vol > avg10 * 1.5
    momentum = price > closes[-2]

    recent_low = min(closes[-5:])
    prev_low = min(closes[-10:-5])
    structure_low = min(recent_low, prev_low)

    # ===== 🔥 統一評分系統（核心）=====
    score = 0
    reasons = []

    # ===== 趨勢 =====
    if price > ma20:
        score += 2
        reasons.append("站上MA20")
    else:
        score -= 2
        reasons.append("跌破MA20")

    if price > ma5:
        score += 1
        reasons.append("站上MA5")

    # ===== 動能 =====
    if momentum:
        score += 1
        reasons.append("動能上升")

    # ===== 量能 =====
    ratio = vol / avg10

    if ratio > 1.5:
        score += 2
        reasons.append("強放量")
    elif ratio > 1.2:
        score += 1
        reasons.append("放量")
    elif ratio < 0.7:
        score -= 1
        reasons.append("縮量")

    # ===== 結構 =====
    if closes[-1] > closes[-2] > closes[-3]:
        score += 1
        reasons.append("連續上漲")

    # ===== 位置（超重要）=====
    if price > resistance * 0.97:
        score -= 2
        reasons.append("接近壓力")

    if price < ma5:
        score += 1
        reasons.append("回踩支撐")

    # ===== 🔥 轉強加分（取代 trend）=====
    if closes[-2] < ma20 and price > ma20:
        score += 2
        reasons.append("轉強突破")

    # ===== 防呆 =====
    if price > resistance * 1.05:
        return "觀望（過熱區）", "-", "-", "0%"

    # ===== 🔥 買點計算 =====
    buy = "-"
    stop = "-"

    # 主升
    if score >= 6:
        buy = price * 0.995
        stop = structure_low

    # 穩健
    elif score >= 4:
        if abs(price - ma5) / ma5 <= 0.03:
            buy = ma5
        else:
            buy = "-"
        stop = max(ma20 * 0.97, structure_low)

    # 試單
    elif score >= 2:
        if price > ma20 and momentum:
            buy = price * 0.995
            stop = ma20 * 0.97
        elif abs(price - ma5) / ma5 <= 0.02:
            buy = ma5
            stop = ma20 * 0.97
        else:
            return "觀望（等待轉強）", "-", "-", "0%"

    else:
        return "觀望（訊號不足）", "-", "-", "0%"

    # ===== 風險控制 =====
    if buy != "-" and stop != "-":

        if stop >= buy:
            stop = buy * 0.97

        risk = (buy - stop) / buy

        if risk > 0.08:
            return "觀望（風險過大）", "-", "-", "0%"

    # ===== 🔥 決策輸出 =====
    if score >= 6:
        decision = "進場🔥（強勢）"
        position = "100%"
    elif score >= 4:
        decision = "進場（穩健）"
        position = "50%"
    else:
        decision = "試單（觀察）"
        position = "30%"

    return decision, round(buy,1), round(stop,1), position

 