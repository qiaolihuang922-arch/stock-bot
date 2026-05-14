# ================================
# 🔥 analysis.py（FINAL v18.2｜CONFLICT GUARD）
# ================================

# 🔒 VERSION LOCK
# - ✅ 保留既有 semantic engine
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
# - ✅ risk 欄位回補，對齊 condition_engine
# - ✅ 短資料保護，避免 K 線不足時誤判
# - ✅ rank_score 與 strength 分離
# - ✅ v18.1 盤中即時價寫入策略 K 線
# - ✅ v18.1 3 / 5 / 10 日多週期趨勢判斷
# - ✅ v18.1 breakout 狀態改用持續天數，降低單日重複誤報
# - ✅ v18.2 弱勢 / 過熱 / BASE 交易衝突防護
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
# 🔥 v18.1 資料保護 / 多週期工具
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

    # 中文註釋：v18.1 將盤中即時價覆蓋最後一根 K，讓策略判斷與報文價格一致。
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

    # 中文註釋：v18.1 統一輸出 1 / 3 / 5 / 10 日變化，避免單日訊號反覆誤判。
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

    # 中文註釋：v18.1 Day1 改看最近 5 日是否首次站上，避免昨天/今天反覆切換。
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

    # 中文註釋：v18.1 失敗需最近 3 日曾突破且今日跌回突破價下方，降低單日誤報。
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

    # 中文註釋：v18.2 WAIT 也保留語義類型，避免顯示層誤判事件與 Edge 全缺。
    return "none"


def can_buy(
    lifecycle,
    heat_state,
    trade_state,
    breakout_state,
    distance
):

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

    # 中文註釋：v18.2 集中交易閘門，避免整理 / 過熱 / 遠離突破仍被 BUY。
    return True


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
    ma5,
    ma20,
    closes,
    volumes
):

    # 中文註釋：v18.1 在策略入口統一補齊資料，避免後面 [-20:] / [-10:-5] 空窗。
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
            )
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

            breakout_fail=True
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
            breakout_dist
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

        breakout_hold_days=b_hold_days
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
            breakout_dist
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
        and breakout_dist <= 3
        and rr >= MIN_RR_PREBREAK
        and can_buy(
            lifecycle,
            heat_state,
            trade_state,
            breakout_state,
            breakout_dist
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

        breakout_hold_days=b_hold_days
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
        )
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

        if result.get("heat_state") == "EXTREME":
            continue

        if result.get("trade_state") == "AVOID":
            continue

        if result.get("volume_state") == "WEAK":
            continue

        if result.get("lifecycle") == "BASE":
            continue

        if result.get("rr", 0) < 1:
            continue

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

        # 中文註釋：v18.2 最強股只從有效 BUY 候選中挑選，不讓禁追 / 弱量 / BASE 混入。
        result["rank_score"] = round(
            score,
            2
        )

        if score > best_score:

            best_score = score

            best_name = name

    return best_name, best_score
