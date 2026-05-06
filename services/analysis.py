# ================================
# 🔥 analysis.py（FINAL v17.7.3｜STATE PRIORITY PATCH）
# ================================

# 🔒 VERSION LOCK
# - ✅ 保留 v17.7 lifecycle engine
# - ✅ 不新增功能（只做穩定化）
# - ✅ 修正：setup_score 正規化
# - ✅ 修正：execution_score 過熱扣分
# - ✅ 修正：strength_score 不再被 RR 主導
# - ✅ 修正：RR target 回歸合理區間
# - ✅ 修正：FAIL 不再扣分過重
# - ✅ 修正：volume expansion 誤判
# - ✅ 修正：structure_state 穩定化
# - ✅ 修正：lifecycle 與 entry_stage 分離
# - ✅ 修正：breakout_ready 全系統一致
# - ✅ 修正：EXTREME state 優先級
# - ✅ 修正：過熱股 BUY 壓倉
# - ✅ 修正：Day1 灌分問題
# - ✅ 修正：EXPANSION 優先級衝突
# - ✅ 保持：BUY / WAIT / NO_TRADE
# ================================


# ================================
# 🔥 常數（v17.7.3）
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
# 🔥 行動轉換（v17.7.3）
# ================================
def action_mapper(decision, position):

    if decision == "BUY":

        return {
            "action": round(position, 2),
            "action_type": "BUY"
        }

    # 🔥 FAIL 不直接 SELL
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
# 🔥 build_result
# ================================
def build_result(**kwargs):

    decision = kwargs.get("decision", "WAIT")

    position = kwargs.get("position", 0)

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

        # 🔥 entry
        "entry_stage": kwargs.get(
            "entry_stage"
        ),

        # 🔥 lifecycle
        "lifecycle": kwargs.get(
            "lifecycle",
            "BASE"
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
# 🔥 strength_score（v17.7.3）
# 🔥 修正：
# - RR 不再主導排名
# - Day1 降低灌分
# - EXTREME 強制降權
# ================================
def strength_score(result):

    score = 0

    score += (
        result.get("setup_score", 0)
        * 0.6
    )

    score += (
        result.get("execution_score", 0)
        * 0.4
    )

    rr = result.get("rr", 0)

    # 🔥 RR 正規化（不再直接加 rr）
    if rr >= 3:
        score += 1.5

    elif rr >= 2:
        score += 1

    elif rr >= 1:
        score += 0.5

    # 🔥 Day1 / Day2 降低加權
    if result.get("entry_stage") == "BREAKOUT_DAY1":
        score += 1.5

    elif result.get("entry_stage") == "CONFIRM_DAY2":
        score += 1

    # 🔥 FAIL 降低懲罰（避免假跌破被打爛）
    if result.get("breakout_fail"):
        score -= 2

    # 🔥 過熱強制降權
    ext_level = result.get(
        "extended_level",
        0
    )

    if ext_level >= 3:
        score -= 5

    elif ext_level >= 2:
        score -= 2

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
# 🔥 volume_signal
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
# 🔥 volume_price_state（v17.7.3）
# 🔥 修正：避免小漲也被判 expansion
# 🔥 修正：量價擴張需結構同步
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

    price_change = (
        (closes[-1] - closes[-2])
        / closes[-2]
    )

    # 🔥 真正主升
    if (
        ratio > 1.5
        and price_change > 0.03
    ):
        return "EXPANSION"

    # 🔥 放量下跌
    if (
        ratio > 1.5
        and price_change < -0.02
    ):
        return "DISTRIBUTION"

    # 🔥 縮量整理
    if ratio < 0.8:
        return "COILING"

    return "NORMAL"


# ================================
# 🔥 structure_state（v17.7.3）
# 🔥 修正：穩定化
# ================================
def structure_state(
    closes,
    ma5,
    ma20
):

    score = 0

    recent_high = max(closes[-5:])
    old_high = max(closes[-10:-5])

    recent_low = min(closes[-5:])
    old_low = min(closes[-10:-5])

    # 🔥 higher high
    if recent_high > old_high:
        score += 1

    # 🔥 higher low
    if recent_low > old_low:
        score += 1

    # 🔥 ma alignment
    if ma5 > ma20:
        score += 1

    # 🔥 close above ma5
    if closes[-1] > ma5:
        score += 1

    # 🔥 above ma20
    if closes[-1] > ma20:
        score += 1

    if score >= 5:
        return "STRONG"

    elif score >= 3:
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
# 🔥 breakout_price
# ================================
def breakout_price(resistance):

    return resistance * (
        1 + BREAKOUT_THRESHOLD
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

    return today and not yesterday


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
        < breakout_price(resistance)
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
# 🔥 detect_entry_stage
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

    # 🔥 真 Day1
    if is_fresh_breakout(
        closes,
        resistance
    ):
        return "BREAKOUT_DAY1"

    # 🔥 真 Day2
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

    # 🔥 reclaim
    if (
        closes[-2] < ma5
        and closes[-1] > ma5
    ):
        return "RECLAIM"

    # 🔥 pullback
    if (
        closes[-1] > ma20
        and closes[-1] < ma5
    ):
        return "PULLBACK"

    # 🔥 turn
    if (
        closes[-1] > closes[-2]
        and closes[-1] > ma5
        and closes[-1] > ma20
        and volume != "WEAK"
    ):
        return "TURN"

    return "BASE"


# ================================
# 🔥 detect_lifecycle（v17.7.3）
# 🔥 修正：
# - EXTREME 優先級最高
# - breakout 與 expansion 分離
# ================================
def detect_lifecycle(
    price,
    resistance,
    vp_state,
    ext_level,
    breakout_ready,
    failed_breakout
):

    if failed_breakout:
        return "FAIL"

    # 🔥 EXTREME 優先級最高
    if ext_level >= 3:
        return "EXTREME"

    # 🔥 breakout 優先於 expansion
    if is_breakout(
        price,
        resistance
    ):
        return "BREAKOUT"

    if vp_state == "EXPANSION":
        return "EXPANSION"

    if breakout_ready:
        return "PRE_BREAKOUT"

    return "BASE"


# ================================
# 🔥 calc_rr（v17.7.3）
# 🔥 修正：RR 合理化
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

    raw_risk = price - stop

    risk = max(
        raw_risk,
        min_risk
    )

    if risk <= 0:
        return 0

    # 🔥 target 正規化
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
# 🔥 extended
# ================================
def extended_level(
    price,
    ma20
):

    ratio = price / ma20

    if ratio >= EXTENDED_LV3:
        return 3

    elif ratio >= EXTENDED_LV2:
        return 2

    elif ratio >= EXTENDED_LV1:
        return 1

    return 0


# ================================
# 🔥 WAIT reason
# ================================
def get_wait_reason(
    volume,
    rr,
    ext_level,
    entry_stage
):

    if ext_level >= 2:
        return "WAIT_EXTENDED"

    if rr < 1:
        return "WAIT_RR"

    if volume == "WEAK":
        return "WAIT_VOLUME"

    if entry_stage == "CONFIRM_DAY2":
        return "WAIT_CONFIRM"

    return "WAIT_EXECUTION"


# ================================
# 🔥 setup score（v17.7.3）
# 🔥 修正：NORMAL 不再 0 分
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
# 🔥 execution score（v17.7.3）
# 🔥 修正：
# - Day1 灌分
# - EXTREME 過熱強制扣分
# ================================
def execution_score(
    entry_stage,
    rr,
    vp_state,
    ext_level
):

    score = 0

    # 🔥 Day1 降低灌分
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

    # 🔥 過熱扣分
    if ext_level >= 3:
        score -= 5

    elif ext_level >= 2:
        score -= 2

    return score


# ================================
# 🔥 strategy（v17.7.3）
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

    extended = ext_level >= 2

    breakout_ready = (
        price > resistance * 0.985
    )

    lifecycle = detect_lifecycle(
        price,
        resistance,
        vp_state,
        ext_level,
        breakout_ready,
        failed_breakout
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

            volume_state=volume,

            volume_price_state=vp_state,

            structure_state=structure,

            rr=0,

            entry_stage="BREAKOUT_FAIL",

            lifecycle="FAIL",

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

            volume_state=volume,

            volume_price_state=vp_state,

            structure_state=structure,

            rr=rr,

            entry_stage=entry_stage,

            lifecycle=lifecycle,

            extended=extended,

            extended_level=ext_level,

            wait_reason="WAIT_TREND"
        )

    # ================================
    # 🔥 fake breakout
    # 🔥 提高優先級避免追高
    # ================================
    if fake_break:

        return build_result(

            decision="WAIT",

            market_score=m_score,

            market_grade=m_grade,

            setup_score=setup,

            execution_score=execute,

            trend=trend,

            volume_state=volume,

            volume_price_state=vp_state,

            structure_state=structure,

            rr=rr,

            entry_stage=entry_stage,

            lifecycle="FAKE_BREAK",

            extended=extended,

            extended_level=ext_level,

            wait_reason="WAIT_FAKE_BREAK"
        )

    # ================================
    # 🔥 EXTREME 過熱
    # 🔥 強制不追
    # ================================
    if ext_level >= 3:

        return build_result(

            decision="WAIT",

            market_score=m_score,

            market_grade=m_grade,

            setup_score=setup,

            execution_score=execute,

            trend=trend,

            volume_state=volume,

            volume_price_state=vp_state,

            structure_state=structure,

            rr=rr,

            entry_stage=entry_stage,

            lifecycle="EXTREME",

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

        # 🔥 過熱壓倉
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

            volume_state=volume,

            volume_price_state=vp_state,

            structure_state=structure,

            rr=rr,

            entry_stage=entry_stage,

            lifecycle="EXPANSION",

            extended=extended,

            extended_level=ext_level
        )

    # ================================
    # 🔥 breakout
    # ================================
    if (
        is_breakout(
            closes[-1],
            resistance
        )
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

        # 🔥 過熱壓倉
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

            volume_state=volume,

            volume_price_state=vp_state,

            structure_state=structure,

            rr=rr,

            entry_stage=entry_stage,

            lifecycle="BREAKOUT",

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

        # 🔥 PRE_BREAKOUT 過熱壓倉
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

            volume_state=volume,

            volume_price_state=vp_state,

            structure_state=structure,

            rr=rr,

            entry_stage=entry_stage,

            lifecycle="PRE_BREAKOUT",

            extended=extended,

            extended_level=ext_level
        )

    # ================================
    # 🔥 WAIT
    # ================================
    return build_result(

        decision="WAIT",

        market_score=m_score,

        market_grade=m_grade,

        setup_score=setup,

        execution_score=execute,

        trend=trend,

        volume_state=volume,

        volume_price_state=vp_state,

        structure_state=structure,

        rr=rr,

        entry_stage=entry_stage,

        lifecycle=lifecycle,

        extended=extended,

        extended_level=ext_level,

        wait_reason=get_wait_reason(
            volume,
            rr,
            ext_level,
            entry_stage
        )
    )


# ================================
# 🔥 pick_best_stock（v17.7.3）
# ================================
def pick_best_stock(results_dict):

    best_name = None

    best_score = -999

    for name, result in results_dict.items():

        score = result.get(
            "strength",
            0
        )

        # 🔥 FAIL / EXTREME 降權
        if result.get("lifecycle") in [
            "FAIL",
            "EXTREME"
        ]:
            score -= 3

        if score > best_score:

            best_score = score

            best_name = name

    return best_name, best_score