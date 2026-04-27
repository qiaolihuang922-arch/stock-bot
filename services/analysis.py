# ================================
# 🔥 analysis.py（FINAL v15.3｜LOCKED｜主升段強化版）
# ================================

# 🔒 VERSION LOCK（重要）
# - 基於 v15.1
# - ❗未刪除任何原有策略邏輯
# - ✅ 強化：market（更嚴格）
# - ✅ 新增：strong（真強段）
# - ✅ 完整三階段：試單 → 確認 → 主升段
# ================================


# ===== 工具 =====
def avg(arr):
    return sum(arr) / len(arr) if arr else 0


# ================================
# 🔥 倉位（原版）
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
# 🔥 行動引擎（原版）
# ================================
def action_mapper(decision, position):

    if decision == "BUY":
        return {"action": round(position, 2), "action_type": "BUY"}

    if decision == "NO_TRADE":
        return {"action": -1.0, "action_type": "SELL_ALL"}

    return {"action": 0.0, "action_type": "HOLD"}


# ================================
# 🔥 權重模型（原版）
# ================================
def decision_score(market, trend, structure, volume):

    score = 0

    if market == "STRONG":
        score += 3
    elif market == "NORMAL":
        score += 1
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
        score -= 2

    return score


# ================================
# 🔥 強度分數（原版）
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
# 🔥 市場評分（🔥拉開差距）
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
# 🔥 市場判斷（🔥更嚴格）
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
# 🔥 其他訊號（原版）
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
# 🔥 壓力 / 事件（原版）
# ================================
def support_resistance(closes):
    return min(closes[-20:]), max(closes[-20:-3])


def event_breakout(price, closes, resistance, volumes):
    avg5 = avg(volumes[-5:])
    return (
        closes[-1] > resistance * 1.01
        and volumes[-1] > avg5 * 1.3
        and volumes[-1] > volumes[-2]
    )


def edge_fake_breakout(closes):
    prev_high = max(closes[-21:-1])
    return closes[-2] > prev_high and closes[-1] < prev_high * 0.98


# ================================
# 🔥 真強判斷（🔥新增核心）
# ================================
def strong_follow(closes, resistance, volume):

    return (
        closes[-1] > resistance
        and closes[-1] > closes[-2] > closes[-3]
        and volume in ["STRONG", "NORMAL"]
    )


# ================================
# 🔥 strategy（🔥三階段完成）
# ================================
def strategy(price, ma5, ma20, closes, volumes):

    support, resistance = support_resistance(closes)

    market = market_signal(closes, ma20)
    trend = trend_signal(price, ma5, ma20)
    volume = volume_signal(volumes)
    structure = structure_state(closes)

    momentum = "ACCELERATING" if closes[-1] > closes[-3] else "DECELERATING"

    m_score = market_score(market, trend, structure, volume, momentum)
    m_grade = market_grade(m_score)

    score = decision_score(market, trend, structure, volume)

    fake_break = edge_fake_breakout(closes)
    base_pos = base_position(market, trend, structure, volume)

    if fake_break:
        return build_result(
            decision="WAIT",
            position=0,
            market_score=m_score,
            market_grade=m_grade,
            trend=trend,
            volume_state=volume,
            structure_state=structure
        )

    if score <= -3:
        return build_result(
            decision="NO_TRADE",
            position=0,
            market_score=m_score,
            market_grade=m_grade,
            trend=trend,
            volume_state=volume,
            structure_state=structure
        )

    # 🔥 真強（最高優先）
    if strong_follow(closes, resistance, volume) and score >= 6:

        pos = max(base_pos, 0.7)
        pos = min(pos + 0.1, 0.9)

        return build_result(
            decision="BUY",
            decision_type="strong",
            buy=price,
            stop=min(ma5, support),
            position=pos,
            market_score=m_score,
            market_grade=m_grade,
            trend=trend,
            volume_state=volume,
            structure_state=structure
        )

    # 🔥 確認
    if event_breakout(price, closes, resistance, volumes) and score >= 4:

        pos = max(base_pos, 0.5)

        if score >= 6:
            pos = max(pos, 0.7)

        return build_result(
            decision="BUY",
            decision_type="add_on",
            buy=price,
            stop=min(ma5, support),
            position=pos,
            market_score=m_score,
            market_grade=m_grade,
            trend=trend,
            volume_state=volume,
            structure_state=structure
        )

    # 🔥 試單
    if trend == "UP" and volume != "WEAK" and price > resistance * 0.97 and score >= 2:

        pos = max(base_pos, 0.2)

        return build_result(
            decision="BUY",
            decision_type="pre_breakout",
            buy=price,
            stop=min(ma5, support),
            position=pos,
            market_score=m_score,
            market_grade=m_grade,
            trend=trend,
            volume_state=volume,
            structure_state=structure
        )

    return build_result(
        decision="WAIT",
        position=0,
        market_score=m_score,
        market_grade=m_grade,
        trend=trend,
        volume_state=volume,
        structure_state=structure
    )


# ================================
# 🔥 最強股（原版）
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