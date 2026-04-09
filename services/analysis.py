# ===== 量能（🔥強化版）=====
def volume_model(volumes, closes):
    vol = volumes[-1]
    avg10 = sum(volumes[-10:]) / 10
    ratio = vol / avg10

    price_up = closes[-1] > closes[-2]

    # 🔥 健康上漲（量縮+價格撐住）
    if volumes[-1] < volumes[-2] < volumes[-3] and closes[-1] > sum(closes[-20:]) / 20:
        return "縮量整理（健康上升）"

    # 🔥 爆量下跌（強警告）
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

    # 🔥 MA翻多起漲（優先判斷）
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

    # 🔥 主升結構
    if price > ma5 > ma20 and slope > 0 and higher_high and higher_low:
        if price > recent_high * 0.98:
            return "🔥主升段"
        return "👍多頭結構"

    # 🔥 高位風險（提前警告）
    if near_res and slope < 0:
        return "⚠高位轉弱"

    if near_res:
        return "⚠高位震盪"

    if price > ma20 and slope > 0:
        return "多頭"

    if price < ma20 and slope < 0:
        return "空頭"

    return "震盪"


# ===== 支撐壓力（保留）=====
def support_resistance(closes):
    return round(min(closes[-10:]), 1), round(max(closes[-10:]), 1)


# ===== 策略（🔥AI級強化版）=====
def strategy(price, ma5, ma20, closes, volumes):
    support, resistance = support_resistance(closes)

    vol = volumes[-1]
    avg10 = sum(volumes[-10:]) / 10

    volume_ok = vol > avg10 * 1.2
    volume_strong = vol > avg10 * 1.5
    momentum = price > closes[-2]

    confirm = sum([volume_ok, momentum, price > ma20]) >= 2
    breakout = price > resistance

    recent_low = min(closes[-5:])
    prev_low = min(closes[-10:-5])
    structure_low = min(recent_low, prev_low)

    # ===== 🔥 防呆 =====
    if price < ma20 and not volume_strong:
        return "觀望（弱勢）", "-", "-", "0%"

    # 🔥 過熱區（避免追高）
    if price > resistance * 1.05:
        return "觀望（過熱區）", "-", "-", "0%"

    # 🔥 假突破過濾（強化）
    if breakout and confirm:
        if closes[-1] <= closes[-2]:
            return "觀望（假突破）", "-", "-", "0%"

    # ===== 🔥 類AI評分系統 =====
    score = 0

    if price > ma20:
        score += 2
    if price > ma5:
        score += 1
    if momentum:
        score += 1
    if volume_strong:
        score += 2
    elif volume_ok:
        score += 1

    if price > resistance:
        score += 1
    if price > resistance * 0.98:
        score -= 1  # 靠近壓力扣分

    # ===== 🔥 主升直接進場 =====
    not_too_high = price < resistance * 1.03

    if volume_strong and momentum and price > ma5 and price > ma20 and not_too_high:
        return "進場🔥（主升）", round(price, 1), round(structure_low, 1), "100%"

    # ===== 原邏輯 =====
    if price > resistance and vol > avg10 * 1.5:
        buy = price
        stop = max(resistance * 0.97, structure_low)

    elif breakout and confirm:
        buy = price
        stop = max(resistance * 0.97, structure_low)

    elif price >= ma5:
        if price > ma5 * 1.05:
            return "觀望（過高）", "-", "-", "0%"
        buy = min(ma5, support)
        stop = max(ma20 * 0.98, structure_low)

    elif price > ma20:
        buy = ma20
        stop = max(ma20 * 0.97, structure_low)

    else:
        return "觀望", "-", "-", "0%"

    # ===== 🔥 停損強化 =====
    stop = min(structure_low, buy * 0.97)
    stop = min(stop, buy * 0.96)

    if stop >= buy:
        stop = buy * 0.97

    if (buy - stop) / buy > 0.08:
        return "觀望（風險過大）", "-", "-", "0%"

    # ===== 🔥 決策分級（關鍵升級）=====
    if score >= 6:
        decision = "進場🔥（強勢）"
        position = "100%"
    elif score >= 4:
        decision = "進場（穩健）"
        position = "50%"
    elif score >= 2:
        decision = "試單（觀察）"
        position = "30%"
    else:
        return "觀望（訊號不足）", "-", "-", "0%"

    return decision, round(buy, 1), round(stop, 1), position