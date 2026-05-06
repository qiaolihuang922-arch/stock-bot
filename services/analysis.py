# ================================
# 🔥 analysis.py（FINAL v17.4｜REAL RR + REAL TURN）
# ================================

# 🔒 VERSION LOCK
# - ✅ 保留 v17.3 所有主結構
# - ✅ 修正：RR 真正 reward/risk
# - ✅ 修正：TURN 必須結構轉強
# - ✅ 修正：CONFIRM 必須是真 breakout continuation
# - ✅ 修正：breakout threshold 全系統統一
# - ✅ 修正：strong_follow 允許強勢整理
# - ✅ 修正：volume 分級
# - ✅ 新增：EXTENDED（過熱）
# - ✅ 保持：原有 BUY / WAIT / NO_TRADE
# ================================


# ================================
# 🔥 常數（v17.4）
# ================================
BREAKOUT_THRESHOLD = 0.005
MIN_RR = 1.2


# ================================
# 🔥 工具
# ================================
def avg(arr):
    return sum(arr) / len(arr) if arr else 0


# ================================
# 🔥 倉位（保留）
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

    # 🔥 v17.4 volume 分級
    if volume == "EXPLOSIVE":
        pos += 0.25
    elif volume == "STRONG":
        pos += 0.2
    elif volume == "NORMAL":
        pos += 0.1

    return round(min(pos, 0.6), 2)


# ================================
# 🔥 行動轉換（保留）
# ================================
def action_mapper(decision, position):

    if decision == "BUY":
        return {
            "action": round(position, 2),
            "action_type": "BUY"
        }

    if decision == "NO_TRADE":
        return {
            "action": -1.0,
            "action_type": "SELL_ALL"
        }

    return {
        "action": 0.0,
        "action_type": "HOLD"
    }


# ================================
# 🔥 build_result（v17.4）
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

        # 🔥 v17.4
        "entry_stage": kwargs.get("entry_stage"),
        "extended": kwargs.get("extended", False),
    }

    result["strength"] = strength_score(result)

    return result


# ================================
# 🔥 decision_score（保留）
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

    if volume in ["STRONG", "EXPLOSIVE"]:
        score += 2

    elif volume == "DISTRIBUTION":
        score -= 3

    elif volume == "WEAK":
        score -= 1

    return score


# ================================
# 🔥 strength_score（v17.4）
# ================================
def strength_score(result):

    score = 0

    score += (result.get("market_score") or 0) * 0.6

    score += min(result.get("rr", 0), 3)

    if result.get("decision") == "BUY":
        score += 2

    if result.get("trend") == "UP":
        score += 1

    if result.get("structure_state") == "STRONG":
        score += 1

    if result.get("volume_state") in ["STRONG", "EXPLOSIVE"]:
        score += 1

    if result.get("entry_stage") == "CONFIRM":
        score += 1

    if result.get("extended"):
        score -= 2

    return round(score, 2)


# ================================
# 🔥 market_score（保留）
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

    if volume in ["STRONG", "EXPLOSIVE"]:
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


# ================================
# 🔥 market_grade（保留）
# ================================
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
# 🔥 market_signal（v17.4）
# ================================
def market_signal(closes, ma20):

    momentum = closes[-1] - closes[-3]

    above_ma20_ratio = (
        sum(1 for c in closes[-5:] if c > ma20) / 5
    )

    # 🔥 WEAK
    if (
        closes[-1] < ma20
        and momentum < 0
        and above_ma20_ratio < 0.4
    ):
        return "WEAK"

    # 🔥 STRONG
    if (
        closes[-1] > ma20
        and closes[-1] > closes[-3]
        and above_ma20_ratio > 0.6
    ):
        return "STRONG"

    # 🔥 CHOPPY
    if (
        (max(closes[-10:]) - min(closes[-10:]))
        / closes[-1] < 0.03
        and abs(momentum) < closes[-1] * 0.01
    ):
        return "CHOPPY"

    return "NORMAL"


# ================================
# 🔥 trend_signal（保留）
# ================================
def trend_signal(price, ma5, ma20):

    if price > ma5 > ma20:
        return "UP"

    if price < ma20:
        return "DOWN"

    return "SIDE"


# ================================
# 🔥 volume_signal（v17.4）
# ================================
def volume_signal(volumes):

    avg10 = avg(volumes[-10:])

    ratio = volumes[-1] / avg10 if avg10 else 1

    if ratio < 0.7:
        return "WEAK"

    if ratio < 1.0:
        return "NORMAL"

    if ratio < 1.5:
        return "STRONG"

    if ratio >= 1.5:
        return "EXPLOSIVE"

    return "NORMAL"


# ================================
# 🔥 structure_state（v17.4）
# ================================
def structure_state(closes, ma5, ma20):

    score = 0

    if closes[-1] > closes[-2]:
        score += 1

    if ma5 > ma20:
        score += 1

    if closes[-1] > avg(closes[-5:]):
        score += 1

    if closes[-2] > closes[-3]:
        score += 1

    if score >= 4:
        return "STRONG"

    elif score >= 2:
        return "NORMAL"

    return "WEAK"


# ================================
# 🔥 support_resistance（保留）
# ================================
def support_resistance(closes):

    support = min(closes[-20:])

    resistance = max(closes[-20:-3])

    return support, resistance


# ================================
# 🔥 breakout（v17.4）
# ================================
def is_breakout(close, resistance):

    return close > resistance * (1 + BREAKOUT_THRESHOLD)


# ================================
# 🔥 event_breakout（v17.4）
# ================================
def event_breakout(closes, resistance, volumes):

    avg5 = avg(volumes[-5:])

    return (
        is_breakout(closes[-1], resistance)
        and volumes[-1] > avg5 * 1.2
    )


# ================================
# 🔥 fake breakout（保留）
# ================================
def edge_fake_breakout(closes):

    prev_high = max(closes[-21:-1])

    return (
        closes[-2] > prev_high
        and closes[-1] < prev_high * 0.985
    )


# ================================
# 🔥 strong_follow（v17.4）
# ================================
def strong_follow(
    closes,
    resistance,
    volume,
    structure,
    trend
):

    return (

        is_breakout(closes[-1], resistance)

        # 🔥 v17.4：允許強勢整理
        and closes[-1] >= closes[-2] * 0.995

        and volume in ["STRONG", "EXPLOSIVE"]

        and structure == "STRONG"

        and trend == "UP"
    )


# ================================
# 🔥 entry_stage（v17.4）
# ================================
def detect_entry_stage(
    closes,
    ma5,
    resistance,
    volume
):

    # 🔥 真 breakout continuation
    prev_breakout = is_breakout(
        closes[-2],
        resistance
    )

    # 🔥 CONFIRM
    if (
        prev_breakout
        and closes[-1] > closes[-2]
    ):
        return "CONFIRM"

    # 🔥 TURN（真正轉強）
    if (
        closes[-1] > closes[-2]
        and closes[-1] > ma5
        and volume != "WEAK"
        and closes[-1] > avg(closes[-3:])
    ):
        return "TURN"

    return "REJECT"


# ================================
# 🔥 RR（v17.4 真 RR）
# ================================
def calc_rr(price, stop, resistance):

    risk = price - stop

    if risk <= 0:
        return 0

    target = resistance * 1.08

    reward = target - price

    if reward <= 0:
        return 0

    return round(reward / risk, 2)


# ================================
# 🔥 EXTENDED（v17.4）
# ================================
def is_extended(price, ma20):

    return price > ma20 * 1.15


# ================================
# 🔥 strategy（v17.4）
# ================================
def strategy(price, ma5, ma20, closes, volumes):

    support, resistance = support_resistance(closes)

    market = market_signal(closes, ma20)

    trend = trend_signal(price, ma5, ma20)

    volume = volume_signal(volumes)

    structure = structure_state(
        closes,
        ma5,
        ma20
    )

    momentum = (
        "ACCELERATING"
        if avg(closes[-3:]) > avg(closes[-6:-3])
        else "DECELERATING"
    )

    m_score = market_score(
        market,
        trend,
        structure,
        volume,
        momentum
    )

    m_grade = market_grade(m_score)

    score = decision_score(
        market,
        trend,
        structure,
        volume
    )

    fake_break = edge_fake_breakout(closes)

    base_pos = base_position(
        market,
        trend,
        structure,
        volume
    )

    # ================================
    # 🔥 stop / rr
    # ================================
    stop_candidate = min(
        ma5,
        avg(closes[-3:])
    )

    rr = calc_rr(
        price,
        stop_candidate,
        resistance
    )

    # ================================
    # 🔥 entry_stage
    # ================================
    entry_stage = detect_entry_stage(
        closes,
        ma5,
        resistance,
        volume
    )

    # ================================
    # 🔥 EXTENDED
    # ================================
    extended = is_extended(
        price,
        ma20
    )

    # ================================
    # 🔥 風控
    # ================================
    if market == "WEAK" or trend == "DOWN":

        return build_result(
            decision="NO_TRADE",
            position=0,

            market_score=m_score,
            market_grade=m_grade,

            trend=trend,

            volume_state=volume,
            structure_state=structure,

            rr=rr,

            entry_stage=entry_stage,
            extended=extended
        )

    # ================================
    # 🔥 fake breakout
    # ================================
    if fake_break:

        return build_result(
            decision="WAIT",
            position=0,

            market_score=m_score,
            market_grade=m_grade,

            trend=trend,

            volume_state=volume,
            structure_state=structure,

            rr=rr,

            entry_stage=entry_stage,
            extended=extended
        )

    # ================================
    # 🔥 REJECT
    # ================================
    if entry_stage == "REJECT":

        return build_result(
            decision="WAIT",
            position=0,

            market_score=m_score,
            market_grade=m_grade,

            trend=trend,

            volume_state=volume,
            structure_state=structure,

            rr=rr,

            entry_stage=entry_stage,
            extended=extended
        )

    # ================================
    # 🔥 RR filter
    # ================================
    if rr < MIN_RR:

        return build_result(
            decision="WAIT",
            position=0,

            market_score=m_score,
            market_grade=m_grade,

            trend=trend,

            volume_state=volume,
            structure_state=structure,

            rr=rr,

            entry_stage=entry_stage,
            extended=extended
        )

    # ================================
    # 🔥 過熱
    # ================================
    if extended:

        return build_result(
            decision="WAIT",
            position=0,

            market_score=m_score,
            market_grade=m_grade,

            trend=trend,

            volume_state=volume,
            structure_state=structure,

            rr=rr,

            entry_stage=entry_stage,
            extended=extended
        )

    # ================================
    # 🔥 主升段
    # ================================
    if (
        strong_follow(
            closes,
            resistance,
            volume,
            structure,
            trend
        )
        and score >= 6
    ):

        pos = min(
            max(base_pos, 0.7),
            0.9
        )

        # 🔥 TURN 限倉
        if entry_stage == "TURN":
            pos = min(pos, 0.4)

        # 🔥 RR 加成
        if rr > 2:
            pos += 0.1

        return build_result(
            decision="BUY",
            decision_type="strong",

            buy=price,
            stop=stop_candidate,

            position=pos,

            market_score=m_score,
            market_grade=m_grade,

            trend=trend,

            volume_state=volume,
            structure_state=structure,

            rr=rr,

            entry_stage=entry_stage,
            extended=extended
        )

    # ================================
    # 🔥 breakout
    # ================================
    if (
        event_breakout(
            closes,
            resistance,
            volumes
        )
        and score >= 4
    ):

        pos = max(base_pos, 0.5)

        if entry_stage == "TURN":
            pos = min(pos, 0.4)

        return build_result(
            decision="BUY",
            decision_type="add_on",

            buy=price,
            stop=stop_candidate,

            position=pos,

            market_score=m_score,
            market_grade=m_grade,

            trend=trend,

            volume_state=volume,
            structure_state=structure,

            rr=rr,

            entry_stage=entry_stage,
            extended=extended
        )

    # ================================
    # 🔥 pre breakout
    # ================================
    if (
        trend == "UP"
        and volume != "WEAK"
        and structure != "WEAK"
        and price > resistance * 0.985
        and score >= 2
    ):

        pos = max(base_pos, 0.2)

        if entry_stage == "TURN":
            pos = min(pos, 0.3)

        return build_result(
            decision="BUY",
            decision_type="pre_breakout",

            buy=price,
            stop=stop_candidate,

            position=pos,

            market_score=m_score,
            market_grade=m_grade,

            trend=trend,

            volume_state=volume,
            structure_state=structure,

            rr=rr,

            entry_stage=entry_stage,
            extended=extended
        )

    # ================================
    # 🔥 default
    # ================================
    return build_result(
        decision="WAIT",
        position=0,

        market_score=m_score,
        market_grade=m_grade,

        trend=trend,

        volume_state=volume,
        structure_state=structure,

        rr=rr,

        entry_stage=entry_stage,
        extended=extended
    )


# ================================
# 🔥 最強股（v17.4）
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