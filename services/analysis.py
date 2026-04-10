# ===== 量能 =====
def volume_model(volumes, closes):
    vol = volumes[-1]
    total = sum(volumes[-10:])
    avg10 = total / 10 if total > 0 else 1
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


# ===== 趨勢 =====
def trend_model(price, ma5, ma20, closes, volumes):

    if closes[-2] < ma20 and price > ma20 and closes[-1] > closes[-2]:
        return "🚀轉強起漲"

    ma20_prev = sum(closes[-21:-1]) / 20
    slope = ma20 - ma20_prev

    recent_high = max(closes[-5:])
    prev_high = max(closes[-10:-5])
    recent_low = min(closes[-5:])
    prev_low = min(closes[-10:-5])

    higher_high = recent_high > prev_high
    higher_low = recent_low > prev_low

    resistance = max(closes[-20:])
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
    return round(min(closes[-20:]), 1), round(max(closes[-20:]), 1)


# ===== 結構確認 =====
def check_structure(closes, volumes):
    stop_falling = closes[-1] >= closes[-2] >= closes[-3]

    total = sum(volumes[-10:])
    avg10 = total / 10 if total > 0 else 1

    no_dump = volumes[-1] <= avg10 * 1.5

    structure_low = min(closes[-7:])
    hold_structure = closes[-1] >= structure_low

    return stop_falling and no_dump and hold_structure


# ===== 市場模型（優化版）=====
def market_model(closes, ma20):

    # 明確弱勢（下破+連跌）
    if closes[-1] < ma20 and closes[-1] < closes[-2] < closes[-3]:
        return "weak"

    return "normal"


# ===== 策略（最終優化版）=====
def strategy(price, ma5, ma20, closes, volumes):

    support, resistance = support_resistance(closes)

    # ===== 市場 =====
    market_trend = market_model(closes, ma20)

    if market_trend == "weak":
        return "觀望（市場偏弱）", "-", "-", "0%", "WAIT_AVOID", "HIGH"

    # ===== 基礎 =====
    prev_resistance = max(closes[-21:-1])
    breakout = price > prev_resistance

    avg10 = sum(volumes[-10:]) / 10 if sum(volumes[-10:]) > 0 else 1
    ratio = volumes[-1] / avg10

    momentum = price > closes[-2]
    structure_low = min(closes[-10:])

    score = 0

    # ===== 趨勢 =====
    score += 2 if price > ma20 else -3
    if price > ma5: score += 1
    if momentum: score += 1

    # ===== 量能 =====
    if ratio > 2:
        score += 2 if momentum else -3
    elif ratio > 1.5:
        score += 2
    elif ratio > 1.2:
        score += 1
    elif ratio < 0.7:
        score -= 1

    # ===== 結構 =====
    up_days = sum(1 for i in range(-5, 0) if closes[i] > closes[i-1])
    if up_days >= 4: score += 2
    elif up_days >= 3: score += 1

    if closes[-1] > max(closes[-5:-1]): score += 1
    if closes[-1] < min(closes[-5:-1]): score -= 2

    # ===== 🔥 補回 breakout =====
    if breakout and momentum and ratio > 1.3:
        score += 2

    if breakout and (not momentum or ratio < 1.2):
        score -= 3

    # ===== 🔥 confirm（關鍵）=====
    confirm = 0
    if price > ma20: confirm += 1
    if momentum: confirm += 1
    if ratio > 1.2: confirm += 1

    if confirm < 2 and score >= 4:
        score -= 2

    # ===== 壓力 =====
    if price > resistance * 0.97:
        return "觀望（接近壓力）", "-", "-", "0%", "WAIT_AVOID", "HIGH"

    # ===== 防追高 =====
    if price > ma5 * 1.05:
        return "觀望（追高風險）", "-", "-", "0%", "WAIT_AVOID", "HIGH"

    # ===== 過熱 =====
    if price > resistance * 1.08:
        return "觀望（過熱）", "-", "-", "0%", "WAIT_AVOID", "HIGH"

    decision_reason = "WAIT"

    # ===== 決策 =====
    if score >= 6:
        buy = price * 0.99
        stop = min(ma5, structure_low)
        decision_reason = "BREAK"

    elif score >= 4:
        if abs(price - ma5) / ma5 <= 0.03 and closes[-1] >= closes[-2]:
            buy = ma5
            stop = max(ma20 * 0.97, structure_low)
            decision_reason = "PULLBACK"
        else:
            return "觀望（未回踩）", "-", "-", "0%", "WAIT_PULLBACK", "MID"

    elif score >= 2:
        return "觀望（等待轉強）", "-", "-", "0%", "WAIT_TREND", "MID"

    else:
        return "觀望（弱勢）", "-", "-", "0%", "WAIT_AVOID", "HIGH"

    # ===== 結構 =====
    if not check_structure(closes, volumes):
        return "觀望（結構未確認）", "-", "-", "0%", "WAIT_AVOID", "HIGH"

    # ===== 風控 =====
    if stop >= buy:
        stop = buy * 0.97

    risk = (buy - stop) / buy

    if risk > 0.08:
        return "觀望（風險過大）", "-", "-", "0%", "WAIT_AVOID", "HIGH"

    reward = resistance - buy
    if reward <= 0:
        return "觀望（空間不足）", "-", "-", "0%", "WAIT_AVOID", "HIGH"

    rr = reward / (buy - stop)

    if rr < 1.2:
        return "觀望（報酬不足）", "-", "-", "0%", "WAIT_AVOID", "MID"

    # ===== 倉位 =====
    risk_per_trade = 0.02
    position = min(risk_per_trade / risk, 1.0)
    position_pct = int(position * 100)

    # ===== 風險等級 =====
    if risk > 0.06:
        risk_level = "HIGH"
    elif risk > 0.03:
        risk_level = "MID"
    else:
        risk_level = "LOW"

    # ===== 最終 =====
    if position_pct >= 70:
        decision = "進場🔥（強勢）"
    elif position_pct >= 40:
        decision = "進場（穩健）"
    else:
        decision = "試單（觀察）"

    return decision, round(buy,1), round(stop,1), f"{position_pct}%", decision_reason, risk_level