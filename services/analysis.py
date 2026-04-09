# ===== 量能（🔥完整保留+強化）=====
def volume_model(volumes, closes):
    vol = volumes[-1]
    avg10 = sum(volumes[-10:]) / 10
    ratio = vol / avg10

    price_up = closes[-1] > closes[-2]

    # 健康整理
    if volumes[-1] < volumes[-2] < volumes[-3] and closes[-1] > sum(closes[-20:]) / 20:
        return "縮量整理（健康上升）"

    # 爆量出貨
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


# ===== 趨勢（🔥完整保留）=====
def trend_model(price, ma5, ma20, closes, volumes):

    # 轉強
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


# ===== 策略（🔥最終融合版｜不刪邏輯）=====
def strategy(price, ma5, ma20, closes, volumes):

    support, resistance = support_resistance(closes)

    vol = volumes[-1]
    avg10 = sum(volumes[-10:]) / 10
    ratio = vol / avg10

    momentum = price > closes[-2]

    recent_low = min(closes[-5:])
    prev_low = min(closes[-10:-5])
    structure_low = min(recent_low, prev_low)

    breakout = price > resistance

    # ===== 🔥 統一評分 =====
    score = 0

    # ===== 趨勢 =====
    if price > ma20:
        score += 2
    else:
        score -= 3

    if price > ma5:
        score += 1

    # ===== 動能 =====
    if momentum:
        score += 1

    # ===== 量能（融合舊邏輯）=====
    if ratio > 2:
        if not momentum:
            score -= 3   # 爆量出貨
        else:
            score += 2   # 爆量上攻

    elif ratio > 1.5:
        score += 2

    elif ratio > 1.2:
        score += 1

    elif ratio < 0.7:
        score -= 1

    # ===== 結構（升級版）=====
    up_days = sum([1 for i in range(-5, 0) if closes[i] > closes[i-1]])

    if up_days >= 4:
        score += 2
    elif up_days >= 3:
        score += 1

    # 創高
    if closes[-1] > max(closes[-5:-1]):
        score += 1

    # 破低
    if closes[-1] < min(closes[-5:-1]):
        score -= 2

    # ===== 位置 =====
    if price > resistance * 0.97:
        score -= 2

    if price < ma5:
        score += 1

    # ===== 假突破 =====
    if breakout and closes[-1] <= closes[-2]:
        score -= 3

    # ===== 轉強確認 =====
    if closes[-3] < ma20 and closes[-2] < ma20 and price > ma20:
        score += 2

    # ===== 過熱 =====
    if price > resistance * 1.05:
        return "觀望（過熱）", "-", "-", "0%"

    # ===== 買點 =====
    buy = "-"
    stop = "-"

    # 強勢
    if score >= 6:
        buy = min(price * 0.995, resistance * 1.01)
        stop = structure_low

    # 穩健
    elif score >= 4:
        if abs(price - ma5) / ma5 <= 0.03:
            buy = ma5
            stop = max(ma20 * 0.97, structure_low)
        else:
            return "觀望（未回踩）", "-", "-", "0%"

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
        return "觀望（弱勢）", "-", "-", "0%"

    # ===== 風險控制 =====
    if stop >= buy:
        stop = buy * 0.97

    risk = (buy - stop) / buy

    if risk > 0.08:
        return "觀望（風險過大）", "-", "-", "0%"

    # ===== RR（關鍵補強）=====
    reward = resistance - buy
    rr = reward / (buy - stop) if (buy - stop) > 0 else 0

    if rr < 1.2:
        return "觀望（報酬不足）", "-", "-", "0%"

    # ===== 最終決策 =====
    if score >= 6:
        return "進場🔥（強勢）", round(buy,1), round(stop,1), "100%"
    elif score >= 4:
        return "進場（穩健）", round(buy,1), round(stop,1), "50%"
    else:
        return "試單（觀察）", round(buy,1), round(stop,1), "30%"