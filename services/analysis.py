# ================================
# 🔥 analysis.py（FINAL v17.5｜REAL DAY1 / DAY2 STATE MACHINE）
# ================================

# 🔒 VERSION LOCK
# - ✅ 保留 v17.4 所有主架構
# - ✅ 新增：真正 Day1 / Day2（fresh breakout）
# - ✅ 新增：previous breakout comparison
# - ✅ 新增：BREAKOUT_FAIL
# - ✅ 新增：minimum stop distance（避免 RR 爆炸）
# - ✅ 新增：setup RR 分級
# - ✅ 新增：volume-price lifecycle
# - ✅ 新增：WAIT state
# - ✅ 修正：EXTENDED 不再禁止交易（只降倉）
# - ✅ 修正：NO_TRADE 不再 SELL_ALL
# - ✅ 修正：structure 不再只看短線紅K
# - ✅ 保持：BUY / WAIT / NO_TRADE 主結構
# ================================


# ================================
# 🔥 常數（v17.5）
# ================================
BREAKOUT_THRESHOLD = 0.005

MIN_RR_BREAKOUT = 1.5
MIN_RR_PREBREAK = 1.0
MIN_RR_STRONG = 2.0

MIN_STOP_BUFFER = 0.015


# ================================
# 🔥 工具
# ================================
def avg(arr):
    return sum(arr) / len(arr) if arr else 0


# ================================
# 🔥 倉位
# ================================
def base_position(
    market,
    trend,
    structure,
    volume
):

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

    if volume == "EXPLOSIVE":
        pos += 0.25

    elif volume == "STRONG":
        pos += 0.2

    elif volume == "NORMAL":
        pos += 0.1

    return round(min(pos, 0.6), 2)


# ================================
# 🔥 行動轉換（v17.5）
# ================================
def action_mapper(decision, position):

    # 🔥 BUY
    if decision == "BUY":

        return {
            "action": round(position, 2),
            "action_type": "BUY"
        }

    # 🔥 EXIT（真正離場）
    if decision == "EXIT":

        return {
            "action": -1.0,
            "action_type": "SELL_ALL"
        }

    # 🔥 WAIT / HOLD
    return {
        "action": 0.0,
        "action_type": "HOLD"
    }


# ================================
# 🔥 build_result
# ================================
def build_result(**kwargs):

    decision = kwargs.get("decision", "WAIT")

    position = kwargs.get("position", 0)

    action_data = action_mapper(
        decision,
        position
    )

    if decision == "EXIT":
        position = 0

    result = {

        "decision": decision,

        "decision_type": kwargs.get(
            "decision_type",
            "none"
        ),

        "wait_reason": kwargs.get(
            "wait_reason"
        ),

        "buy": kwargs.get("buy"),

        "stop": kwargs.get("stop"),

        "position": round(position, 2),

        "action": action_data["action"],

        "action_type": action_data[
            "action_type"
        ],

        "market_score": kwargs.get(
            "market_score"
        ),

        "market_grade": kwargs.get(
            "market_grade"
        ),

        "trend": kwargs.get("trend"),

        "structure_state": kwargs.get(
            "structure_state"
        ),

        "volume_state": kwargs.get(
            "volume_state"
        ),

        "volume_price_state": kwargs.get(
            "volume_price_state"
        ),

        "rr": kwargs.get("rr", 0),

        # 🔥 v17.5 state machine
        "entry_stage": kwargs.get(
            "entry_stage"
        ),

        "extended": kwargs.get(
            "extended",
            False
        ),

        "fresh_breakout": kwargs.get(
            "fresh_breakout",
            False
        ),

        "breakout_fail": kwargs.get(
            "breakout_fail",
            False
        )
    }

    result["strength"] = strength_score(
        result
    )

    return result


# ================================
# 🔥 decision_score
# ================================
def decision_score(
    market,
    trend,
    structure,
    volume
):

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

    if volume in [
        "STRONG",
        "EXPLOSIVE"
    ]:
        score += 2

    elif volume == "DISTRIBUTION":
        score -= 3

    elif volume == "WEAK":
        score -= 1

    return score


# ================================
# 🔥 strength_score（v17.5）
# ================================
def strength_score(result):

    score = 0

    score += (
        result.get("market_score", 0)
        * 0.6
    )

    score += min(
        result.get("rr", 0),
        3
    )

    if result.get("trend") == "UP":
        score += 1

    if (
        result.get("structure_state")
        == "STRONG"
    ):
        score += 1

    if (
        result.get("volume_state")
        in ["STRONG", "EXPLOSIVE"]
    ):
        score += 1

    # 🔥 真 Day1
    if result.get("entry_stage") == "BREAKOUT_DAY1":
        score += 2

    # 🔥 真 Day2
    elif result.get("entry_stage") == "CONFIRM_DAY2":
        score += 1.5

    # 🔥 fail
    if result.get("breakout_fail"):
        score -= 4

    return round(score, 2)


# ================================
# 🔥 market_score
# ================================
def market_score(
    market,
    trend,
    structure,
    volume,
    momentum
):

    score = 0

    if market == "STRONG":
        score += 3

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

    if volume in [
        "STRONG",
        "EXPLOSIVE"
    ]:
        score += 2

    elif volume == "WEAK":
        score -= 1

    if momentum == "ACCELERATING":
        score += 2

    else:
        score -= 1

    return score


# ================================
# 🔥 market_grade
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
# 🔥 market_signal
# ================================
def market_signal(closes, ma20):

    momentum = closes[-1] - closes[-3]

    above_ma20_ratio = (
        sum(
            1 for c in closes[-5:]
            if c > ma20
        ) / 5
    )

    if (
        closes[-1] < ma20
        and momentum < 0
        and above_ma20_ratio < 0.4
    ):
        return "WEAK"

    if (
        closes[-1] > ma20
        and closes[-1] > closes[-3]
        and above_ma20_ratio > 0.6
    ):
        return "STRONG"

    return "NORMAL"


# ================================
# 🔥 trend_signal
# ================================
def trend_signal(
    price,
    ma5,
    ma20
):

    if price > ma5 > ma20:
        return "UP"

    if price < ma20:
        return "DOWN"

    return "SIDE"


# ================================
# 🔥 volume_signal（v17.5）
# ================================
def volume_signal(volumes):

    avg10 = avg(volumes[-10:])

    ratio = (
        volumes[-1] / avg10
        if avg10 else 1
    )

    if ratio < 0.7:
        return "WEAK"

    if ratio < 1.0:
        return "NORMAL"

    if ratio < 1.5:
        return "STRONG"

    return "EXPLOSIVE"


# ================================
# 🔥 volume_price_state（新增）
# ================================
def volume_price_state(
    closes,
    volumes
):

    avg10 = avg(volumes[-10:])

    ratio = (
        volumes[-1] / avg10
        if avg10 else 1
    )

    price_up = (
        closes[-1] > closes[-2]
    )

    # 🔥 爆量上漲
    if ratio > 1.5 and price_up:
        return "EXPANSION"

    # 🔥 爆量不漲
    if ratio > 1.5 and not price_up:
        return "DISTRIBUTION"

    # 🔥 縮量整理
    if ratio < 0.8:
        return "COILING"

    return "NORMAL"


# ================================
# 🔥 structure_state（v17.5）
# ================================
def structure_state(
    closes,
    ma5,
    ma20
):

    score = 0

    # 🔥 higher low
    if min(closes[-3:]) > min(closes[-6:-3]):
        score += 1

    # 🔥 ma alignment
    if ma5 > ma20:
        score += 1

    # 🔥 above average
    if closes[-1] > avg(closes[-5:]):
        score += 1

    # 🔥 above ma20
    if closes[-1] > ma20:
        score += 1

    if score >= 4:
        return "STRONG"

    elif score >= 2:
        return "NORMAL"

    return "WEAK"


# ================================
# 🔥 support_resistance
# ================================
def support_resistance(closes):

    support = min(closes[-20:])

    resistance = max(closes[-20:-3])

    return support, resistance


# ================================
# 🔥 breakout
# ================================
def is_breakout(
    close,
    resistance
):

    return (
        close >
        resistance * (
            1 + BREAKOUT_THRESHOLD
        )
    )


# ================================
# 🔥 fresh breakout（新增）
# ================================
def is_fresh_breakout(
    closes,
    resistance
):

    today = is_breakout(
        closes[-1],
        resistance
    )

    yesterday = is_breakout(
        closes[-2],
        resistance
    )

    return today and not yesterday


# ================================
# 🔥 breakout fail（新增）
# ================================
def breakout_fail(
    closes,
    resistance
):

    yesterday_breakout = is_breakout(
        closes[-2],
        resistance
    )

    today_fail = (
        closes[-1] < resistance
    )

    return (
        yesterday_breakout
        and today_fail
    )


# ================================
# 🔥 fake breakout
# ================================
def edge_fake_breakout(closes):

    prev_high = max(
        closes[-21:-1]
    )

    return (
        closes[-2] > prev_high
        and closes[-1] < prev_high * 0.985
    )


# ================================
# 🔥 strong_follow
# ================================
def strong_follow(
    closes,
    resistance,
    volume,
    structure,
    trend
):

    return (

        is_breakout(
            closes[-1],
            resistance
        )

        and closes[-1]
        >= closes[-2] * 0.995

        and volume in [
            "STRONG",
            "EXPLOSIVE"
        ]

        and structure == "STRONG"

        and trend == "UP"
    )


# ================================
# 🔥 detect_entry_stage（v17.5 核心）
# ================================
def detect_entry_stage(
    closes,
    ma5,
    resistance,
    volume
):

    # ================================
    # 🔥 真 Day1
    # ================================
    if is_fresh_breakout(
        closes,
        resistance
    ):
        return "BREAKOUT_DAY1"

    # ================================
    # 🔥 真 Day2
    # ================================
    yesterday_breakout = is_breakout(
        closes[-2],
        resistance
    )

    if (
        yesterday_breakout
        and closes[-1] > closes[-2]
        and closes[-1] > resistance
    ):
        return "CONFIRM_DAY2"

    # ================================
    # 🔥 TURN
    # ================================
    if (
        closes[-1] > closes[-2]
        and closes[-1] > ma5
        and volume != "WEAK"
        and closes[-1]
        > avg(closes[-3:])
    ):
        return "TURN"

    return "REJECT"


# ================================
# 🔥 calc_rr（v17.5）
# ================================
def calc_rr(
    price,
    stop,
    resistance,
    setup_type="breakout"
):

    # 🔥 minimum stop
    min_risk = (
        price * MIN_STOP_BUFFER
    )

    raw_risk = price - stop

    risk = max(
        raw_risk,
        min_risk
    )

    if risk <= 0:
        return 0

    # 🔥 setup RR
    if setup_type == "pre_breakout":

        target = resistance * 1.05

    elif setup_type == "strong_follow":

        target = resistance * 1.15

    else:

        target = resistance * 1.10

    reward = target - price

    if reward <= 0:
        return 0

    return round(
        reward / risk,
        2
    )


# ================================
# 🔥 EXTENDED（v17.5）
# ================================
def is_extended(
    price,
    ma20
):

    return (
        price > ma20 * 1.15
    )


# ================================
# 🔥 WAIT reason
# ================================
def get_wait_reason(
    volume,
    rr,
    extended,
    breakout_ready=False
):

    if extended:
        return "WAIT_EXTENDED"

    if rr < 1:
        return "WAIT_RR"

    if volume == "WEAK":
        return "WAIT_VOLUME"

    if breakout_ready:
        return "WAIT_BREAKOUT"

    return "WAIT"


# ================================
# 🔥 strategy（v17.5）
# ================================
def strategy(
    price,
    ma5,
    ma20,
    closes,
    volumes
):

    support, resistance = (
        support_resistance(closes)
    )

    market = market_signal(
        closes,
        ma20
    )

    trend = trend_signal(
        price,
        ma5,
        ma20
    )

    volume = volume_signal(
        volumes
    )

    vp_state = volume_price_state(
        closes,
        volumes
    )

    structure = structure_state(
        closes,
        ma5,
        ma20
    )

    momentum = (
        "ACCELERATING"
        if avg(closes[-3:])
        > avg(closes[-6:-3])
        else "DECELERATING"
    )

    m_score = market_score(
        market,
        trend,
        structure,
        volume,
        momentum
    )

    m_grade = market_grade(
        m_score
    )

    score = decision_score(
        market,
        trend,
        structure,
        volume
    )

    fake_break = edge_fake_breakout(
        closes
    )

    failed_breakout = breakout_fail(
        closes,
        resistance
    )

    base_pos = base_position(
        market,
        trend,
        structure,
        volume
    )

    # ================================
    # 🔥 stop
    # ================================
    stop_candidate = min(
        ma5,
        avg(closes[-3:])
    )

    # ================================
    # 🔥 stage
    # ================================
    entry_stage = detect_entry_stage(
        closes,
        ma5,
        resistance,
        volume
    )

    # ================================
    # 🔥 extended
    # ================================
    extended = is_extended(
        price,
        ma20
    )

    # ================================
    # 🔥 breakout fail
    # ================================
    if failed_breakout:

        return build_result(

            decision="EXIT",

            position=0,

            market_score=m_score,

            market_grade=m_grade,

            trend=trend,

            volume_state=volume,

            volume_price_state=vp_state,

            structure_state=structure,

            rr=0,

            entry_stage="BREAKOUT_FAIL",

            extended=extended,

            breakout_fail=True
        )

    # ================================
    # 🔥 WEAK
    # ================================
    if (
        market == "WEAK"
        or trend == "DOWN"
    ):

        return build_result(

            decision="NO_TRADE",

            position=0,

            market_score=m_score,

            market_grade=m_grade,

            trend=trend,

            volume_state=volume,

            volume_price_state=vp_state,

            structure_state=structure,

            rr=0,

            entry_stage=entry_stage,

            extended=extended,

            wait_reason="WAIT_TREND"
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

            volume_price_state=vp_state,

            structure_state=structure,

            rr=0,

            entry_stage=entry_stage,

            extended=extended,

            wait_reason="WAIT_FAKE_BREAK"
        )

    # ================================
    # 🔥 strong follow
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

        rr = calc_rr(
            price,
            stop_candidate,
            resistance,
            "strong_follow"
        )

        if rr < MIN_RR_STRONG:

            return build_result(

                decision="WAIT",

                position=0,

                market_score=m_score,

                market_grade=m_grade,

                trend=trend,

                volume_state=volume,

                volume_price_state=vp_state,

                structure_state=structure,

                rr=rr,

                entry_stage=entry_stage,

                extended=extended,

                wait_reason="WAIT_RR"
            )

        pos = min(
            max(base_pos, 0.7),
            0.9
        )

        # 🔥 extended 降倉
        if extended:
            pos *= 0.5

        return build_result(

            decision="BUY",

            decision_type="strong",

            buy=price,

            stop=stop_candidate,

            position=round(pos, 2),

            market_score=m_score,

            market_grade=m_grade,

            trend=trend,

            volume_state=volume,

            volume_price_state=vp_state,

            structure_state=structure,

            rr=rr,

            entry_stage=entry_stage,

            extended=extended
        )

    # ================================
    # 🔥 breakout
    # ================================
    if (
        is_breakout(
            closes[-1],
            resistance
        )
        and score >= 4
    ):

        rr = calc_rr(
            price,
            stop_candidate,
            resistance,
            "breakout"
        )

        if rr < MIN_RR_BREAKOUT:

            return build_result(

                decision="WAIT",

                position=0,

                market_score=m_score,

                market_grade=m_grade,

                trend=trend,

                volume_state=volume,

                volume_price_state=vp_state,

                structure_state=structure,

                rr=rr,

                entry_stage=entry_stage,

                extended=extended,

                wait_reason="WAIT_RR"
            )

        pos = max(base_pos, 0.5)

        if entry_stage == "TURN":
            pos = min(pos, 0.4)

        if extended:
            pos *= 0.5

        return build_result(

            decision="BUY",

            decision_type="breakout",

            buy=price,

            stop=stop_candidate,

            position=round(pos, 2),

            market_score=m_score,

            market_grade=m_grade,

            trend=trend,

            volume_state=volume,

            volume_price_state=vp_state,

            structure_state=structure,

            rr=rr,

            entry_stage=entry_stage,

            extended=extended,

            fresh_breakout=is_fresh_breakout(
                closes,
                resistance
            )
        )

    # ================================
    # 🔥 pre breakout
    # ================================
    breakout_ready = (
        price > resistance * 0.985
    )

    if (
        trend == "UP"
        and volume != "WEAK"
        and structure != "WEAK"
        and breakout_ready
        and score >= 2
    ):

        rr = calc_rr(
            price,
            stop_candidate,
            resistance,
            "pre_breakout"
        )

        if rr < MIN_RR_PREBREAK:

            return build_result(

                decision="WAIT",

                position=0,

                market_score=m_score,

                market_grade=m_grade,

                trend=trend,

                volume_state=volume,

                volume_price_state=vp_state,

                structure_state=structure,

                rr=rr,

                entry_stage=entry_stage,

                extended=extended,

                wait_reason="WAIT_RR"
            )

        pos = max(base_pos, 0.2)

        if entry_stage == "TURN":
            pos = min(pos, 0.3)

        return build_result(

            decision="BUY",

            decision_type="pre_breakout",

            buy=price,

            stop=stop_candidate,

            position=round(pos, 2),

            market_score=m_score,

            market_grade=m_grade,

            trend=trend,

            volume_state=volume,

            volume_price_state=vp_state,

            structure_state=structure,

            rr=rr,

            entry_stage=entry_stage,

            extended=extended
        )

    # ================================
    # 🔥 default WAIT
    # ================================
    rr = calc_rr(
        price,
        stop_candidate,
        resistance,
        "breakout"
    )

    return build_result(

        decision="WAIT",

        position=0,

        market_score=m_score,

        market_grade=m_grade,

        trend=trend,

        volume_state=volume,

        volume_price_state=vp_state,

        structure_state=structure,

        rr=rr,

        entry_stage=entry_stage,

        extended=extended,

        wait_reason=get_wait_reason(
            volume,
            rr,
            extended,
            breakout_ready=(
                price >
                resistance * 0.985
            )
        )
    )


# ================================
# 🔥 pick_best_stock（v17.5）
# ================================
def pick_best_stock(results_dict):

    best_name = None

    best_score = -999

    for name, result in results_dict.items():

        score = result.get(
            "strength",
            0
        )

        if score > best_score:

            best_score = score

            best_name = name

    return best_name, best_score