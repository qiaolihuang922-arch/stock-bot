# ===== 量能（完全保留）=====
def volume_model(volumes, closes):
    vol = volumes[-1]
    avg10 = sum(volumes[-10:]) / 10
    ratio = vol / avg10

    if volumes[-1] < volumes[-2] < volumes[-3] and closes[-1] > sum(closes[-20:]) / 20:
        return "縮量整理（蓄力🔥）"

    vol_trend = volumes[-1] > volumes[-2] > volumes[-3]
    accumulation = sum(volumes[-3:]) > avg10 * 3
    price_up = closes[-1] > closes[-2]

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


# ===== 趨勢（完全保留）=====
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

    if near_res:
        return "⚠高位震盪"

    if price > ma20 and slope > 0:
        return "多頭"

    if price < ma20 and slope < 0:
        return "空頭"

    return "震盪"


# ===== 支撐壓力（完全保留）=====
def support_resistance(closes):
    return round(min(closes[-10:]), 1), round(max(closes[-10:]), 1)


# ===== 策略（完全保留）=====
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

    if price < ma20 and not volume_strong:
        return "觀望（弱勢）", "-", "-", "0%"

    if price > resistance * 1.05:
        return "觀望（過熱區）", "-", "-", "0%"

    if breakout and confirm:
        if closes[-1] <= closes[-2]:
            return "觀望（假突破）", "-", "-", "0%"

    not_too_high = price < resistance * 1.03
    if volume_strong and momentum and price > ma5 and price > ma20 and not_too_high:
        return "進場🔥（主升）", round(price, 1), round(structure_low, 1), "100%"

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

    stop = min(structure_low, buy * 0.97)
    stop = min(stop, buy * 0.96)

    if stop >= buy:
        stop = buy * 0.97

    if (buy - stop) / buy > 0.08:
        return "觀望（風險過大）", "-", "-", "0%"

    if volume_strong and price > ma20:
        decision = "進場🔥（主升）"
        position = "100%"
    elif price > ma20:
        decision = "進場"
        position = "50%"
    else:
        decision = "觀望"
        position = "0%"

    return decision, round(buy, 1), round(stop, 1), position