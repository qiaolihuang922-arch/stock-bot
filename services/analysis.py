# ================================
# 🔥 analysis.py（FINAL v17.7.6｜STATE HIERARCHY PATCH）
# ================================

# 🔒 VERSION LOCK
# - ✅ 保留 v17.7.5 semantic engine
# - ✅ breakout / trade / heat state 分離
# - ✅ lifecycle hierarchy 正式建立
# - ✅ strength ceiling system
# - ✅ dominant state normalization
# - ✅ RR=0 ceiling 修正
# - ✅ LATE_ENTRY 優先級修正
# - ✅ EXTREME state hierarchy
# - ✅ breakout trend phase
# - ✅ late trend phase
# - ✅ pick_best_stock contextual ranking
# - ✅ semantic collision 修正
# ================================


# ================================
# 🔥 常數
# ================================
BREAKOUT_THRESHOLD = 0.005

MIN_RR_BREAKOUT = 1.5
MIN_RR_PREBREAK = 1.0
MIN_RR_STRONG = 2.0

MIN_STOP_BUFFER = 0.015

EXTENDED_LV1 = 1.08
EXTENDED_LV2 = 1.15
EXTENDED_LV3 = 1.22


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

    elif market == "NORMAL":
        pos += 0.15

    if trend == "UP":
        pos += 0.2

    elif trend == "SIDE":
        pos += 0.05

    if structure == "STRONG":
        pos += 0.2

    elif structure == "NORMAL":
        pos += 0.1

    if volume == "EXPLOSIVE":
        pos += 0.25

    elif volume == "STRONG":
        pos += 0.2

    elif volume == "NORMAL":
        pos += 0.1

    return round(min(pos, 0.6), 2)


# ================================
# 🔥 action mapper
# ================================
def action_mapper(decision, position):

    if decision == "BUY":

        return {
            "action": round(position, 2),
            "action_type": "BUY"
        }

    if decision == "FAIL":

        return {
            "action": 0.0,
            "action_type": "FAIL"
        }

    return {
        "action": 0.0,
        "action_type": "HOLD"
    }


# ================================
# 🔥 dominant state
# ================================
def dominant_state(
    lifecycle,
    breakout_state,
    trade_state,
    heat_state
):

    if breakout_state == "FAIL":
        return "FAILED"

    if heat_state == "EXTREME":
        return "EXTREME"

    if trade_state == "LATE_ENTRY":
        return "LATE"

    if breakout_state == "BREAKOUT":
        return "BREAKOUT"

    if lifecycle in [
        "TREND",
        "BREAKOUT_TREND"
    ]:
        return "TREND"

    return "NORMAL"


# ================================
# 🔥 lifecycle strength ceiling
# ================================
def lifecycle_strength_ceiling(
    lifecycle
):

    mapping = {

        "FAILED": 1.5,

        "DISTRIBUTION": 3,

        "EXTREME": 4,

        "LATE_TREND": 5.5,

        "WEAK": 4.5,

        "BASE": 6,

        "TREND": 8,

        "BREAKOUT_TREND": 10
    }

    return mapping.get(
        lifecycle,
        6
    )


# ================================
# 🔥 build result
# ================================
def build_result(**kwargs):

    decision = kwargs.get(
        "decision",
        "WAIT"
    )

    position = kwargs.get(
        "position",
        0
    )

    action_data = action_mapper(
        decision,
        position
    )

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

        "setup_score": kwargs.get(
            "setup_score",
            0
        ),

        "execution_score": kwargs.get(
            "execution_score",
            0
        ),

        "trend": kwargs.get("trend"),

        "trend_bias": kwargs.get(
            "trend_bias",
            "NORMAL"
        ),

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

        "entry_stage": kwargs.get(
            "entry_stage"
        ),

        "lifecycle": kwargs.get(
            "lifecycle",
            "BASE"
        ),

        "breakout_state": kwargs.get(
            "breakout_state",
            "NONE"
        ),

        "trade_state": kwargs.get(
            "trade_state",
            "NORMAL"
        ),

        "heat_state": kwargs.get(
            "heat_state",
            "NORMAL"
        ),

        "dominant_state": kwargs.get(
            "dominant_state",
            "NORMAL"
        ),

        "extended": kwargs.get(
            "extended",
            False
        ),

        "extended_level": kwargs.get(
            "extended_level",
            0
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
# 🔥 strength score
# ================================
def strength_score(result):

    score = 0

    score += (
        result.get(
            "setup_score",
            0
        ) * 0.6
    )

    score += (
        result.get(
            "execution_score",
            0
        ) * 0.4
    )

    rr = result.get("rr", 0)

    if rr >= 3:
        score += 1.5

    elif rr >= 2:
        score += 1

    elif rr >= 1:
        score += 0.5

    entry_stage = result.get(
        "entry_stage"
    )

    if entry_stage == "BREAKOUT_DAY1":
        score += 1.5

    elif entry_stage == "CONFIRM_DAY2":
        score += 1

    breakout_state = result.get(
        "breakout_state"
    )

    if breakout_state == "FAIL":
        score -= 2

    trade_state = result.get(
        "trade_state"
    )

    if trade_state == "LATE_ENTRY":
        score -= 1.5

    elif trade_state == "NO_VOLUME":
        score -= 1

    heat_state = result.get(
        "heat_state"
    )

    if heat_state == "EXTREME":
        score -= 5

    elif heat_state == "HOT":
        score -= 2

    lifecycle = result.get(
        "lifecycle"
    )

    ceiling = lifecycle_strength_ceiling(
        lifecycle
    )

    score = min(score, ceiling)

    if rr <= 0:
        score = min(score, 3)

    return round(score, 2)


# ================================
# 🔥 market score
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
# 🔥 market grade
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
# 🔥 market signal
# ================================
def market_signal(
    closes,
    ma20
):

    momentum = (
        closes[-1]
        - closes[-3]
    )

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
# 🔥 trend signal
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
# 🔥 volume signal
# ================================
def volume_signal(volumes):

    avg10 = avg(
        volumes[-10:]
    )

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
# 🔥 volume price state
# ================================
def volume_price_state(
    closes,
    volumes
):

    avg10 = avg(
        volumes[-10:]
    )

    ratio = (
        volumes[-1] / avg10
        if avg10 else 1
    )

    price_change = (
        (closes[-1] - closes[-2])
        / closes[-2]
    )

    if (
        ratio > 1.5
        and price_change > 0.03
    ):
        return "EXPANSION"

    if (
        ratio > 1.5
        and price_change < -0.02
    ):
        return "DISTRIBUTION"

    if ratio < 0.8:
        return "COILING"

    return "NORMAL"


# ================================
# 🔥 structure state
# ================================
def structure_state(
    closes,
    ma5,
    ma20
):

    score = 0

    recent_high = max(
        closes[-5:]
    )

    old_high = max(
        closes[-10:-5]
    )

    recent_low = min(
        closes[-5:]
    )

    old_low = min(
        closes[-10:-5]
    )

    if recent_high > old_high:
        score += 1

    if recent_low > old_low:
        score += 1

    if ma5 > ma20:
        score += 1

    if closes[-1] > ma5:
        score += 1

    if closes[-1] > ma20:
        score += 1

    if score >= 5:
        return "STRONG"

    elif score >= 3:
        return "NORMAL"

    return "WEAK"


# ================================
# 🔥 support resistance
# ================================
def support_resistance(closes):

    support = min(
        closes[-20:]
    )

    resistance = max(
        closes[-20:-3]
    )

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
# 🔥 breakout price
# ================================
def breakout_price(resistance):

    return (
        resistance * (
            1 + BREAKOUT_THRESHOLD
        )
    )


# ================================
# 🔥 fresh breakout
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

    return (
        today
        and not yesterday
    )


# ================================
# 🔥 breakout fail
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

        closes[-1]
        < breakout_price(
            resistance
        )
    )

    return (
        yesterday_breakout
        and today_fail
    )


# ================================
# 🔥 fake breakout
# ================================
def edge_fake_breakout(
    closes,
    resistance
):

    breakout_lv = breakout_price(
        resistance
    )

    return (

        closes[-2] > breakout_lv
        and closes[-1]
        < breakout_lv * 0.985
    )


# ================================
# 🔥 strong follow
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
# 🔥 detect entry stage
# ================================
def detect_entry_stage(
    closes,
    ma5,
    ma20,
    resistance,
    volume
):

    breakout_lv = breakout_price(
        resistance
    )

    if is_fresh_breakout(
        closes,
        resistance
    ):
        return "BREAKOUT_DAY1"

    yesterday_breakout = is_breakout(
        closes[-2],
        resistance
    )

    if (
        yesterday_breakout
        and closes[-1] > closes[-2]
        and closes[-1] > breakout_lv
    ):
        return "CONFIRM_DAY2"

    if (
        closes[-2] < ma5
        and closes[-1] > ma5
    ):
        return "RECLAIM"

    if (
        closes[-1] > ma20
        and closes[-1] < ma5
    ):
        return "PULLBACK"

    if (
        closes[-1] > closes[-2]
        and closes[-1] > ma5
        and closes[-1] > ma20
        and volume != "WEAK"
    ):
        return "TURN"

    return "BASE"


# ================================
# 🔥 detect breakout state
# ================================
def detect_breakout_state(
    price,
    resistance,
    breakout_ready,
    failed_breakout
):

    if failed_breakout:
        return "FAIL"

    if is_breakout(
        price,
        resistance
    ):
        return "BREAKOUT"

    if breakout_ready:
        return "READY"

    return "NONE"


# ================================
# 🔥 detect trade state
# ================================
def detect_trade_state(
    rr,
    volume,
    ext_level
):

    if ext_level >= 3:
        return "AVOID"

    if ext_level >= 2:
        return "EXTENDED"

    if rr < 0.5:
        return "LATE_ENTRY"

    if volume == "WEAK":
        return "NO_VOLUME"

    return "TRADEABLE"


# ================================
# 🔥 detect heat state
# ================================
def detect_heat_state(
    ext_level
):

    if ext_level >= 3:
        return "EXTREME"

    if ext_level >= 2:
        return "HOT"

    return "NORMAL"


# ================================
# 🔥 detect lifecycle
# ================================
def detect_lifecycle(
    vp_state,
    structure,
    trend,
    rr,
    breakout_state,
    heat_state
):

    if breakout_state == "FAIL":
        return "FAILED"

    if vp_state == "DISTRIBUTION":
        return "DISTRIBUTION"

    if heat_state == "EXTREME":
        return "EXTREME"

    if (
        vp_state == "EXPANSION"
        and rr < 0.5
    ):
        return "LATE_TREND"

    if (
        breakout_state == "BREAKOUT"
        and trend == "UP"
    ):
        return "BREAKOUT_TREND"

    if (
        structure == "STRONG"
        and trend == "UP"
    ):
        return "TREND"

    if trend == "SIDE":
        return "BASE"

    return "WEAK"


# ================================
# 🔥 calc rr
# ================================
def calc_rr(
    price,
    stop,
    resistance,
    setup_type="breakout"
):

    min_risk = (
        price * MIN_STOP_BUFFER
    )

    raw_risk = (
        price - stop
    )

    risk = max(
        raw_risk,
        min_risk
    )

    if risk <= 0:
        return 0

    if setup_type == "pre_breakout":

        target = resistance * 1.05

    elif setup_type == "strong_follow":

        target = resistance * 1.12

    else:

        target = resistance * 1.08

    reward = target - price

    if reward <= 0:
        return 0

    return round(
        reward / risk,
        2
    )


# ================================
# 🔥 extended level
# ================================
def extended_level(
    price,
    ma20
):

    ratio = (
        price / ma20
    )

    if ratio >= EXTENDED_LV3:
        return 3

    elif ratio >= EXTENDED_LV2:
        return 2

    elif ratio >= EXTENDED_LV1:
        return 1

    return 0


# ================================
# 🔥 wait reason
# ================================
def get_wait_reason(
    trade_state
):

    mapping = {

        "AVOID":
            "WAIT_EXTREME",

        "EXTENDED":
            "WAIT_EXTENDED",

        "LATE_ENTRY":
            "WAIT_RR",

        "NO_VOLUME":
            "WAIT_VOLUME"
    }

    return mapping.get(
        trade_state,
        "WAIT_EXECUTION"
    )


# ================================
# 🔥 setup score
# ================================
def setup_score(
    market,
    trend,
    structure,
    volume
):

    score = 0

    if market == "STRONG":
        score += 3

    elif market == "NORMAL":
        score += 1

    if trend == "UP":
        score += 3

    elif trend == "SIDE":
        score += 1

    if structure == "STRONG":
        score += 2

    elif structure == "NORMAL":
        score += 1

    if volume in [
        "STRONG",
        "EXPLOSIVE"
    ]:
        score += 2

    elif volume == "NORMAL":
        score += 1

    return score


# ================================
# 🔥 execution score
# ================================
def execution_score(
    entry_stage,
    rr,
    vp_state,
    ext_level
):

    score = 0

    if entry_stage == "BREAKOUT_DAY1":
        score += 3

    elif entry_stage == "CONFIRM_DAY2":
        score += 2.5

    elif entry_stage == "TURN":
        score += 2

    elif entry_stage == "RECLAIM":
        score += 1

    if rr >= 2:
        score += 2

    elif rr >= 1:
        score += 1

    if vp_state == "EXPANSION":
        score += 1.5

    elif vp_state == "DISTRIBUTION":
        score -= 2

    if ext_level >= 3:
        score -= 5

    elif ext_level >= 2:
        score -= 2

    return score


# ================================
# 🔥 strategy
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

    fake_break = edge_fake_breakout(
        closes,
        resistance
    )

    failed_breakout = breakout_fail(
        closes,
        resistance
    )

    stop_candidate = min(
        ma5,
        avg(closes[-3:])
    )

    entry_stage = detect_entry_stage(
        closes,
        ma5,
        ma20,
        resistance,
        volume
    )

    ext_level = extended_level(
        price,
        ma20
    )

    extended = (
        ext_level >= 2
    )

    breakout_ready = (
        price > resistance * 0.985
    )

    rr = calc_rr(
        price,
        stop_candidate,
        resistance,
        "breakout"
    )

    setup = setup_score(
        market,
        trend,
        structure,
        volume
    )

    execute = execution_score(
        entry_stage,
        rr,
        vp_state,
        ext_level
    )

    breakout_state = detect_breakout_state(
        price,
        resistance,
        breakout_ready,
        failed_breakout
    )

    trade_state = detect_trade_state(
        rr,
        volume,
        ext_level
    )

    heat_state = detect_heat_state(
        ext_level
    )

    lifecycle = detect_lifecycle(
        vp_state,
        structure,
        trend,
        rr,
        breakout_state,
        heat_state
    )

    dominant = dominant_state(
        lifecycle,
        breakout_state,
        trade_state,
        heat_state
    )

    if market == "STRONG":

        trend_bias = "STRONG"

    elif market == "WEAK":

        trend_bias = "WEAK"

    else:

        trend_bias = "NORMAL"

    # ================================
    # 🔥 breakout fail
    # ================================
    if failed_breakout:

        return build_result(

            decision="FAIL",

            market_score=m_score,

            market_grade=m_grade,

            setup_score=setup,

            execution_score=execute,

            trend=trend,

            trend_bias=trend_bias,

            volume_state=volume,

            volume_price_state=vp_state,

            structure_state=structure,

            rr=0,

            entry_stage="BREAKOUT_FAIL",

            lifecycle=lifecycle,

            breakout_state="FAIL",

            trade_state=trade_state,

            heat_state=heat_state,

            dominant_state=dominant,

            extended=extended,

            extended_level=ext_level,

            breakout_fail=True
        )

    # ================================
    # 🔥 weak market
    # ================================
    if (
        market == "WEAK"
        or trend == "DOWN"
    ):

        return build_result(

            decision="NO_TRADE",

            market_score=m_score,

            market_grade=m_grade,

            setup_score=setup,

            execution_score=execute,

            trend=trend,

            trend_bias=trend_bias,

            volume_state=volume,

            volume_price_state=vp_state,

            structure_state=structure,

            rr=rr,

            entry_stage=entry_stage,

            lifecycle=lifecycle,

            breakout_state=breakout_state,

            trade_state=trade_state,

            heat_state=heat_state,

            dominant_state=dominant,

            extended=extended,

            extended_level=ext_level,

            wait_reason=get_wait_reason(
                trade_state
            )
        )

    # ================================
    # 🔥 fake breakout
    # ================================
    if fake_break:

        return build_result(

            decision="WAIT",

            market_score=m_score,

            market_grade=m_grade,

            setup_score=setup,

            execution_score=execute,

            trend=trend,

            trend_bias=trend_bias,

            volume_state=volume,

            volume_price_state=vp_state,

            structure_state=structure,

            rr=rr,

            entry_stage=entry_stage,

            lifecycle=lifecycle,

            breakout_state="FAKE_BREAK",

            trade_state=trade_state,

            heat_state=heat_state,

            dominant_state=dominant,

            extended=extended,

            extended_level=ext_level,

            wait_reason="WAIT_FAKE_BREAK"
        )

    # ================================
    # 🔥 extreme
    # ================================
    if heat_state == "EXTREME":

        return build_result(

            decision="WAIT",

            market_score=m_score,

            market_grade=m_grade,

            setup_score=setup,

            execution_score=execute,

            trend=trend,

            trend_bias=trend_bias,

            volume_state=volume,

            volume_price_state=vp_state,

            structure_state=structure,

            rr=rr,

            entry_stage=entry_stage,

            lifecycle=lifecycle,

            breakout_state=breakout_state,

            trade_state="AVOID",

            heat_state="EXTREME",

            dominant_state=dominant,

            extended=extended,

            extended_level=ext_level,

            wait_reason="WAIT_EXTREME"
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
        and rr >= MIN_RR_STRONG
    ):

        pos = min(
            max(
                base_position(
                    market,
                    trend,
                    structure,
                    volume
                ),
                0.7
            ),
            0.9
        )

        if ext_level >= 2:
            pos *= 0.4

        return build_result(

            decision="BUY",

            decision_type="strong_follow",

            buy=price,

            stop=stop_candidate,

            position=round(pos, 2),

            market_score=m_score,

            market_grade=m_grade,

            setup_score=setup,

            execution_score=execute,

            trend=trend,

            trend_bias=trend_bias,

            volume_state=volume,

            volume_price_state=vp_state,

            structure_state=structure,

            rr=rr,

            entry_stage=entry_stage,

            lifecycle=lifecycle,

            breakout_state=breakout_state,

            trade_state=trade_state,

            heat_state=heat_state,

            dominant_state=dominant,

            extended=extended,

            extended_level=ext_level
        )

    # ================================
    # 🔥 breakout
    # ================================
    if (
        breakout_state == "BREAKOUT"
        and rr >= MIN_RR_BREAKOUT
    ):

        pos = max(
            base_position(
                market,
                trend,
                structure,
                volume
            ),
            0.5
        )

        if entry_stage == "TURN":
            pos = min(pos, 0.4)

        if ext_level >= 2:
            pos *= 0.4

        return build_result(

            decision="BUY",

            decision_type="breakout",

            buy=price,

            stop=stop_candidate,

            position=round(pos, 2),

            market_score=m_score,

            market_grade=m_grade,

            setup_score=setup,

            execution_score=execute,

            trend=trend,

            trend_bias=trend_bias,

            volume_state=volume,

            volume_price_state=vp_state,

            structure_state=structure,

            rr=rr,

            entry_stage=entry_stage,

            lifecycle=lifecycle,

            breakout_state="BREAKOUT",

            trade_state=trade_state,

            heat_state=heat_state,

            dominant_state=dominant,

            extended=extended,

            extended_level=ext_level,

            fresh_breakout=is_fresh_breakout(
                closes,
                resistance
            )
        )

    # ================================
    # 🔥 pre breakout
    # ================================
    if (
        trend == "UP"
        and volume != "WEAK"
        and structure != "WEAK"
        and breakout_ready
        and rr >= MIN_RR_PREBREAK
    ):

        pos = max(
            base_position(
                market,
                trend,
                structure,
                volume
            ),
            0.2
        )

        if ext_level >= 2:
            pos *= 0.5

        return build_result(

            decision="BUY",

            decision_type="pre_breakout",

            buy=price,

            stop=stop_candidate,

            position=round(pos, 2),

            market_score=m_score,

            market_grade=m_grade,

            setup_score=setup,

            execution_score=execute,

            trend=trend,

            trend_bias=trend_bias,

            volume_state=volume,

            volume_price_state=vp_state,

            structure_state=structure,

            rr=rr,

            entry_stage=entry_stage,

            lifecycle=lifecycle,

            breakout_state="READY",

            trade_state=trade_state,

            heat_state=heat_state,

            dominant_state=dominant,

            extended=extended,

            extended_level=ext_level
        )

    # ================================
    # 🔥 wait
    # ================================
    return build_result(

        decision="WAIT",

        market_score=m_score,

        market_grade=m_grade,

        setup_score=setup,

        execution_score=execute,

        trend=trend,

        trend_bias=trend_bias,

        volume_state=volume,

        volume_price_state=vp_state,

        structure_state=structure,

        rr=rr,

        entry_stage=entry_stage,

        lifecycle=lifecycle,

        breakout_state=breakout_state,

        trade_state=trade_state,

        heat_state=heat_state,

        dominant_state=dominant,

        extended=extended,

        extended_level=ext_level,

        wait_reason=get_wait_reason(
            trade_state
        )
    )


# ================================
# 🔥 pick best stock
# ================================
def pick_best_stock(results_dict):

    best_name = None

    best_score = -999

    for name, result in results_dict.items():

        score = result.get(
            "strength",
            0
        )

        lifecycle = result.get(
            "lifecycle"
        )

        if result.get(
            "breakout_state"
        ) == "FAIL":

            score -= 3

        if result.get(
            "heat_state"
        ) == "EXTREME":

            score -= 4

        if result.get(
            "trade_state"
        ) == "LATE_ENTRY":

            score -= 2

        if lifecycle == "BREAKOUT_TREND":
            score += 1

        elif lifecycle == "LATE_TREND":
            score -= 2

        elif lifecycle == "EXTREME":
            score -= 4

        if score > best_score:

            best_score = score

            best_name = name

    return best_name, best_score