# ================================
# 🔥 analysis.py（FINAL v17.1｜STABLE PROFIT PATCH）
# ================================

# 🔒 VERSION LOCK
# - ✅ 完整保留 v17 所有策略分支
# - ❗不刪任何交易邏輯
# - ✅ 修正：RR 真實化（影響 strength）
# - ✅ 修正：momentum 改為趨勢加速
# - ✅ 強化：strong（必須爆量）
# - ✅ 強化：pre_breakout（收緊進場）
# - ✅ 強化：fake_break（更敏感）
# - ✅ 修正：stop（避免過遠/過近）
# ================================


# ===== 工具 =====
def avg(arr):
    return sum(arr) / len(arr) if arr else 0


# ================================
# 🔥 倉位（原版保留）
# ================================
def base_position(market, trend, structure, volume):

    pos = 0

    if market == "STRONG":
        pos += 0.3
    elif market == "CHOPPY":
        pos += 0.2
    elif market == "NORMAL":
        pos += 0.1

    if trend == "UP":
        pos += 0.2

    if structure == "STRONG":
        pos += 0.2

    if volume == "STRONG":
        pos += 0.2
    elif volume == "NORMAL":
        pos += 0.1

    return round(min(pos, 0.5), 2)


# ================================
# 🔥 行動轉換（原版）
# ================================
def action_mapper(decision, position):

    if decision == "BUY":
        return {"action": round(position, 2), "action_type": "BUY"}

    if decision == "NO_TRADE":
        return {"action": -1.0, "action_type": "SELL_ALL"}

    return {"action": 0.0, "action_type": "HOLD"}


# ================================
# 🔥 統一輸出（核心不可動）
# ================================
def build_result(**kwargs):

    decision = kwargs.get("decision", "WAIT")
    position = kwargs.get("position", 0)

    action_data = action_mapper(decision, position)

    if decision == "NO_TRADE":
        position = 0

    result = {
        "decision": decision,
        "decision_type": kwargs.get("decision_type", "none"),
        "buy": kwargs.get("buy"),
        "stop": kwargs.get("stop"),
        "position": round(position, 2),
        "action": action_data["action"],
        "action_type": action_data["action_type"],
        "market_score": kwargs.get("market_score"),
        "market_grade": kwargs.get("market_grade"),
        "trend": kwargs.get("trend"),
        "structure_state": kwargs.get("structure_state"),
        "volume_state": kwargs.get("volume_state"),
        "rr": kwargs.get("rr", 0),
    }

    result["strength"] = strength_score(result)

    return result


# ================================
# 🔥 決策分數（v17 保留）
# ================================
def decision_score(market, trend, structure, volume):

    score = 0

    if market == "STRONG":
        score += 4
    elif market == "NORMAL":
        score += 1
    elif market == "WEAK":
        score -= 4

    if trend == "UP":
        score += 3
    elif trend == "DOWN":
        score -= 4

    if structure == "STRONG":
        score += 2
    elif structure == "WEAK":
        score -= 2

    if volume == "STRONG":
        score += 2
    elif volume == "DISTRIBUTION":
        score -= 3
    elif volume == "WEAK":
        score -= 1

    return score


# ================================
# 🔥 強度分數（使用真實 RR）
# ================================
def strength_score(result):

    score = 0

    if result.get("decision") == "BUY":
        score += 5
    elif result.get("decision") == "WAIT":
        score += 2

    score += (result.get("market_score") or 0) * 0.5
    score += (result.get("rr") or 0)

    if result.get("trend") == "UP":
        score += 1
    if result.get("structure_state") == "STRONG":
        score += 1
    if result.get("volume_state") == "STRONG":
        score += 1

    return round(score, 2)


# ================================
# 🔥 市場評分（保留）
# ================================
def market_score(market, trend, structure, volume, momentum):

    score = 0

    if market == "STRONG":
        score += 3
    elif market == "CHOPPY":
        score += 0
    elif market == "WEAK":
        score -= 3

    if trend == "UP":
        score += 3
    elif trend == "DOWN":
        score -= 3

    if structure == "STRONG":
        score += 2
    elif structure == "WEAK":
        score -= 2

    if volume == "STRONG":
        score += 2
    elif volume == "DISTRIBUTION":
        score -= 3
    elif volume == "WEAK":
        score -= 1

    if momentum == "ACCELERATING":
        score += 2
    else:
        score -= 1

    return score


def market_grade(score):
    if score >= 11:
        return "A+"
    elif score >= 8:
        return "A"
    elif score >= 5:
        return "B"
    elif score >= 2:
        return "C"
    return "D"


# ================================
# 🔥 市場判斷（保留）
# ================================
def market_signal(closes, ma20):

    momentum = closes[-1] - closes[-3]
    above_ma20_ratio = sum(1 for c in closes[-5:] if c > ma20) / 5

    if closes[-1] < ma20 and momentum < 0 and above_ma20_ratio < 0.4:
        return "WEAK"

    if (
        (max(closes[-10:]) - min(closes[-10:])) / closes[-1] < 0.03
        and abs(momentum) < closes[-1] * 0.01
    ):
        return "CHOPPY"

    if (
        closes[-1] > ma20
        and closes[-1] > closes[-3]
        and above_ma20_ratio > 0.6
    ):
        return "STRONG"

    return "NORMAL"


# ================================
# 🔥 其他訊號（保留）
# ================================
def trend_signal(price, ma5, ma20):
    if price > ma5 > ma20:
        return "UP"
    if price < ma20:
        return "DOWN"
    return "SIDE"


def volume_signal(volumes):
    avg10 = avg(volumes[-10:])
    ratio = volumes[-1] / avg10 if avg10 else 1

    if avg10 < 1:
        return "WEAK"

    if ratio > 1.5 and volumes[-1] > volumes[-2]:
        return "STRONG"

    if ratio > 1.5 and volumes[-1] < volumes[-2]:
        return "DISTRIBUTION"

    if ratio < 0.8:
        return "WEAK"

    return "NORMAL"


def structure_state(closes):
    score = 0
    if closes[-1] > closes[-2]:
        score += 1
    if closes[-2] > closes[-3]:
        score += 1
    if closes[-1] > avg(closes[-5:]):
        score += 1

    if score >= 3:
        return "STRONG"
    elif score == 2:
        return "NORMAL"
    return "WEAK"


# ================================
# 🔥 支撐壓力
# ================================
def support_resistance(closes):
    return min(closes[-20:]), max(closes[-20:-3])


# ================================
# 🔥 突破 / 假突破（強化）
# ================================
def event_breakout(price, closes, resistance, volumes):
    avg5 = avg(volumes[-5:])
    return (
        closes[-1] > resistance * 1.01
        and volumes[-1] > avg5 * 1.3
        and volumes[-1] > volumes[-2]
    )


def edge_fake_breakout(closes):
    prev_high = max(closes[-21:-1])
    return closes[-2] > prev_high and closes[-1] < prev_high * 0.985


# ================================
# 🔥 主升段（強化：必須爆量）
# ================================
def strong_follow(closes, resistance, volume, structure, trend):

    return (
        closes[-1] > resistance
        and closes[-1] > closes[-2] > closes[-3]
        and volume == "STRONG"
        and structure == "STRONG"
        and trend == "UP"
    )


# ================================
# 🔥 strategy（v17.1）
# ================================
def strategy(price, ma5, ma20, closes, volumes):

    support, resistance = support_resistance(closes)

    market = market_signal(closes, ma20)
    trend = trend_signal(price, ma5, ma20)
    volume = volume_signal(volumes)
    structure = structure_state(closes)

    # 🔥 momentum（改進）
    momentum = "ACCELERATING" if avg(closes[-3:]) > avg(closes[-6:-3]) else "DECELERATING"

    m_score = market_score(market, trend, structure, volume, momentum)
    m_grade = market_grade(m_score)

    score = decision_score(market, trend, structure, volume)

    fake_break = edge_fake_breakout(closes)
    base_pos = base_position(market, trend, structure, volume)

    # 🔥 RR（新增）
    try:
        stop_candidate = min(ma5, avg(closes[-3:]))
        rr = (price - stop_candidate) / price
    except:
        rr = 0

    # 🔥 風控
    if market == "WEAK" or trend == "DOWN":
        return build_result(decision="NO_TRADE", position=0,
            market_score=m_score, market_grade=m_grade,
            trend=trend, volume_state=volume, structure_state=structure, rr=rr)

    if fake_break:
        return build_result(decision="WAIT", position=0,
            market_score=m_score, market_grade=m_grade,
            trend=trend, volume_state=volume, structure_state=structure, rr=rr)

    if score <= -3:
        return build_result(decision="NO_TRADE", position=0,
            market_score=m_score, market_grade=m_grade,
            trend=trend, volume_state=volume, structure_state=structure, rr=rr)

    # 🔥 主升段
    if strong_follow(closes, resistance, volume, structure, trend) and score >= 6:

        pos = min(max(base_pos, 0.7) + 0.1, 0.9)

        return build_result(decision="BUY", decision_type="strong",
            buy=price, stop=stop_candidate, position=pos,
            market_score=m_score, market_grade=m_grade,
            trend=trend, volume_state=volume, structure_state=structure, rr=rr)

    # 🔥 確認突破
    if event_breakout(price, closes, resistance, volumes) and score >= 4:

        pos = max(base_pos, 0.5)
        if score >= 6:
            pos = max(pos, 0.7)

        return build_result(decision="BUY", decision_type="add_on",
            buy=price, stop=stop_candidate, position=pos,
            market_score=m_score, market_grade=m_grade,
            trend=trend, volume_state=volume, structure_state=structure, rr=rr)

    # 🔥 試單（收緊）
    if (
        trend == "UP"
        and volume != "WEAK"
        and structure != "WEAK"
        and price > resistance * 0.985
        and score >= 2
    ):
        pos = max(base_pos, 0.2)

        return build_result(decision="BUY", decision_type="pre_breakout",
            buy=price, stop=stop_candidate, position=pos,
            market_score=m_score, market_grade=m_grade,
            trend=trend, volume_state=volume, structure_state=structure, rr=rr)

    return build_result(decision="WAIT", position=0,
        market_score=m_score, market_grade=m_grade,
        trend=trend, volume_state=volume, structure_state=structure, rr=rr)


# ================================
# 🔥 最強股（保留）
# ================================
def pick_best_stock(results_dict):

    best_name = None
    best_score = -999

    for name, result in results_dict.items():
        score = result.get("strength", 0)

        if score > best_score:
            best_score = score
            best_name = name

    return best_name, best_score