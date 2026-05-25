# ================================
# analysis.py（v19.1.3｜WATCH AND SHAKEOUT FIX）
# ================================

# ================================
# 🔥 常數
# ================================
BREAKOUT_THRESHOLD = 0.005
MIN_DATA_POINTS = 20

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
# 🔥 v19.1.3 資料保護 / 多週期工具
# ================================
def normalize_series(arr, n=MIN_DATA_POINTS):

    if not arr:
        return []

    data = list(arr)

    if len(data) < n:
        # 中文註釋：K 線不足時用最早資料補前段，保留最新價格位置不變。
        data = [data[0]] * (n - len(data)) + data

    return data


def merge_live_close(closes, price):

    data = normalize_series(
        closes
    )

    if not data:
        return []

    if price is None:
        return data

    # 中文註釋：v19.1.3 將盤中即時價覆蓋最後一根 K，讓策略判斷與報文價格一致。
    return data[:-1] + [
        float(price)
    ]


def pct_change(arr, days):

    if not arr or len(arr) <= days:
        return 0

    base = arr[-1 - days]

    if not base:
        return 0

    return (
        arr[-1] - base
    ) / base


def multi_period_metrics(closes, volumes):

    avg5_volume = avg(
        volumes[-5:]
    )

    avg10_volume = avg(
        volumes[-10:]
    )

    ratio5 = (
        volumes[-1] / avg5_volume
        if avg5_volume else 1
    )

    ratio10 = (
        volumes[-1] / avg10_volume
        if avg10_volume else 1
    )

    # 中文註釋：v19.1.3 統一輸出 1 / 3 / 5 / 10 日變化，避免單日訊號反覆誤判。
    return {
        "chg_1d": pct_change(closes, 1),
        "chg_3d": pct_change(closes, 3),
        "chg_5d": pct_change(closes, 5),
        "chg_10d": pct_change(closes, 10),
        "vol_ratio_5": ratio5,
        "vol_ratio_10": ratio10,
        "avg3": avg(closes[-3:]),
        "avg5": avg(closes[-5:]),
        "avg10": avg(closes[-10:])
    }


def momentum_signal(metrics):

    chg3 = metrics.get(
        "chg_3d",
        0
    )

    chg5 = metrics.get(
        "chg_5d",
        0
    )

    chg10 = metrics.get(
        "chg_10d",
        0
    )

    if chg3 > 0 and chg5 > 0:
        return "ACCELERATING"

    if chg5 > 0 and chg10 >= 0:
        return "STABLE_UP"

    if chg3 < 0 and chg5 < 0:
        return "REVERSING"

    return "DECELERATING"


def multi_day_bias(metrics):

    chg3 = metrics.get("chg_3d", 0)
    chg5 = metrics.get("chg_5d", 0)
    chg10 = metrics.get("chg_10d", 0)

    if chg3 > 0 and chg5 > 0 and chg10 >= 0:
        return "UP_CONFIRM"

    if chg3 < 0 and chg5 >= 0 and chg10 >= 0:
        return "SHAKEOUT"

    if chg3 > 0 and chg5 < 0:
        return "UP_WEAKENING"

    if chg3 < 0 and chg5 < 0 and chg10 < 0:
        return "DOWN_CONFIRM"

    # 中文註釋：v19.1.3 將 3 / 5 / 10 日趨勢壓成單一偏向，供洗盤與弱反彈判斷使用。
    return "MIXED"


def market_regime(market, trend, heat_state, m_grade):

    if heat_state == "EXTREME":
        return "OVERHEAT"

    if market == "STRONG" and trend == "UP":
        return "RISK_ON"

    if market == "WEAK" or trend == "DOWN" or m_grade == "D":
        return "RISK_OFF"

    # 中文註釋：v19.1.3 中性市場獨立成 regime，不再與弱勢混用。
    return "NEUTRAL"


def price_behavior_signal(
    change,
    market,
    trend,
    volume,
    vp_state,
    momentum
):

    if change >= 9.5:
        if market == "STRONG" and trend == "UP" and vp_state != "DISTRIBUTION":
            return "LIMIT_LOCK"

        return "LIMIT_REBOUND"

    if change >= 3 and trend != "UP":
        return "WEAK_REBOUND"

    if vp_state == "DISTRIBUTION":
        return "DISTRIBUTION_SPIKE"

    if change <= -3 and volume != "WEAK":
        return "VOLUME_DROP"

    if change < 0 and volume == "WEAK" and momentum != "REVERSING":
        return "LOW_VOLUME_PULLBACK"

    if vp_state == "EXPANSION" and trend == "UP":
        return "VOLUME_BREAKOUT"

    return "NORMAL"


def structure_phase_signal(
    price_behavior,
    lifecycle,
    breakout_state,
    heat_state,
    trend,
    volume,
    structure,
    market,
    dist,
    bias
):

    if breakout_state == "FAIL":
        return "FAILED_BREAKOUT"

    if price_behavior == "LIMIT_LOCK":
        return "LOCK_LIMIT"

    if price_behavior == "LIMIT_REBOUND":
        return "LIMIT_REBOUND"

    if price_behavior == "DISTRIBUTION_SPIKE":
        return "DISTRIBUTION"

    if price_behavior == "LOW_VOLUME_PULLBACK" or bias == "SHAKEOUT":
        if trend == "UP" and structure != "WEAK":
            return "SHAKEOUT"

        return "HEALTHY_PULLBACK"

    if price_behavior == "WEAK_REBOUND":
        return "WEAK_REBOUND"

    if breakout_state == "BREAKOUT" and trend == "UP":
        if dist is not None and dist <= 1:
            return "BREAKOUT_CONFIRM"

        return "BREAKOUT"

    if breakout_state == "READY":
        return "BREAKOUT_WATCH"

    if market == "WEAK" or trend == "DOWN":
        return "WEAK"

    if heat_state == "EXTREME":
        # 中文註釋：v19.1.3 過熱只作為風險標籤，不能覆蓋漲停、突破、弱勢等原本型態。
        return "EXTENDED_RISK"

    if lifecycle == "BASE":
        return "BASE"

    # 中文註釋：v19.1.3 structure_phase 作為策略層主語，讓顯示層不再自行猜型態。
    return lifecycle or "BASE"


def entry_profile_signal(
    phase,
    behavior,
    breakout_state,
    entry_stage,
    rr,
    risk,
    dist
):

    if behavior == "LIMIT_REBOUND":
        return "WAIT_LIMIT_REBOUND"

    if behavior == "LIMIT_LOCK":
        return "WAIT_LIMIT_LOCK"

    if behavior == "WEAK_REBOUND":
        return "WAIT_WEAK_REBOUND"

    if phase in ["SHAKEOUT", "HEALTHY_PULLBACK"]:
        return "BUY_PULLBACK_CONFIRM"

    if phase == "BREAKOUT_CONFIRM":
        return "BUY_BREAKOUT_CONFIRM"

    if phase == "BREAKOUT_WATCH":
        return "WAIT_BREAKOUT_CONFIRM"

    if entry_stage in ["RECLAIM", "TURN"]:
        return "BUY_RECLAIM_CONFIRM"

    if breakout_state == "BREAKOUT" and rr >= MIN_RR_BREAKOUT:
        return "BUY_BREAKOUT"

    if dist is not None and dist > 4:
        return "WAIT_DISTANCE"

    if risk is not None and risk > 0.08:
        return "WAIT_RISK"

    # 中文註釋：v19.1.3 entry_profile 拆買點類型，避免所有 WAIT / BUY 都用同一套解釋。
    return "WAIT_CONFIRM"


def entry_quality_score(
    market_regime_value,
    phase,
    behavior,
    trend,
    structure,
    volume,
    rr,
    risk,
    dist,
    heat_state,
    bias
):

    score = 0

    if market_regime_value == "RISK_ON":
        score += 20
    elif market_regime_value == "NEUTRAL":
        score += 10
    elif market_regime_value == "RISK_OFF":
        score -= 15

    if phase in ["BREAKOUT_CONFIRM", "LOCK_LIMIT"]:
        score += 25
    elif phase in ["BREAKOUT", "BREAKOUT_WATCH", "SHAKEOUT", "HEALTHY_PULLBACK"]:
        score += 15
    elif phase in ["WEAK_REBOUND", "LIMIT_REBOUND"]:
        score -= 15
    elif phase in ["DISTRIBUTION", "FAILED_BREAKOUT"]:
        score -= 30

    if behavior in ["VOLUME_BREAKOUT", "LIMIT_LOCK"]:
        score += 15
    elif behavior in ["LOW_VOLUME_PULLBACK"]:
        score += 8
    elif behavior in ["WEAK_REBOUND", "LIMIT_REBOUND", "DISTRIBUTION_SPIKE"]:
        score -= 15

    if trend == "UP":
        score += 12
    elif trend == "DOWN":
        score -= 15

    if structure == "STRONG":
        score += 10
    elif structure == "NORMAL":
        score += 5
    elif structure == "WEAK":
        score -= 10

    if volume in ["STRONG", "EXPLOSIVE"]:
        score += 10
    elif volume == "WEAK" and behavior != "LIMIT_LOCK":
        score -= 8

    if rr >= 1.8:
        score += 12
    elif rr >= 1.2:
        score += 6
    elif rr > 0:
        score -= 4

    if risk is not None and 0 < risk <= 0.06:
        score += 8
    elif risk is not None and risk > 0.08:
        score -= 10

    if dist is not None:
        if -3 <= dist <= 2:
            score += 8
        elif dist > 6:
            score -= 10

    if heat_state == "EXTREME":
        score -= 18
    elif heat_state == "HOT":
        score -= 8

    if bias == "UP_CONFIRM":
        score += 8
    elif bias == "DOWN_CONFIRM":
        score -= 12

    if rr < 0.8:
        score = min(score, 49)
    elif rr < 1.2:
        score = min(score, 64)

    if heat_state == "HOT" and rr < 1.5:
        score = min(score, 64)

    # 中文註釋：v19.1.3 RR 是新進場品質硬門檻，低 RR 不允許被市場與突破分數灌成 A 級。
    return max(0, min(100, round(score)))


def entry_quality_label(score):

    if score >= 85:
        return "A+"

    if score >= 75:
        return "A"

    if score >= 65:
        return "B"

    if score >= 50:
        return "C"

    return "D"


def guard_low_volume_quality(
    score,
    metrics,
    structure,
    behavior,
    phase,
    heat_state
):

    ratio5 = metrics.get(
        "vol_ratio_5",
        1
    )

    ratio10 = metrics.get(
        "vol_ratio_10",
        ratio5
    )

    vol_ratio = min(
        ratio5,
        ratio10
    )

    if (
        vol_ratio < 0.8
        and heat_state == "HOT"
    ):
        # 中文註釋：v19.1.3 過熱觀察又低量時只保留觀察分，避免顯示成 A+ 強買點。
        return min(
            score,
            64
        )

    if (
        vol_ratio < 0.8
        and structure != "STRONG"
        and behavior not in [
            "LIMIT_LOCK",
            "VOLUME_BREAKOUT"
        ]
    ):
        # 中文註釋：v19.1.3 品質分與報文 V 倍率共用 5/10 日較低口徑，避免低量仍顯示 A+。
        return min(
            score,
            74
        )

    if (
        vol_ratio < 0.65
        and phase not in [
            "SHAKEOUT",
            "HEALTHY_PULLBACK"
        ]
    ):
        # 中文註釋：v19.1.3 極低量能只允許洗盤 / 健康回踩保留觀察分，其餘不得成為高品質進場。
        return min(
            score,
            64
        )

    return score


def quality_position(position, quality, profile):

    if quality in ["A+", "A"]:
        return position

    if quality == "B":
        return min(position, 0.25)

    if quality == "C":
        # 中文註釋：v19.1.3 C 品質只做觀察，不產生實際買入倉位，避免顯示觀察但策略仍下單。
        return 0

    # 中文註釋：v19.1.3 品質分不直接砍掉合理出手，而是把倉位降到對應風險級別。
    return 0


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

        "risk": kwargs.get(
            "risk",
            0 if decision in [
                "NO_TRADE",
                "FAIL"
            ] else None
        ),

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

        "period_metrics": kwargs.get(
            "period_metrics",
            {}
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
        ),

        "breakout_days": kwargs.get(
            "breakout_days",
            0
        ),

        "breakout_hold_days": kwargs.get(
            "breakout_hold_days",
            0
        ),

        "price_behavior": kwargs.get(
            "price_behavior",
            "NORMAL"
        ),

        "structure_phase": kwargs.get(
            "structure_phase",
            kwargs.get("lifecycle", "BASE")
        ),

        "market_regime": kwargs.get(
            "market_regime",
            "NEUTRAL"
        ),

        "multi_day_bias": kwargs.get(
            "multi_day_bias",
            "MIXED"
        ),

        "live_change": kwargs.get(
            "live_change"
        ),

        "entry_profile": kwargs.get(
            "entry_profile",
            "NONE"
        ),

        "entry_quality": kwargs.get(
            "entry_quality",
            "D"
        ),

        "confidence_score": kwargs.get(
            "confidence_score",
            0
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

    elif momentum == "STABLE_UP":
        score += 1

    elif momentum == "REVERSING":
        score -= 2

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
    ma20,
    metrics=None
):

    metrics = metrics or multi_period_metrics(
        closes,
        [1] * len(closes)
    )

    chg3 = metrics.get(
        "chg_3d",
        0
    )

    chg5 = metrics.get(
        "chg_5d",
        0
    )

    above_ma20_ratio = (

        sum(
            1 for c in closes[-5:]
            if c > ma20
        ) / 5
    )

    if (
        closes[-1] < ma20
        and chg3 < 0
        and chg5 < 0
        and above_ma20_ratio < 0.4
    ):
        return "WEAK"

    if (
        closes[-1] > ma20
        and chg3 > 0
        and chg5 >= 0
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
    volumes,
    metrics=None
):

    metrics = metrics or multi_period_metrics(
        closes,
        volumes
    )

    ratio = metrics.get(
        "vol_ratio_10",
        1
    )

    chg3 = metrics.get(
        "chg_3d",
        0
    )

    chg5 = metrics.get(
        "chg_5d",
        0
    )

    if (
        ratio > 1.5
        and chg3 > 0.03
        and chg5 >= 0
    ):
        return "EXPANSION"

    if (
        ratio > 1.5
        and chg3 < -0.02
        and chg5 < 0
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

    # 中文註釋：v19.1.3 Day1 改看最近 5 日是否首次站上，避免昨天/今天反覆切換。
    return (
        is_breakout(
            closes[-1],
            resistance
        )
        and breakout_days(
            closes[:-1],
            resistance,
            5
        ) == 0
    )


def breakout_days(
    closes,
    resistance,
    window=5
):

    return sum(
        1 for c in closes[-window:]
        if is_breakout(
            c,
            resistance
        )
    )


def breakout_hold_days(
    closes,
    resistance
):

    count = 0

    for close in reversed(closes):

        if not is_breakout(
            close,
            resistance
        ):
            break

        count += 1

    return count


# ================================
# 🔥 breakout fail
# ================================
def breakout_fail(
    closes,
    resistance
):

    breakout_lv = breakout_price(
        resistance
    )

    recent_breakout = breakout_days(
        closes[:-1],
        resistance,
        3
    ) > 0

    today_fail = (
        closes[-1] < breakout_lv * 0.99
    )

    # 中文註釋：v19.1.3 失敗需最近 3 日曾突破且今日跌回突破價下方，降低單日誤報。
    return (
        recent_breakout
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

        max(closes[-4:-1]) > breakout_lv
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
    trend,
    metrics=None
):

    metrics = metrics or multi_period_metrics(
        closes,
        [1] * len(closes)
    )

    return (

        is_breakout(
            closes[-1],
            resistance
        )

        and metrics.get(
            "chg_3d",
            0
        ) >= -0.015

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
    volume,
    metrics=None
):

    breakout_lv = breakout_price(
        resistance
    )

    hold_days = breakout_hold_days(
        closes,
        resistance
    )

    metrics = metrics or multi_period_metrics(
        closes,
        [1] * len(closes)
    )

    if is_fresh_breakout(
        closes,
        resistance
    ):
        return "BREAKOUT_DAY1"

    if hold_days >= 5:
        return "BREAKOUT_CONFIRM_5D"

    if hold_days >= 3:
        return "BREAKOUT_HOLD_3D"

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
        metrics.get("chg_3d", 0) > 0
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
# 🔥 calc risk / rr
# ================================
def calc_risk(
    price,
    stop
):

    if not price or not stop:
        return 0

    risk = (
        price - stop
    ) / price

    if risk <= 0:
        return 0

    # 中文註釋：risk 用比例輸出，condition_engine 以 8% 作為硬上限。
    return round(
        risk,
        4
    )


def calc_rr(
    price,
    stop,
    resistance,
    setup_type="breakout"
):

    if not price or not stop or not resistance:
        # 中文註釋：v19.1.3 RR 底層函式防止 None / 0 造成回測中斷，無效資料直接視為 RR 0。
        return 0

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

    if not price or not ma20:
        # 中文註釋：v19.1.3 過熱判斷遇到缺值時回到 0，避免 replay / 測試資料不完整時報錯。
        return 0

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


def wait_decision_type(
    breakout_state,
    rr,
    volume
):

    if breakout_state == "BREAKOUT":

        if rr < MIN_RR_BREAKOUT:
            return "wait_breakout_low_rr"

        return "wait_breakout_confirm"

    if breakout_state == "READY":

        if rr < MIN_RR_PREBREAK:
            return "wait_pre_breakout_low_rr"

        return "wait_pre_breakout"

    if volume == "WEAK":
        return "wait_volume"

    # 中文註釋：v19.1.3 WAIT 也保留語義類型，避免顯示層誤判事件與 Edge 全缺。
    return "none"


def watch_result(
    reason,
    m_score,
    m_grade,
    setup,
    execute,
    trend,
    trend_bias,
    volume,
    vp_state,
    structure,
    rr,
    risk,
    entry_stage,
    lifecycle,
    breakout_state,
    trade_state,
    heat_state,
    dominant,
    extended,
    ext_level,
    metrics,
    b_days,
    b_hold_days,
    strategy_tags
):

    # 中文註釋：v19.1.3 WATCH 是策略層觀察，不再用 BUY+0 倉位假裝可買。
    return build_result(
        decision="WAIT",
        decision_type=reason,
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
        risk=risk,
        entry_stage=entry_stage,
        lifecycle=lifecycle,
        breakout_state=breakout_state,
        trade_state=trade_state,
        heat_state=heat_state,
        dominant_state=dominant,
        extended=extended,
        extended_level=ext_level,
        period_metrics=metrics,
        breakout_days=b_days,
        breakout_hold_days=b_hold_days,
        wait_reason="WAIT_CONFIRM",
        **strategy_tags
    )


def can_buy(
    lifecycle,
    heat_state,
    trade_state,
    breakout_state,
    distance,
    price_behavior="NORMAL",
    entry_quality="D"
):

    if price_behavior in [
        "WEAK_REBOUND",
        "LIMIT_REBOUND",
        "LIMIT_LOCK"
    ]:
        return False

    if heat_state == "EXTREME":
        return False

    if trade_state == "AVOID":
        return False

    if lifecycle == "BASE" and breakout_state not in [
        "BREAKOUT",
        "READY"
    ]:
        return False

    if distance is not None and distance > 4:
        return False

    if entry_quality == "D":
        return False

    if entry_quality == "C":
        # 中文註釋：v19.1.3 C 品質歸入 WATCH，不進 BUY；B 以上才允許小倉或正常出手。
        return False

    # 中文註釋：v19.1.3 集中交易閘門加入價格行為與品質分，不靠少買，而是避免錯誤類型出手。
    return True


def holding_signal(
    result,
    price,
    avg_price,
    price_source="realtime",
    change=None,
    profit_taken_ratio=0
):

    pnl = (
        (price - avg_price) / avg_price * 100
        if avg_price else 0
    )

    warning_price = avg_price * 0.95
    hard_stop_price = avg_price * 0.92

    if pnl >= 8:
        warning_price = max(warning_price, price * 0.95)

    if pnl >= 15:
        hard_stop_price = max(hard_stop_price, avg_price * 1.02)

    phase = result.get("structure_phase")
    behavior = result.get("price_behavior")
    regime = result.get("market_regime")
    bias = result.get("multi_day_bias")
    decision = result.get("decision")
    heat = result.get("heat_state")
    extended = result.get("extended_level", 0)
    trend = result.get("trend")
    volume = result.get("volume_state")
    vp = result.get("volume_price_state")
    rr = result.get("rr", 0)
    dist = result.get("breakout_distance")
    quality = result.get("entry_quality", "D")
    confidence = result.get("confidence_score", 0)
    profile = result.get("entry_profile", "NONE")

    structure_broken = (
        phase in ["FAILED_BREAKOUT", "DISTRIBUTION"]
        or vp == "DISTRIBUTION"
        or (
            trend == "DOWN"
            and volume != "WEAK"
            and bias == "DOWN_CONFIRM"
        )
    )

    shakeout_protected = (
        phase in ["SHAKEOUT", "HEALTHY_PULLBACK"]
        or (
            behavior == "LOW_VOLUME_PULLBACK"
            and trend != "DOWN"
            and vp != "DISTRIBUTION"
            and bias != "DOWN_CONFIRM"
        )
        or (
            volume == "WEAK"
            and vp == "COILING"
            and phase not in ["FAILED_BREAKOUT", "DISTRIBUTION"]
            and trend != "DOWN"
            and bias != "DOWN_CONFIRM"
            and pnl > -5
        )
    )

    if pnl >= 15:
        hard_stop_price = max(
            hard_stop_price,
            price * 0.9,
            avg_price * 1.05
        )

    elif pnl >= 8:
        hard_stop_price = max(
            hard_stop_price,
            avg_price * 1.02
        )

    def add_blockers():
        blockers = []

        if change is not None and change >= 9.5:
            blockers.append("漲停不追")

        if pnl < 0:
            blockers.append("持倉未轉盈")
        elif pnl < 1:
            blockers.append("浮盈不足")

        if decision != "BUY":
            blockers.append("買點未成立")

        if regime != "RISK_ON":
            blockers.append("市場未轉強")

        if trend != "UP":
            blockers.append("趨勢未轉強")

        if volume == "WEAK":
            blockers.append("量能不足")

        if heat in ["HOT", "EXTREME"] or extended >= 2:
            blockers.append("過熱不加碼")

        if behavior in ["WEAK_REBOUND", "LIMIT_REBOUND", "LIMIT_LOCK"]:
            blockers.append("不追反彈/漲停")

        if quality not in ["A+", "A", "B"]:
            blockers.append("品質不足")

        if rr < 1.1:
            blockers.append("RR不足")

        if dist is None:
            blockers.append("位置不明")
        elif dist > 3:
            blockers.append("離突破太遠")

        if confidence < 65:
            blockers.append("信心不足")

        return list(dict.fromkeys(blockers))

    def payload(
        action,
        ratio,
        reason,
        level,
        signal_phase,
        allow_add=False,
        risk_level=2,
        add_status=None,
        add_blockers_value=None
    ):
        if add_status is None:
            if allow_add:
                add_status = "ALLOW"
            elif level in [
                "STOP_100",
                "REDUCE_50",
                "REDUCE_25",
                "TAKE_PROFIT_50",
                "TAKE_PROFIT_25",
                "WATCH",
                "HOLD_CORE"
            ]:
                add_status = "FORBID"
            else:
                add_status = "BLOCK"

        return {
            "action": action,
            "ratio": ratio,
            "reason": reason,
            "level": level,
            "phase": signal_phase,
            "allow_add": allow_add,
            "add_status": add_status,
            "add_blockers": add_blockers_value if add_blockers_value is not None else ([] if allow_add else add_blockers()),
            "risk_level": risk_level,
            "warning_price": warning_price,
            "hard_stop_price": hard_stop_price
        }

    if (
        price <= hard_stop_price
        and not shakeout_protected
    ):
        # 中文註釋：v19.1.3 硬停損需避開縮量洗盤，只有非洗盤情境跌破保護線才清倉。
        return payload("停損 100%", 1, "硬停損觸發", "STOP_100", "STOP_LOSS", False, 5)

    if (
        pnl <= -8
        and structure_broken
    ):
        # 中文註釋：v19.1.3 大幅虧損且結構已破才全停損，避免單靠虧損百分比被洗出去。
        return payload("停損 100%", 1, "破位轉弱", "STOP_100", "STOP_LOSS", False, 5)

    if structure_broken:
        ratio = 0.5 if pnl <= 0 else 0.25
        return payload(
            f"減碼 {int(ratio * 100)}%",
            ratio,
            "結構破壞，先降風險",
            "REDUCE_50" if ratio == 0.5 else "REDUCE_25",
            "RISK_REDUCE",
            False,
            4
        )

    if decision == "FAIL" or phase == "FAILED_BREAKOUT":
        ratio = 0.5 if pnl <= 0 else 0.25
        return payload(
            f"減碼 {int(ratio * 100)}%",
            ratio,
            "突破失敗，先降風險",
            "REDUCE_50" if ratio == 0.5 else "REDUCE_25",
            "RISK_REDUCE",
            False,
            4
        )

    if profit_taken_ratio >= 0.5 and pnl >= 0:
        return payload(
            "續抱核心倉",
            0,
            "已完成50%停利，等待冷卻",
            "HOLD_CORE",
            "CORE_HOLD",
            False,
            2
        )

    if (
        pnl >= 15
        and behavior == "LIMIT_LOCK"
        and extended >= 2
        and profit_taken_ratio < 0.25
    ):
        return payload(
            "停利 25%",
            0.25,
            "漲停過熱，保留核心倉",
            "TAKE_PROFIT_25",
            "LOCK_PROFIT",
            False,
            3
        )

    if pnl >= 8 and heat == "EXTREME":
        if profit_taken_ratio >= 0.25:
            return payload(
                "停利 25%",
                0.25,
                "已停利部分，極熱再降風險",
                "TAKE_PROFIT_25",
                "LOCK_PROFIT",
                False,
                4
            )

        return payload(
            "停利 50%",
            0.5,
            "極熱鎖利，避免末段反轉",
            "TAKE_PROFIT_50",
            "LOCK_PROFIT",
            False,
            4
        )

    if behavior == "LIMIT_LOCK":
        return payload(
            "續抱核心倉",
            0,
            "漲停鎖價，未見出貨",
            "HOLD_CORE",
            "CORE_HOLD",
            False,
            2
        )

    if shakeout_protected and pnl > -5:
        return payload(
            "洗盤觀察",
            0,
            "縮量回測，未見出貨",
            "SHAKEOUT",
            "SHAKEOUT_HOLD",
            False,
            2
        )

    if pnl < 0 and (regime == "RISK_OFF" or trend == "DOWN" or volume == "WEAK"):
        return payload("警戒", 0, "輕虧不加碼", "WATCH", "WATCH", False, 3)

    addable = (
        decision == "BUY"
        and price_source != "twse"
        and change is not None
        and change < 9.5
        and regime == "RISK_ON"
        and trend == "UP"
        and volume != "WEAK"
        and heat != "EXTREME"
        and behavior not in ["WEAK_REBOUND", "LIMIT_REBOUND", "LIMIT_LOCK"]
        and quality in ["A+", "A", "B"]
    )

    if addable and pnl >= 2 and rr >= 1.5 and dist is not None and dist <= 2 and confidence >= 80:
        return payload("加碼 30%", 0.3, "強勢突破確認", "ADD_30", "ADD_READY", True, 2)

    if addable and pnl >= 1 and rr >= 1.3 and dist is not None and dist <= 3 and confidence >= 72:
        return payload("加碼 20%", 0.2, "趨勢延續", "ADD_20", "ADD_READY", True, 2)

    if addable and pnl >= 0 and rr >= 1.1 and confidence >= 65:
        return payload("加碼 10%", 0.1, "小幅轉強", "ADD_10", "ADD_READY", True, 2)

    if decision == "BUY" and pnl >= 0 and rr < 1.3:
        # 中文註釋：v19.1.3 持倉加碼需完整證據鏈，RR 不足時續抱等待，不因 BUY 訊號直接加碼。
        return payload("續抱", 0, "突破成立，RR不足不加碼", "HOLD", "CORE_HOLD", False, 2)

    if phase == "BREAKOUT_WATCH" and pnl >= 0:
        return payload("續抱", 0, "接近突破，等確認再加碼", "HOLD", "ADD_WATCH", False, 2)

    if phase == "BREAKOUT_CONFIRM" and pnl >= 0:
        return payload("續抱", 0, "突破成立，等量價確認再加碼", "HOLD", "CORE_HOLD", False, 2)

    if pnl >= 0 and (regime == "RISK_OFF" or volume == "WEAK"):
        return payload("續抱", 0, "保成本，不加碼", "HOLD", "CORE_HOLD", False, 2)

    # 中文註釋：v19.1.3 持倉動作由策略層輸出，顯示層只換算股數與排版。
    return payload("續抱", 0, "不加碼", "HOLD", "CORE_HOLD", False, 1)


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

    elif entry_stage == "BREAKOUT_HOLD_3D":
        score += 2.2

    elif entry_stage == "BREAKOUT_CONFIRM_5D":
        score += 1.8

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
    change,
    ma5,
    ma20,
    closes,
    volumes
):

    # 中文註釋：v19.1.3 在策略入口統一補齊資料，避免後面 [-20:] / [-10:-5] 空窗。
    closes = normalize_series(
        closes
    )

    volumes = normalize_series(
        volumes
    )

    if not closes or not volumes:
        return build_result(
            decision="NO_TRADE",
            wait_reason="WAIT_DATA"
        )

    closes = merge_live_close(
        closes,
        price
    )

    metrics = multi_period_metrics(
        closes,
        volumes
    )

    support, resistance = (
        support_resistance(closes)
    )

    market = market_signal(
        closes,
        ma20,
        metrics
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
        volumes,
        metrics
    )

    structure = structure_state(
        closes,
        ma5,
        ma20
    )

    momentum = momentum_signal(
        metrics
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

    b_days = breakout_days(
        closes,
        resistance,
        5
    )

    b_hold_days = breakout_hold_days(
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
        volume,
        metrics
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

    breakout_dist = round(
        (
            breakout_price(resistance)
            - price
        ) / price * 100,
        2
    )

    rr = calc_rr(
        price,
        stop_candidate,
        resistance,
        "breakout"
    )

    risk = calc_risk(
        price,
        stop_candidate
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

    behavior = price_behavior_signal(
        change if change is not None else metrics.get("chg_1d", 0) * 100,
        market,
        trend,
        volume,
        vp_state,
        momentum
    )

    bias = multi_day_bias(
        metrics
    )

    regime = market_regime(
        market,
        trend,
        heat_state,
        m_grade
    )

    phase = structure_phase_signal(
        behavior,
        lifecycle,
        breakout_state,
        heat_state,
        trend,
        volume,
        structure,
        market,
        breakout_dist,
        bias
    )

    entry_profile = entry_profile_signal(
        phase,
        behavior,
        breakout_state,
        entry_stage,
        rr,
        risk,
        breakout_dist
    )

    confidence = entry_quality_score(
        regime,
        phase,
        behavior,
        trend,
        structure,
        volume,
        rr,
        risk,
        breakout_dist,
        heat_state,
        bias
    )

    confidence = guard_low_volume_quality(
        confidence,
        metrics,
        structure,
        behavior,
        phase,
        heat_state
    )

    quality = entry_quality_label(
        confidence
    )

    strategy_tags = {
        "price_behavior": behavior,
        "structure_phase": phase,
        "market_regime": regime,
        "multi_day_bias": bias,
        "live_change": change,
        "entry_profile": entry_profile,
        "entry_quality": quality,
        "confidence_score": confidence
    }

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

            risk=risk,

            entry_stage=entry_stage,

            lifecycle=lifecycle,

            breakout_state=breakout_state,

            trade_state=trade_state,

            heat_state=heat_state,

            dominant_state=dominant,

            extended=extended,

            extended_level=ext_level,

            period_metrics=metrics,

            breakout_days=b_days,

            breakout_hold_days=b_hold_days,

            wait_reason=get_wait_reason(
                trade_state
            ),

            **strategy_tags
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

            trend_bias=trend_bias,

            volume_state=volume,

            volume_price_state=vp_state,

            structure_state=structure,

            rr=0,

            risk=0,

            entry_stage="BREAKOUT_FAIL",

            lifecycle=lifecycle,

            breakout_state="FAIL",

            trade_state=trade_state,

            heat_state=heat_state,

            dominant_state=dominant,

            extended=extended,

            extended_level=ext_level,

            period_metrics=metrics,

            breakout_days=b_days,

            breakout_hold_days=b_hold_days,

            breakout_fail=True,

            **strategy_tags
        )

    # ================================
    # 🔥 fake breakout
    # ================================
    if fake_break:

        return build_result(

            decision="WAIT",

            decision_type="fake_breakout",

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

            risk=risk,

            entry_stage=entry_stage,

            lifecycle=lifecycle,

            breakout_state="FAKE_BREAK",

            trade_state=trade_state,

            heat_state=heat_state,

            dominant_state=dominant,

            extended=extended,

            extended_level=ext_level,

            period_metrics=metrics,

            breakout_days=b_days,

            breakout_hold_days=b_hold_days,

            wait_reason="WAIT_FAKE_BREAK"
            ,

            **strategy_tags
        )

    # ================================
    # 🔥 extreme
    # ================================
    if heat_state == "EXTREME":

        return build_result(

            decision="WAIT",

            decision_type="extended",

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

            risk=risk,

            entry_stage=entry_stage,

            lifecycle=lifecycle,

            breakout_state=breakout_state,

            trade_state="AVOID",

            heat_state="EXTREME",

            dominant_state=dominant,

            extended=extended,

            extended_level=ext_level,

            period_metrics=metrics,

            breakout_days=b_days,

            breakout_hold_days=b_hold_days,

            wait_reason="WAIT_EXTREME"
            ,

            **strategy_tags
        )

    if quality == "C":
        # 中文註釋：v19.1.3 C 品質在排除弱勢 / 失敗 / 假突破 / 極熱後才轉觀察，避免覆蓋更高優先級風險。
        return watch_result(
            "watch_quality_c",
            m_score,
            m_grade,
            setup,
            execute,
            trend,
            trend_bias,
            volume,
            vp_state,
            structure,
            rr,
            risk,
            entry_stage,
            lifecycle,
            breakout_state,
            trade_state,
            heat_state,
            dominant,
            extended,
            ext_level,
            metrics,
            b_days,
            b_hold_days,
            strategy_tags
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
            trend,
            metrics
        )
        and rr >= MIN_RR_STRONG
        and can_buy(
            lifecycle,
            heat_state,
            trade_state,
            breakout_state,
            breakout_dist,
            behavior,
            quality
        )
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

            position=round(
                quality_position(
                    pos,
                    quality,
                    entry_profile
                ),
                2
            ),

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

            risk=risk,

            entry_stage=entry_stage,

            lifecycle=lifecycle,

            breakout_state=breakout_state,

            trade_state=trade_state,

            heat_state=heat_state,

            dominant_state=dominant,

            extended=extended,

            extended_level=ext_level,

        period_metrics=metrics,

        breakout_days=b_days,

        breakout_hold_days=b_hold_days,

        **strategy_tags
        )

    # ================================
    # 🔥 breakout
    # ================================
    if (
        breakout_state == "BREAKOUT"
        and rr >= MIN_RR_BREAKOUT
        and can_buy(
            lifecycle,
            heat_state,
            trade_state,
            breakout_state,
            breakout_dist,
            behavior,
            quality
        )
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

            position=round(
                quality_position(
                    pos,
                    quality,
                    entry_profile
                ),
                2
            ),

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

            risk=risk,

            entry_stage=entry_stage,

            lifecycle=lifecycle,

            breakout_state="BREAKOUT",

            trade_state=trade_state,

            heat_state=heat_state,

            dominant_state=dominant,

            extended=extended,

            extended_level=ext_level,

            period_metrics=metrics,

            breakout_days=b_days,

            breakout_hold_days=b_hold_days,

            fresh_breakout=is_fresh_breakout(
                closes,
                resistance
            ),

            **strategy_tags
        )

    # ================================
    # 🔥 pre breakout
    # ================================
    if (
        trend == "UP"
        and volume != "WEAK"
        and structure != "WEAK"
        and breakout_ready
        and breakout_dist <= 3
        and rr >= MIN_RR_PREBREAK
        and can_buy(
            lifecycle,
            heat_state,
            trade_state,
            breakout_state,
            breakout_dist,
            behavior,
            quality
        )
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

            position=round(
                quality_position(
                    pos,
                    quality,
                    entry_profile
                ),
                2
            ),

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

            risk=risk,

            entry_stage=entry_stage,

            lifecycle=lifecycle,

            breakout_state="READY",

            trade_state=trade_state,

            heat_state=heat_state,

            dominant_state=dominant,

            extended=extended,

            extended_level=ext_level,

        period_metrics=metrics,

        breakout_days=b_days,

        breakout_hold_days=b_hold_days,

        **strategy_tags
        )

    # ================================
    # 🔥 wait
    # ================================
    return build_result(

        decision="WAIT",

        decision_type=wait_decision_type(
            breakout_state,
            rr,
            volume
        ),

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

        risk=risk,

        entry_stage=entry_stage,

        lifecycle=lifecycle,

        breakout_state=breakout_state,

        trade_state=trade_state,

        heat_state=heat_state,

        dominant_state=dominant,

        extended=extended,

        extended_level=ext_level,

            period_metrics=metrics,

            breakout_days=b_days,

            breakout_hold_days=b_hold_days,

        wait_reason=get_wait_reason(
            trade_state
        ),

        **strategy_tags
    )


# ================================
# 🔥 pick best stock
# ================================
def pick_best_stock(results_dict):

    best_name = None

    best_score = -999

    for name, result in results_dict.items():

        if result.get("decision") != "BUY":
            continue

        if result.get("action", 0) <= 0:
            continue

        if result.get("entry_quality") in ["C", "D"]:
            continue

        if result.get("entry_quality") not in ["A+", "A"]:
            continue

        if result.get("price_behavior") in [
            "WEAK_REBOUND",
            "LIMIT_REBOUND",
            "LIMIT_LOCK"
        ]:
            continue

        if result.get("structure_phase") == "SHAKEOUT":
            # 中文註釋：v19.1.3 洗盤是持倉保護語義，未持倉不得被選為最強新進場。
            continue

        if result.get("heat_state") in ["HOT", "EXTREME"]:
            continue

        if result.get("trade_state") == "AVOID":
            continue

        if result.get("volume_state") == "WEAK":
            continue

        metrics = result.get(
            "period_metrics",
            {}
        )

        ratio5 = metrics.get(
            "vol_ratio_5",
            1
        )

        ratio10 = metrics.get(
            "vol_ratio_10",
            ratio5
        )

        vol_ratio = min(
            ratio5,
            ratio10
        )

        if (
            vol_ratio < 0.8
            and result.get("structure_state") != "STRONG"
            and result.get("price_behavior") != "VOLUME_BREAKOUT"
        ):
            # 中文註釋：v19.1.3 最強股需有足夠量能或攻擊結構，避免低量小倉觀察被選成最強。
            continue

        if result.get("lifecycle") == "BASE":
            continue

        if result.get("rr", 0) < 1:
            continue

        score = result.get(
            "strength",
            0
        )

        score += result.get("confidence_score", 0) / 20

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

        # 中文註釋：v19.1.3 最強股加入入場品質與信心分，不讓弱反彈 / 漲停追價混入。
        result["rank_score"] = round(
            score,
            2
        )

        if score > best_score:

            best_score = score

            best_name = name

    return best_name, best_score
