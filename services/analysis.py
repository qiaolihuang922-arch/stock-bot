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


# ===== 策略（🔥最終極穩定版）=====
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

    # ===== 防呆 =====
    if price < ma20 and not volume_strong:
        return "觀望（弱勢）", "-", "-", "0%"

    if price > resistance * 1.05:
        return "觀望（過熱區）", "-", "-", "0%"

    if price > ma5 * 1.03:
        return "觀望（追高風險）", "-", "-", "0%"

    if breakout and confirm:
        if closes[-1] <= closes[-2]:
            return "觀望（假突破）", "-", "-", "0%"

    # ===== 評分 =====
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
        score -= 1

    # ===== 🔥 轉強突破試單（修正版本）=====
    if price > ma20 and closes[-2] < ma20:
        if momentum and price < resistance * 1.02:
            buy = price * 0.995
            stop = ma20 * 0.97
            return "試單（轉強突破）", round(buy,1), round(stop,1), "30%"

    # ===== 主升 =====
    if volume_strong and momentum and price > ma5 and price > ma20:
        buy = price * 0.995
        stop = structure_low

        rr = (price - stop) / price
        if rr > 0.06:
            return "觀望（風險過大）", "-", "-", "0%"

        return "進場🔥（主升）", round(buy,1), round(stop,1), "100%"

    # ===== 回踩 =====
    if breakout and confirm:
        buy = resistance * 1.01
        stop = max(resistance * 0.97, structure_low)

    elif price >= ma5:
        if abs(price - ma5) / ma5 > 0.03:
            return "觀望（未回踩MA5）", "-", "-", "0%"

        buy = ma5
        stop = max(ma20 * 0.98, structure_low)

    elif price > ma20:
        if abs(price - ma20) / ma20 > 0.03:
            return "觀望（未回踩MA20）", "-", "-", "0%"

        buy = ma20
        stop = max(ma20 * 0.97, structure_low)

    else:
        return "觀望", "-", "-", "0%"

    # ===== 停損 =====
    stop = min(structure_low, buy * 0.97)
    stop = min(stop, buy * 0.96)

    if stop >= buy:
        stop = buy * 0.97

    # ===== RR =====
    rr = (buy - stop) / buy
    if rr > 0.08:
        return "觀望（風險過大）", "-", "-", "0%"

    # ===== 決策 =====
    if score >= 6:
        return "進場🔥（強勢）", round(buy,1), round(stop,1), "100%"

    elif score >= 4:
        return "進場（穩健）", round(buy,1), round(stop,1), "50%"

    elif score >= 2:

        if price <= ma5 * 1.01:
            return "試單（支撐）", round(ma5,1), round(ma20*0.97,1), "30%"

        if price > ma20 and momentum:
            return "試單（轉強）", round(price*0.995,1), round(ma20*0.97,1), "30%"

        return "觀望（等待確認）", "-", "-", "0%"

    return "觀望（訊號不足）", "-", "-", "0%"