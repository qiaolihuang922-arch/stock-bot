# ================================
# FINAL UI（v19.0｜Daily Signal Database）
# ================================

from datetime import datetime
import pytz

from services.stock_api import (
    get_twse,
    get_yahoo,
    get_realtime_price
)

from services.analysis import (
    strategy,
    pick_best_stock,
    BREAKOUT_THRESHOLD,
    holding_signal as strategy_holding_signal
)

from core.condition_engine import (
    condition_engine,
    summarize_conditions
)

from services.signal_store import record_daily_signals

tz = pytz.timezone("Asia/Taipei")

VERSION = "v19.0"


# ================================
# 🔒 股票池
# ================================
stocks = {

    "緯創": "3231",
    "建準": "2421",
    "智原": "3035",
    "聯電": "2303",
    "群創": "3481",

    "華邦電": "2344",
    "技嘉": "2376",
    "南亞科": "2408",

    "英業達": "2356",
    "仁寶": "2324",

    "光寶科": "2301",
    "旺宏": "2337"
}


# ================================
# 🔒 持倉
# ================================
holdings = {

    "英業達": {
        "shares": 1100,
        "avg_price": 50.22
    },

    "智原": {
        "shares": 50,
        "avg_price": 209
    },

    "光寶科": {
        "shares": 50,
        "avg_price": 208.5
    },

    "緯創": {
        "shares": 440,
        "avg_price": 140.92
    }
}


# ================================
# 🔥 safe utils
# ================================
def safe_list(data, n=20):

    if not data:
        return None

    if len(data) < n:
        # 中文註釋：短資料補在前段，避免最新價格被重複放大。
        return [data[0]] * (n - len(data)) + data

    return data


def safe_round(val, n=2):

    try:

        if val is None:
            return "-"

        return round(float(val), n)

    except:
        return "-"


def signed_pct(val):

    try:
        return f"{float(val):+.2f}%"

    except:
        return "-"


def calc_shares(shares, ratio):

    try:
        if ratio <= 0:
            # 中文註釋：v18.8 續抱 / 警戒不應顯示 1 股，0 比例直接回傳 0。
            return 0

        return max(
            int(round(shares * ratio)),
            1
        )

    except:
        return 0


# ================================
# 🔥 market map
# ================================
MARKET_MAP = {

    "A+": "🟢 極強",
    "A": "🟢 極強",
    "B": "🟡 偏強",
    "C": "🟠 中性",
    "D": "🔴 弱勢"
}


# ================================
# 🔥 wait map
# ================================
WAIT_MAP = {

    "WAIT_EXTENDED": "過熱",
    "WAIT_EXTREME": "禁追",
    "WAIT_RR": "RR不足",
    "WAIT_VOLUME": "等量",
    "WAIT_CONFIRM": "等確認",
    "WAIT_EXECUTION": "觀察",
    "WAIT_TREND": "弱勢",
    "WAIT_FAKE_BREAK": "假突破",
    "WAIT_DATA": "資料不足"
}


# ================================
# 🔥 condition label
# ================================
CONDITION_LABELS = {

    "market": "市場",
    "structure": "結構",
    "trend": "趨勢",
    "volume": "量能",
    "event": "事件",
    "edge": "Edge",
    "risk": "風控",
    "rr": "RR"
}


# ================================
# 🔥 entry map
# ================================
ENTRY_MAP = {

    "BREAKOUT_DAY1": "🔥 Day1",
    "CONFIRM_DAY2": "🚀 Day2",
    "BREAKOUT_HOLD_3D": "🚀 站穩3日",
    "BREAKOUT_CONFIRM_5D": "🚀 確認5日",
    "TURN": "↗ 轉強",
    "PULLBACK": "↘ 拉回",
    "RECLAIM": "↗ 收復",
    "BREAKOUT_FAIL": "❌ 失敗"
}


# ================================
# 🔥 market phase
# ================================
def get_market_phase():

    now = datetime.now(tz)

    h, m = now.hour, now.minute

    if now.weekday() >= 5:
        return "假日"

    if h == 8 and 30 <= m < 40:
        return "盤前"

    if 9 <= h < 13:
        return "盤中"

    if h == 13 and m >= 20:
        return "收盤"

    return "盤後"


# ================================
# 🔥 realtime merge
# ================================
def get_live_price_data(
    realtime,
    yahoo,
    twse_price,
    twse_change
):

    if realtime and yahoo:

        r_price = realtime[0]
        r_change = realtime[1]
        y_price = yahoo[0]
        y_change = yahoo[1]

        if abs(r_change) >= 8:
            # 中文註釋：v18.5 接近漲跌停時 Yahoo 常有延遲或昨收價，優先採用 TWSE 即時成交 / 盘口價。
            return r_price, r_change, "realtime"

        if (
            y_price
            and y_change is not None
            and abs(y_change) < 0.3
            and abs(r_change) >= 3
        ):
            # 中文註釋：v18.5 Yahoo 幾乎不動但 TWSE 即時價明顯變動時，視為 Yahoo 舊價。
            return r_price, r_change, "realtime"

        if y_price and abs(r_price - y_price) / y_price <= 0.02:
            # 中文註釋：v18.4 即時價與 Yahoo 差距 2% 內才採用，降低異常報價誤判。
            return r_price, r_change, "realtime"

        return yahoo[0], yahoo[1], "yahoo"

    if realtime:
        return realtime[0], realtime[1], "realtime"

    if yahoo:
        return yahoo[0], yahoo[1], "yahoo"

    return twse_price, twse_change, "twse"


def price_label_for_source(source):

    phase = get_market_phase()

    if phase == "假日":
        # 中文註釋：v18.8.4 假日不顯示 realtime/yahoo/twse 來源，避免被誤解為即時成交。
        return "最近價格"

    if phase == "盤中":

        if source == "twse":
            return "盤中參考(twse)"

        if source == "yahoo":
            return "盤中參考(yahoo)"

        return f"盤中即時({source})"

    # 中文註釋：v18.4 twse 不是盤中即時價，避免報文誤導。
    if source == "twse":
        return "日線(twse)"

    return f"價格({source})"


# ================================
# 🔥 結構進度
# 用來計算 S x/5
# ================================
def structure_progress(
    closes,
    ma5,
    ma20
):

    try:

        closes = safe_list(closes)

        if not closes:
            return 0

        score = 0

        if max(closes[-5:]) > max(closes[-10:-5]):
            score += 1

        if min(closes[-5:]) > min(closes[-10:-5]):
            score += 1

        if ma5 > ma20:
            score += 1

        if closes[-1] > ma5:
            score += 1

        if closes[-1] > ma20:
            score += 1

        return score

    except:
        return 0


# ================================
# 🔥 volume ratio
# V x倍率
# ================================
def volume_ratio(volumes):

    try:

        avg10 = (
            sum(volumes[-10:])
            / max(len(volumes[-10:]), 1)
        )

        if avg10 <= 0:
            return 1

        return round(
            volumes[-1] / avg10,
            2
        )

    except:
        return 1


# ================================
# 🔥 breakout distance
# 距離突破百分比
# ================================
def breakout_distance(
    price,
    closes
):

    try:

        closes = safe_list(closes)

        resistance = max(
            closes[-20:-3]
        )

        breakout_price = (
            resistance
            * (1 + BREAKOUT_THRESHOLD)
        )

        return round(

            (
                breakout_price - price
            ) / price * 100,

            2
        )

    except:
        return None


# ================================
# 🔥 semantic state
# 合併：
# dominant_state
# lifecycle
# breakout phase
# ================================
def semantic_state(result):

    holding_decision = result.get("_holding_decision") or {}

    if holding_decision.get("level") == "SHAKEOUT":
        # 中文註釋：v19.0 持倉已判定洗盤時，型態主語優先顯示洗盤，避免和弱勢文字衝突。
        return "🧽 洗盤回測"

    phase = result.get("structure_phase")

    phase_map = {
        "LOCK_LIMIT": "🚀 漲停鎖價",
        "LIMIT_REBOUND": "↗ 漲停反彈",
        "BREAKOUT_CONFIRM": "🚀 突破確認",
        "BREAKOUT": "🚀 主升突破",
        "BREAKOUT_WATCH": "👀 突破觀察",
        "SHAKEOUT": "🧽 洗盤回測",
        "HEALTHY_PULLBACK": "↘ 健康回踩",
        "WEAK_REBOUND": "↗ 弱勢反彈",
        "FAILED_BREAKOUT": "❌ 突破失敗",
        "DISTRIBUTION": "📦 高位出貨",
        "EXTENDED_RISK": "🚨 極熱加速",
        "BASE": "⏳ 整理蓄勢",
        "WEAK": "⚠ 弱勢"
    }

    if phase in phase_map:
        # 中文註釋：v18.7 型態主語改讀策略層 structure_phase，避免顯示層自行推論漲停 / 洗盤。
        return phase_map[phase]

    dominant = result.get(
        "dominant_state"
    )

    lifecycle = result.get(
        "lifecycle"
    )

    # breakout fail
    if dominant == "FAILED":
        return "❌ 突破失敗"

    # extreme
    if dominant == "EXTREME":
        return "🚨 極熱加速"

    # late trend
    if dominant == "LATE":
        return "⚠ 主升末段"

    # breakout trend
    if lifecycle == "BREAKOUT_TREND":

        if result.get("fresh_breakout"):
            return "🚀 主升突破（初期）"

        return "🚀 主升突破"

    # normal trend
    if lifecycle == "TREND":
        return "📈 趨勢延續"

    # distribution
    if lifecycle == "DISTRIBUTION":
        return "📦 高位出貨"

    # base
    if lifecycle == "BASE":
        return "⏳ 整理蓄勢"

    return "⚠ 弱勢"


# ================================
# 🔥 semantic trade
# 合併：
# trade_state
# heat_state
# ================================
def semantic_trade(result):

    holding_decision = result.get("_holding_decision") or {}

    if holding_decision.get("level") == "SHAKEOUT":
        # 中文註釋：v19.0 持倉洗盤的低量是保護條件，不再顯示成一般無量交易缺口。
        return "🧽 縮量洗盤"

    decision = result.get(
        "decision"
    )

    behavior = result.get("price_behavior")

    trade = result.get(
        "trade_state"
    )

    heat = result.get(
        "heat_state"
    )

    if decision == "FAIL":
        # 中文註釋：v18.5 突破失敗優先於禁追 / 無量，避免同一檔同時顯示兩種互斥交易狀態。
        return "✅ 可交易"

    if behavior == "LIMIT_LOCK":
        return "🚨 不追高"

    if behavior == "LIMIT_REBOUND":
        return "👀 隔日確認"

    if heat == "EXTREME":
        return "🚨 禁追"

    if trade == "EXTENDED":
        return "🌡 過熱觀察"

    if trade == "LATE_ENTRY":
        return "⚠ RR不足"

    if trade == "NO_VOLUME":
        return "⚠ 無量"

    return "✅ 可交易"


# ================================
# 🔥 semantic structure
# 合併：
# structure
# volume
# vp_state
# ================================
def semantic_structure(result):

    vp = result.get(
        "volume_price_state"
    )

    volume = result.get(
        "volume_state"
    )

    structure = result.get(
        "structure_state"
    )

    # 出貨
    if vp == "DISTRIBUTION":
        return "📦 高檔出貨"

    # 攻擊量
    if (
        vp == "EXPANSION"
        and volume in [
            "STRONG",
            "EXPLOSIVE"
        ]
    ):
        return "🚀 攻擊量"

    # 收縮
    if vp == "COILING":
        return "🔹 收縮整理"

    # 趨勢量
    if structure == "STRONG":
        return "📈 趨勢量"

    return "⏳ 普通"


# ================================
# 🔥 semantic position
# semantic + numeric coexist
# ================================
def semantic_position(dist):

    if dist is None:
        return None

    if dist < 0:
        return f"🚀 已突破（{dist}%）"

    if dist < 1:
        return f"🔥 臨界突破（{dist}%）"

    if dist < 4:
        return f"👀 接近突破（{dist}%）"

    return f"⏳ 遠離突破（{dist}%）"


# ================================
# 🔥 semantic reason
# 評級原因
# ================================
def semantic_reason(result):

    rr = result.get("rr", 0)

    decision = result.get(
        "decision"
    )

    trade = result.get(
        "trade_state"
    )

    vp = result.get(
        "volume_price_state"
    )

    heat = result.get(
        "heat_state"
    )

    behavior = result.get("price_behavior")
    phase = result.get("structure_phase")
    quality = result.get("entry_quality")
    confidence = result.get("confidence_score")
    holding_decision = result.get("_holding_decision")

    if holding_decision:
        level = holding_decision.get("level")

        if level in ["TAKE_PROFIT_25", "TAKE_PROFIT_50"]:
            return "持倉停利"

        if level in ["REDUCE_25", "REDUCE_50", "STOP_100"]:
            return "持倉風控"

        if level == "SHAKEOUT":
            return "縮量洗盤"

        if level in ["HOLD", "HOLD_CORE"]:
            return "持倉續抱"

        if level == "WATCH":
            return "持倉警戒"

        if level in ["ADD_10", "ADD_20", "ADD_30"]:
            return "持倉加碼"

    dist = result.get(
        "breakout_distance"
    )

    if decision == "FAIL":
        # 中文註釋：v18.5 失敗股評級原因固定為突破失敗，不再被過熱或遠離觸發覆蓋。
        return "突破失敗"

    if quality in ["A+", "A"] and confidence:
        return f"高品質{quality}"

    if quality == "B":
        return "小倉品質"

    if quality == "C":
        return "等待確認"

    if quality == "D":
        return "不交易"

    if behavior == "LIMIT_LOCK":
        return "漲停鎖價"

    if behavior == "LIMIT_REBOUND":
        return "弱勢漲停"

    if phase == "SHAKEOUT":
        return "縮量洗盤"

    if heat == "EXTREME":
        return "過熱風險"

    if decision == "NO_TRADE":

        if trade == "NO_VOLUME":
            return "量能不足"

        if result.get("trend") == "DOWN":
            return "趨勢轉弱"

        # 中文註釋：v18.4 NO_TRADE 不再用高 RR 當評級原因，避免弱勢股被誤解成機會。
        return "不交易"

    if should_hide_rr(result):

        # 中文註釋：v18.5 RR 被隱藏時，評級原因同步回到市場 / 趨勢 / 量能主因，避免文字仍提示高 RR。
        if result.get("market_grade") == "D":
            return "市場弱勢"

        if trade == "NO_VOLUME" or result.get("volume_state") == "WEAK":
            return "量能不足"

        if dist is not None and dist > 4:
            return "遠離觸發"

        return "不交易"

    if dist is not None and dist > 4:
        return "遠離觸發"

    if rr >= 3:
        return "高RR"

    if vp == "EXPANSION":
        return "突破量能"

    if trade == "LATE_ENTRY":
        return "末段弱RR"

    if trade == "NO_VOLUME":
        return "量能不足"

    return "結構正常"


def semantic_condition_labels(
    result,
    condition_items
):

    holding_decision = result.get("_holding_decision")
    holding_add_ready = (
        holding_decision
        and holding_decision.get("level") in [
            "ADD_30",
            "ADD_20",
            "ADD_10"
        ]
    )

    if (
        result.get("decision") == "BUY"
        and result.get("action", 0) > 0
        and (not holding_decision or holding_add_ready)
    ):
        quality = result.get("entry_quality", "D")
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

        if result.get("heat_state") == "HOT" or vol_ratio < 0.8:
            labels = ["風控"]
            if vol_ratio < 0.8:
                labels.append("RR足夠")
                labels.append("低量觀察")
            elif result.get("heat_state") == "HOT":
                labels.append("RR足夠")
                labels.append("過熱觀察")
            # 中文註釋：v18.8.4 觀察型買點明確標出 RR 足夠但量能/過熱未確認。
            return labels

        if quality in ["A+", "A"]:
            return ["完整", "風控", f"品質{quality}"]

        return ["風控", "RR", "觀察"]

    labels = []
    dist = result.get("breakout_distance")
    profile = result.get("entry_profile")

    if result.get("decision_type") == "watch_quality_c":
        watch_labels = []
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

        if result.get("rr", 0) >= 1:
            watch_labels.append("RR足夠")

        if vol_ratio < 0.8:
            watch_labels.append("低量觀察")

        if result.get("heat_state") == "HOT":
            watch_labels.append("過熱觀察")

        if not watch_labels:
            watch_labels.append("品質待確認")

        # 中文註釋：v18.9.3 WATCH_C 改用觀察條件，不再顯示事件 / Edge / RR 不足假缺口。
        return watch_labels[:3]

    profile_reason = {
        "WAIT_LIMIT_REBOUND": "漲停反彈待確認",
        "WAIT_WEAK_REBOUND": "弱反彈待確認",
        "WAIT_DISTANCE": "遠離觸發",
        "WAIT_RISK": "風控不足",
        "WAIT_BREAKOUT_CONFIRM": "等突破確認",
        "WAIT_LIMIT_LOCK": "漲停不追高"
    }

    if profile in profile_reason:
        labels.append(profile_reason[profile])

    holding_decision = result.get("_holding_decision")

    if holding_decision and holding_decision.get("level") == "HOLD":
        note = holding_decision.get("note")

        if "RR不足" in note:
            return ["RR不足，不加碼"]

        return []

    if holding_decision and holding_decision.get("level") == "WATCH":
        return []

    # 中文註釋：v18.5 缺口改成交易語意，避免直接露出 event / Edge 造成報文像假錯誤。
    for item in condition_items:

        if item == "market":
            if result.get("market_grade") == "D":
                label = "市場弱"
            else:
                # 中文註釋：v18.7 中性盤不是弱勢盤，缺口文字改成未轉強避免顯示衝突。
                label = "市場未強"
        elif item == "trend":
            label = "趨勢未轉強"
        elif item == "volume":
            label = "量能不足"
        elif item in ["event", "edge"] and dist is not None and dist > 4:
            label = "遠離觸發"
        elif item == "event":
            label = "事件不足"
        elif item == "edge":
            label = "Edge不足"
        elif item == "risk":
            label = "風控不足"
        elif item == "rr":
            label = "RR不足"
        elif item == "structure":
            label = "結構不足"
        else:
            label = CONDITION_LABELS.get(item, item)

        if label not in labels:
            labels.append(label)

    return labels[:3]


def should_hide_rr(result):

    decision = result.get("decision")
    dist = result.get("breakout_distance")

    if decision in ["NO_TRADE", "FAIL"]:
        return True

    if result.get("heat_state") == "EXTREME":
        return True

    if result.get("price_behavior") in [
        "LIMIT_LOCK",
        "LIMIT_REBOUND",
        "WEAK_REBOUND"
    ]:
        return True

    if result.get("market_grade") == "D":
        return True

    if result.get("volume_state") == "WEAK":
        return True

    if dist is not None and dist > 4:
        return True

    # 中文註釋：v18.5 弱勢 / 遠離 / 無量時 RR 只作內部判斷，不在報文顯示成可交易誘因。
    return False


def should_show_entry_suffix(
    result,
    holding_decision
):

    if result.get("decision") == "FAIL":
        # 中文註釋：v18.5 失敗標題已經表達主狀態，不再追加 BREAKOUT_FAIL 後綴造成重複。
        return False

    if result.get("entry_profile") in [
        "WAIT_LIMIT_REBOUND",
        "WAIT_WEAK_REBOUND",
        "WAIT_DISTANCE",
        "WAIT_LIMIT_LOCK"
    ]:
        # 中文註釋：v18.9.3 觀察 / 不交易型態不掛 Day1，避免弱反彈被誤看成有效突破日。
        return False

    if result.get("structure_phase") in [
        "WEAK_REBOUND",
        "LIMIT_REBOUND"
    ]:
        # 中文註釋：v18.9.3 弱勢反彈和漲停反彈需要隔日確認，不顯示突破日後綴。
        return False

    if not holding_decision:
        return True

    if holding_decision.get("level") in [
        "ADD_30",
        "ADD_20",
        "ADD_10"
    ]:
        return True

    if result.get("decision") == "BUY":
        return True

    # 中文註釋：v18.5 持倉股以持倉動作為主，非加碼情境不顯示收復 / 站穩等短線後綴。
    return False


# ================================
# 🔥 action
# ================================
def get_action(result):

    decision = result.get(
        "decision"
    )

    if decision == "FAIL":
        return "❌"

    if result.get("action_type") == "BUY":

        quality = result.get("entry_quality", "D")
        position = result.get("action", 0)

        if position <= 0:
            return "⏳"

        if quality == "B":
            return f"🟡 {round(position * 100)}%"

        if quality in ["C", "D"]:
            # 中文註釋：v18.8.4 C/D 品質只顯示觀察，不顯示倉位比例避免被當成買進指令。
            return "⏳"

        if result.get("extended_level", 0) == 2:
            return (
                f"🟡 "
                f"{round(position * 100)}%"
            )

        return (
            f"🟢 "
            f"{round(position * 100)}%"
        )

    return "⏳"


# ================================
# 🔥 final label
# ================================
def final_label(result):

    decision = result.get(
        "decision"
    )

    behavior = result.get("price_behavior")

    if behavior == "LIMIT_LOCK":
        return "漲停鎖價"

    if behavior == "LIMIT_REBOUND":
        return "漲停反彈"

    if decision == "BUY":
        quality = result.get("entry_quality", "D")

        if quality == "B":
            return "小倉觀察"

        if quality in ["C", "D"]:
            return "觀察"

        if result.get("extended_level", 0) == 2:
            return "小倉觀察"

        return "進場"

    if result.get("decision_type") == "watch_quality_c":
        # 中文註釋：v18.9.3 C 品質是策略層觀察，不顯示成「等確認」以免像缺少資料。
        return "觀察"

    if decision == "FAIL":
        return "失敗"

    if decision == "NO_TRADE":
        return "不交易"

    return WAIT_MAP.get(
        result.get("wait_reason"),
        "觀察"
    )


def holding_status(
    result,
    price,
    avg_price,
    shares,
    price_source="realtime",
    change=None
):

    signal = strategy_holding_signal(
        result,
        price,
        avg_price,
        price_source,
        change
    )

    ratio = signal.get("ratio", 0)
    action_shares = (
        shares
        if ratio >= 1
        else calc_shares(shares, ratio)
    )

    # 中文註釋：v18.7 持倉策略由 analysis.py 輸出，generator.py 只換算股數與維持既有報文格式。
    return {
        "action": signal.get("action", "續抱"),
        "shares": action_shares,
        "note": signal.get("reason", "不加碼"),
        "level": signal.get("level", "HOLD"),
        "warning_price": signal.get("warning_price"),
        "hard_stop_price": signal.get("hard_stop_price"),
        "phase": signal.get("phase"),
        "allow_add": signal.get("allow_add", False),
        "risk_level": signal.get("risk_level", 1)
    }

def holding_risk_text(
    decision
):

    warning = safe_round(
        decision.get("warning_price")
    )

    hard_stop = safe_round(
        decision.get("hard_stop_price")
    )

    return f"警戒 {warning} ｜停損 {hard_stop}"


def holding_position_text(
    decision,
    current_shares
):

    action_shares = decision.get("shares", 0)
    level = decision.get("level")

    if level == "STOP_100":
        return "清倉後 0股"

    if level in [
        "REDUCE_50",
        "REDUCE_25",
        "TAKE_PROFIT_50",
        "TAKE_PROFIT_25"
    ]:
        remain = max(
            current_shares - action_shares,
            0
        )
        return f"剩餘 {remain}股 ｜保留核心倉"

    if level in [
        "ADD_30",
        "ADD_20",
        "ADD_10"
    ]:
        target = current_shares + action_shares
        return f"目標 {target}股 ｜分批加碼"

    if level == "SHAKEOUT":
        return f"維持 {current_shares}股 ｜等量價確認"

    if level == "HOLD_CORE":
        return f"維持 {current_shares}股 ｜不追高加碼"

    # 中文註釋：v18.7 持倉輸出補上倉位結果，讓加碼 / 減碼 / 洗盤觀察後的股數更清楚。
    return f"維持 {current_shares}股 ｜不加碼"


# ================================
# 🔥 render stock
# ================================
def render_stock(
    name,
    data
):

    result = data["result"]

    price = data["price"]
    change = data["change"]
    price_source = data.get(
        "price_source",
        "twse"
    )
    holding = data.get("holding")

    # 中文註釋：v18.4 顯示層只讀 condition_engine 映射結果，不自行判斷交易條件。
    conditions = condition_engine(
        result
    )

    condition_items = summarize_conditions(
        conditions,
        result.get("decision")
    )

    # S 分數
    struct = structure_progress(
        data["closes"],
        data["ma5"],
        data["ma20"]
    )
    data["structure_score"] = struct

    # V 倍率
    vol = volume_ratio(
        data["volumes"]
    )
    data["volume_ratio"] = vol

    # breakout 距離
    dist = breakout_distance(
        price,
        data["closes"]
    )
    data["breakout_distance"] = dist

    result["breakout_distance"] = dist

    # entry stage
    entry = ENTRY_MAP.get(
        result.get("entry_stage"),
        ""
    )

    holding_decision = None
    pnl = None

    if holding:

        pnl = (
            (price - holding["avg_price"])
            / holding["avg_price"]
            * 100
        )

        holding_decision = holding_status(
            result,
            price,
            holding["avg_price"],
            holding["shares"],
            price_source,
            change
        )

        result["_holding_decision"] = holding_decision
        data["holding_decision"] = holding_decision

    holding_add_ready = (
        holding_decision
        and holding_decision.get("level") in [
            "ADD_30",
            "ADD_20",
            "ADD_10"
        ]
    )

    if holding_decision and not holding_add_ready:
        # 中文註釋：v18.9.3 持倉非加碼完全隱藏買點條件，避免「RR -」卻顯示 RR 足夠或洗盤又顯示量能不足。
        condition_items = []

    # header
    if holding:

        header = (
            f"【{name}】 "
            f"📌 持倉 ｜{holding_decision['action']}"
        )

    else:

        header = (

            f"【{name}】 "
            f"{get_action(result)} "
            f"{final_label(result)}"
        )

    if (
        entry
        and result.get("decision") != "NO_TRADE"
        and not (
            result.get("entry_quality") == "D"
            and result.get("market_grade") == "D"
        )
        and should_show_entry_suffix(
        result,
        holding_decision
        )
    ):
        header += f" ｜{entry}"

    msg = header + "\n"

    if holding:

        # 中文註釋：v18.4 只對已持有股票增加持倉管理資訊，其餘原始技術資料全部保留。
        msg += (
            f"├─ 持倉："
            f"{holding['shares']}股"
            f" ｜均價 {safe_round(holding['avg_price'])}"
            f" ｜損益 {signed_pct(pnl)}\n"
        )

        msg += (
            f"├─ 操作："
            f"{holding_decision['action']}"
        )

        if holding_decision["shares"] > 0:
            msg += f" {holding_decision['shares']}股"

        msg += (
            f" ｜{holding_decision['note']}\n"
        )

        msg += (
            f"├─ 倉位："
            f"{holding_position_text(holding_decision, holding['shares'])}\n"
        )

        msg += (
            f"├─ 風控："
            f"{holding_risk_text(holding_decision)}\n"
        )

    # ================================
    # 🔥 型態
    # ================================
    msg += (
        f"├─ 型態："
        f"{semantic_state(result)}\n"
    )

    # ================================
    # 🔥 市場
    # ================================
    msg += (
        f"├─ 市場："
        f"{MARKET_MAP.get(result.get('market_grade'), '🟡 偏強')}\n"
    )

    # ================================
    # 🔥 結構
    # ================================
    msg += (
        f"├─ 結構："
        f"{semantic_structure(result)}\n"
    )

    # ================================
    # 🔥 位置
    # 只在未明確 breakout fail 顯示
    # ================================
    if result.get(
        "breakout_state"
    ) not in [
        "FAIL"
    ]:

        pos = semantic_position(dist)

        if pos:
            msg += f"├─ 位置：{pos}\n"

    # ================================
    # 🔥 交易
    # 不再分 heat/trade
    # ================================
    trade_text = semantic_trade(
        result
    )

    if trade_text != "✅ 可交易":

        msg += (
            f"├─ 交易："
            f"{trade_text}\n"
        )

    if (
        result.get("heat_state") == "EXTREME"
        and result.get("decision") != "FAIL"
    ):

        # 中文註釋：v18.5 只有非失敗的過熱股顯示禁追原因，避免 FAIL + EXTREME 雙主因衝突。
        msg += (
            f"├─ 原因："
            f"過熱 Lv.{result.get('extended_level')}\n"
        )

    # ================================
    # 🔥 條件
    # WAIT / NO_TRADE 顯示缺口，BUY 顯示已成立條件
    # ================================
    show_condition_line = (
        not holding_decision
        or holding_add_ready
    ) and (
        condition_items
        or result.get("decision_type") == "watch_quality_c"
    )

    if show_condition_line and result.get("heat_state") != "EXTREME":

        if (
            result.get("decision") == "BUY"
            and result.get("action", 0) > 0
            and (not holding_decision or holding_add_ready)
        ):
            if (
                result.get("heat_state") == "HOT"
                or result.get("entry_quality") not in ["A+", "A"]
            ):
                # 中文註釋：v18.8.3 觀察型買點改用「條件」，避免和強買點「成立」混在一起。
                label_title = "條件"
            else:
                label_title = "成立"
        elif result.get("decision_type") == "watch_quality_c":
            # 中文註釋：v18.9.3 C 品質觀察即使缺口清單為空，也要顯示策略觀察條件。
            label_title = "條件"
        else:
            label_title = "缺口"

        labels = semantic_condition_labels(
            result,
            condition_items
        )

        if labels:
            msg += (
                f"├─ {label_title}："
                f"{'、'.join(labels)}\n"
            )

    # ================================
    # 🔥 數據
    # 核心交易資訊
    # ================================
    rr_text = (
        "-"
        if should_hide_rr(result)
        or (holding_decision and not holding_add_ready)
        else safe_round(result.get("rr"))
    )

    # 中文註釋：v18.8 持倉非加碼時隱藏新進場 RR，避免用買點 RR 反向干擾續抱 / 停利判斷。
    msg += (
        f"├─ 數據："
        f"RR {rr_text}"
        f" ｜S {struct}/5"
        f" ｜V {vol}x（日線）\n"
    )

    quality = result.get("entry_quality")
    confidence = result.get("confidence_score")

    if quality and confidence and quality != "D" and (
        not holding_decision or holding_add_ready
    ):
        # 中文註釋：v18.8 品質分只用於新進場 / 持倉加碼，停利與續抱不混用入場品質。
        msg += (
            f"├─ 品質："
            f"{quality} ｜信心 {confidence}\n"
        )

    # ================================
    # 🔥 評級
    # ================================
    msg += (
        f"├─ 評級："
        f"★ {safe_round(result.get('strength'))}"
        f" ｜{semantic_reason(result)}\n"
    )

    # ================================
    # 🔥 extreme level
    # ================================
    if result.get(
        "extended_level",
        0
    ) >= 2 and result.get("heat_state") != "EXTREME":

        msg += (
            f"├─ 過熱："
            f"Lv.{result.get('extended_level')}\n"
        )

    # ================================
    # 🔥 price
    # ================================
    price_label = price_label_for_source(
        price_source
    )

    msg += (
        f"└─ 💰 {price_label}："
        f"{safe_round(price)}"
        f"（{safe_round(change)}%）\n\n"
    )

    return msg


# ================================
# 🔥 generate
# ================================
def generate():

    now = datetime.now(tz)

    msg = (

        f"【{now.strftime('%m/%d')} "
        f"{get_market_phase()}｜{VERSION}】\n"
    )

    msg += "====================\n\n"

    results_map = {}
    decisions = []

    # ================================
    # 🔥 scan
    # ================================
    for name, code in stocks.items():

        try:

            twse = get_twse(code)

            if not twse:
                continue

            (
                t_price,
                t_change,
                ma5,
                ma20,
                closes,
                volumes
            ) = twse

            realtime = get_realtime_price(code)
            yahoo = get_yahoo(code)

            price, change, price_source = (

                get_live_price_data(
                    realtime,
                    yahoo,
                    t_price,
                    t_change
                )
            )

            if not closes or not volumes:
                continue

            result = strategy(
                price,
                change,
                ma5,
                ma20,
                closes,
                volumes
            )

            # 中文註釋：v18.1 顯示層也用盤中即時價覆蓋最後一根 K，與 analysis.py 判斷保持一致。
            display_closes = (
                closes[:-1] + [price]
                if closes else closes
            )

            decisions.append(
                result.get("decision")
            )

            results_map[name] = {

                "result": result,

                "price": price,
                "change": change,
                "price_source": price_source,
                "stock_code": code,

                "ma5": ma5,
                "ma20": ma20,

                "closes": display_closes,
                "volumes": volumes,

                "holding": holdings.get(name)
            }

        except Exception as e:

            msg += (
                f"⚠ {name} 錯誤："
                f"{str(e)}\n"
            )

    if not results_map:
        return msg + "\n⚠ 無有效數據"

    # ================================
    # 🔥 render
    # ================================
    for name, data in results_map.items():

        try:

            msg += render_stock(
                name,
                data
            )

        except Exception as e:

            msg += (
                f"⚠ {name} 顯示錯誤："
                f"{str(e)}\n\n"
            )

    # ================================
    # 🔥 strongest
    # ================================
    best, score = pick_best_stock({

        k: v["result"]

        for k, v in results_map.items()
        if not v.get("holding")
    })

    msg += "====================\n"

    if best:

        best_result = results_map[best]["result"]

        rank_score = safe_round(
            score
        )

        strength_score = safe_round(
            best_result.get("strength")
        )

        # 中文註釋：v18.4 最強股只從有效 BUY 候選挑選，並同時顯示排序分與評級分。
        msg += (
            f"🔥 最強："
            f"{best}"
            f"（排序★{rank_score}"
            f"｜評級★{strength_score}）\n"
        )

    else:

        msg += "🔥 最強：無有效進場標的\n"

    holding_actions = []

    for name, data in results_map.items():

        if not data.get("holding"):
            continue

        h_decision = holding_status(
            data["result"],
            data["price"],
            data["holding"]["avg_price"],
            data["holding"]["shares"],
            data.get("price_source", "twse"),
            data.get("change")
        )

        if h_decision["level"] in [
            "STOP_100",
            "REDUCE_50",
            "REDUCE_25",
            "TAKE_PROFIT_50",
            "TAKE_PROFIT_25",
            "ADD_30",
            "ADD_20",
            "ADD_10",
            "WATCH",
            "SHAKEOUT"
        ]:
            holding_actions.append(
                f"{name}{h_decision['action']}"
            )

    if holding_actions:
        # 中文註釋：v18.4 底部提示需要處理的持倉與明確加減碼等級。
        msg += (
            f"📌 持倉處理："
            f"{'、'.join(holding_actions[:3])}\n"
        )

    # ================================
    # 🔥 market summary
    # ================================
    # 中文註釋：底部局部機會只統計未持倉新進場，避免持倉 BUY 訊號誤導成新買點。
    buy_count = sum(
        1 for data in results_map.values()
        if not data.get("holding")
        and data["result"].get("decision") == "BUY"
        and data["result"].get("action", 0) > 0
        and data["result"].get("entry_quality") in ["A+", "A", "B"]
        and data["result"].get("heat_state") not in ["HOT", "EXTREME"]
    )

    fail_count = sum(
        1 for d in decisions
        if d == "FAIL"
    )

    extreme_count = sum(
        1 for data in results_map.values()
        if data["result"].get("heat_state") == "EXTREME"
    )

    no_trade_count = sum(
        1 for d in decisions
        if d == "NO_TRADE"
    )

    weak_count = sum(
        1 for data in results_map.values()
        if data["result"].get("market_grade") == "D"
    )

    market_summary = "⏳ 觀望"

    if no_trade_count >= 6 or weak_count >= 6:

        # 中文註釋：v18.5 全局弱勢優先於局部失敗數，避免底部總結只看兩檔 FAIL 而誤判盤面。
        market_summary = "⏳ 弱勢觀望"

    elif extreme_count >= 3:

        market_summary = "🚨 過熱分歧"

    elif fail_count >= 2:

        market_summary = "🔴 突破失敗增多"

    elif buy_count >= 3:

        market_summary = "🟢 市場偏強"

    elif buy_count > 0:

        market_summary = "🟡 局部機會"

    msg += market_summary

    try:
        # 中文註釋：v19.0 只在收盤/盤後把每日穩定訊號寫入 Supabase，盤中不入庫。
        record_daily_signals(
            VERSION,
            get_market_phase(),
            msg,
            results_map,
            best,
            market_summary
        )
    except Exception as e:
        msg += f"\n⚠ DB記錄失敗：{str(e)}"

    return msg
