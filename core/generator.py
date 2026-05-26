# ================================
# FINAL UI（v19.1.3｜Daily Signal Database）
# ================================

from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import pytz

from services.stock_api import (
    get_twse,
    get_yahoo_history,
    get_yahoo,
    get_realtime_price,
    get_last_error,
    get_last_ohlcv
)

from services.analysis import (
    strategy,
    pick_best_stock,
    BREAKOUT_THRESHOLD,
    holding_signal as strategy_holding_signal,
    MIN_DATA_POINTS
)

from core.condition_engine import (
    condition_engine,
    summarize_conditions
)
from services.position_store import (
    get_position_store_warning,
    load_positions,
    load_today_position_events
)
from core.watchlist import STOCKS

from services.signal_store import record_daily_signals
from services.daily_snapshot_store import (
    get_supabase_client,
    record_daily_snapshots
)

tz = pytz.timezone("Asia/Taipei")

VERSION = "v19.3.2"

EXECUTION_LEVELS = {
    "TAKE_PROFIT_50": "TP50",
    "TAKE_PROFIT_25": "TP25",
    "REDUCE_50": "R50",
    "REDUCE_25": "R25",
    "STOP_100": "STP",
    "ADD_30": "A30",
    "ADD_20": "A20",
    "ADD_10": "A10"
}

# ================================
# 🔒 股票池
# ================================
stocks = STOCKS


# ================================
# 🔒 持倉
# ================================
holdings = {}
position_events = {}


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


def price_text(val, n=2):

    try:

        if val is None:
            return "-"

        return f"{float(val):.{n}f}"

    except:
        return "-"


def signed_pct(val):

    try:
        return f"{float(val):+.2f}%"

    except:
        return "-"


def price_change_line(price, change):

    return f"價格：{safe_round(price)}（{signed_pct(change)}）"


def calc_shares(shares, ratio):

    try:
        if ratio <= 0:
            # 中文註釋：v19.1.3 續抱 / 警戒不應顯示 1 股，0 比例直接回傳 0。
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

    if h > 13:
        return "盤後"

    # 中文註釋：v19.1.3 非交易時段不標成盤後，避免早盤手動執行被誤解為收盤訊號。
    return "非交易"


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
            # 中文註釋：v19.1.3 接近漲跌停時 Yahoo 常有延遲或昨收價，優先採用 TWSE 即時成交 / 盘口價。
            return r_price, r_change, "realtime"

        if (
            y_price
            and y_change is not None
            and abs(y_change) < 0.3
            and abs(r_change) >= 3
        ):
            # 中文註釋：v19.1.3 Yahoo 幾乎不動但 TWSE 即時價明顯變動時，視為 Yahoo 舊價。
            return r_price, r_change, "realtime"

        if y_price and abs(r_price - y_price) / y_price <= 0.02:
            # 中文註釋：v19.1.3 即時價與 Yahoo 差距 2% 內才採用，降低異常報價誤判。
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
        # 中文註釋：v19.1.3 假日不顯示 realtime/yahoo/twse 來源，避免被誤解為即時成交。
        return "最近價格"

    if phase == "盤中":

        if source == "twse":
            return "盤中參考(twse)"

        if source == "yahoo":
            return "盤中參考(yahoo)"

        return f"盤中即時({source})"

    # 中文註釋：v19.1.3 twse 不是盤中即時價，避免報文誤導。
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
        # 中文註釋：v19.1.3 持倉已判定洗盤時，型態主語優先顯示洗盤，避免和弱勢文字衝突。
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
        # 中文註釋：v19.1.3 型態主語改讀策略層 structure_phase，避免顯示層自行推論漲停 / 洗盤。
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
        # 中文註釋：v19.1.3 持倉洗盤的低量是保護條件，不再顯示成一般無量交易缺口。
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
        # 中文註釋：v19.1.3 突破失敗優先於禁追 / 無量，避免同一檔同時顯示兩種互斥交易狀態。
        return "❌ 不交易"

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


def entry_blockers(result):

    labels = []
    behavior = result.get("price_behavior")
    phase = result.get("structure_phase")
    trade = result.get("trade_state")
    heat = result.get("heat_state")
    rr = result.get("rr", 0)
    dist = result.get("breakout_distance")

    if result.get("decision") == "FAIL" or phase == "FAILED_BREAKOUT":
        labels.append("突破失敗")

    if behavior == "LIMIT_LOCK":
        labels.append("漲停不追")
    elif behavior == "LIMIT_REBOUND":
        labels.append("漲停反彈待確認")
    elif behavior == "WEAK_REBOUND":
        labels.append("弱反彈待確認")

    if heat == "EXTREME":
        labels.append(f"過熱 Lv.{result.get('extended_level', 3)}")
    elif trade == "EXTENDED" or heat == "HOT":
        labels.append("過熱觀察")

    if rr is not None and rr < 1 and result.get("decision") != "FAIL":
        labels.append("RR不足")

    if trade == "NO_VOLUME" or result.get("volume_state") == "WEAK":
        labels.append("量能不足")

    if result.get("market_grade") == "D":
        labels.append("市場弱")

    if dist is not None and dist > 4:
        labels.append("遠離觸發")

    return list(dict.fromkeys(labels))


def entry_advantages(result):

    labels = []
    phase = result.get("structure_phase")
    rr = result.get("rr", 0)
    vp = result.get("volume_price_state")

    if phase in ["BREAKOUT_CONFIRM", "BREAKOUT"]:
        labels.append("突破確認")
    elif phase == "BREAKOUT_WATCH":
        labels.append("接近突破")

    if result.get("market_grade") in ["A+", "A"]:
        labels.append("市場強")

    if result.get("structure_state") == "STRONG":
        labels.append("結構強")

    if vp == "EXPANSION":
        labels.append("攻擊量")

    if rr is not None and rr >= 1 and not should_hide_rr(result):
        labels.append("RR足夠")

    return labels[:4]


def compact_market_line(result, dist):
    state = semantic_state(result)
    market = MARKET_MAP.get(result.get('market_grade'), '🟡 偏強')
    structure = semantic_structure(result)
    pos = None

    if result.get("breakout_state") not in ["FAIL"]:
        pos = semantic_position(dist)

    parts = [
        state,
        market,
        structure
    ]

    if pos:
        parts.append(pos)

    return "｜".join(parts)


def compact_entry_judgement(result):
    blockers = entry_blockers(result)
    advantages = entry_advantages(result)
    conclusion = entry_conclusion(result)

    parts = []
    if blockers:
        parts.append(f"阻斷：{'、'.join(blockers[:3])}")

    if advantages:
        parts.append(f"優勢：{'、'.join(advantages[:3])}")

    if conclusion:
        parts.append(conclusion)

    return "｜".join(parts)


def event_summary_text(events):
    if not events or not events.get("event_count"):
        return ""

    parts = []

    if events.get("bought_shares", 0) > 0:
        parts.append(f"買 {events['bought_shares']}股")

    if events.get("sold_shares", 0) > 0:
        sold = f"賣 {events['sold_shares']}股"
        if events.get("sell_pct", 0) > 0:
            sold += f"（{events['sell_pct']}%）"
        parts.append(sold)

    if not parts and events.get("labels"):
        parts.append("、".join(events["labels"][:2]))

    if not parts:
        return ""

    return "｜".join(parts)


def entry_header(result):

    decision = result.get("decision")
    blockers = entry_blockers(result)

    if (
        decision == "BUY"
        and result.get("action", 0) > 0
        and not blockers
        and result.get("entry_quality") in ["A+", "A", "B"]
    ):
        return f"{get_action(result)} 可買"

    if blockers:
        return f"⛔ 不買｜{blockers[0]}"

    if decision == "FAIL":
        return "❌ 不買｜失敗"

    return f"⏳ {final_label(result)}"


def entry_conclusion(result):

    blockers = entry_blockers(result)

    if not blockers and result.get("decision") == "BUY" and result.get("action", 0) > 0:
        return "可新進場"

    if "突破失敗" in blockers:
        return "失敗訊號，不交易"

    if "漲停不追" in blockers:
        return "漲停鎖價，不追高"

    if "過熱觀察" in blockers or any(item.startswith("過熱") for item in blockers):
        return "過熱風險優先，等待冷卻"

    if "弱反彈待確認" in blockers or "漲停反彈待確認" in blockers:
        return "反彈先觀察，等隔日確認"

    if "市場弱" in blockers:
        return "市場弱，不新增"

    if "量能不足" in blockers:
        return "量能不足，等量"

    if "遠離觸發" in blockers:
        return "位置太遠，等接近觸發"

    if "RR不足" in blockers and result.get("market_grade") in ["A+", "A"]:
        return "強勢但風報不夠，不追"

    if "RR不足" in blockers:
        return "RR不足，不進場"

    return "觀察，不急進場"


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
        # 中文註釋：v19.1.3 失敗股評級原因固定為突破失敗，不再被過熱或遠離觸發覆蓋。
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

        # 中文註釋：v19.1.3 NO_TRADE 不再用高 RR 當評級原因，避免弱勢股被誤解成機會。
        return "不交易"

    if should_hide_rr(result):

        # 中文註釋：v19.1.3 RR 被隱藏時，評級原因同步回到市場 / 趨勢 / 量能主因，避免文字仍提示高 RR。
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
            # 中文註釋：v19.1.3 觀察型買點明確標出 RR 足夠但量能/過熱未確認。
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

        # 中文註釋：v19.1.3 WATCH_C 改用觀察條件，不再顯示事件 / Edge / RR 不足假缺口。
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

    # 中文註釋：v19.1.3 缺口改成交易語意，避免直接露出 event / Edge 造成報文像假錯誤。
    for item in condition_items:

        if item == "market":
            if result.get("market_grade") == "D":
                label = "市場弱"
            else:
                # 中文註釋：v19.1.3 中性盤不是弱勢盤，缺口文字改成未轉強避免顯示衝突。
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

    # 中文註釋：v19.1.3 弱勢 / 遠離 / 無量時 RR 只作內部判斷，不在報文顯示成可交易誘因。
    return False


def hidden_rr_reason(result, holding=False):

    if holding:
        return "持倉不看新倉RR"

    dist = result.get("breakout_distance")

    if result.get("heat_state") in ["HOT", "EXTREME"] or result.get("trade_state") in ["EXTENDED", "AVOID"]:
        return "過熱"

    if result.get("market_grade") == "D" or result.get("structure_phase") in ["WEAK", "WEAK_REBOUND"]:
        return "弱勢"

    if result.get("volume_state") == "WEAK" or result.get("trade_state") == "NO_VOLUME":
        return "量能不足"

    if dist is not None and dist > 4:
        return "遠離觸發"

    if result.get("price_behavior") in ["LIMIT_LOCK", "LIMIT_REBOUND"]:
        return "過熱"

    return "不可用"


def rr_display_text(result, holding=False):

    if should_hide_rr(result):
        return f"-（{hidden_rr_reason(result, holding)}）"

    return safe_round(result.get("rr"))


def should_show_entry_suffix(
    result,
    holding_decision
):

    if result.get("decision") == "FAIL":
        # 中文註釋：v19.1.3 失敗標題已經表達主狀態，不再追加 BREAKOUT_FAIL 後綴造成重複。
        return False

    if result.get("entry_profile") in [
        "WAIT_LIMIT_REBOUND",
        "WAIT_WEAK_REBOUND",
        "WAIT_DISTANCE",
        "WAIT_LIMIT_LOCK"
    ]:
        # 中文註釋：v19.1.3 觀察 / 不交易型態不掛 Day1，避免弱反彈被誤看成有效突破日。
        return False

    if result.get("structure_phase") in [
        "WEAK_REBOUND",
        "LIMIT_REBOUND"
    ]:
        # 中文註釋：v19.1.3 弱勢反彈和漲停反彈需要隔日確認，不顯示突破日後綴。
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

    # 中文註釋：v19.1.3 持倉股以持倉動作為主，非加碼情境不顯示收復 / 站穩等短線後綴。
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
            # 中文註釋：v19.1.3 C/D 品質只顯示觀察，不顯示倉位比例避免被當成買進指令。
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
        # 中文註釋：v19.1.3 C 品質是策略層觀察，不顯示成「等確認」以免像缺少資料。
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
    change=None,
    realized_profit_taken_ratio=0,
    realized_profit_taken_date=None,
    signal_date=None
):

    signal = strategy_holding_signal(
        result,
        price,
        avg_price,
        price_source,
        change,
        realized_profit_taken_ratio,
        realized_profit_taken_date,
        signal_date
    )

    ratio = signal.get("ratio", 0)
    action_shares = (
        shares
        if ratio >= 1
        else calc_shares(shares, ratio)
    )

    # 中文註釋：v19.1.3 持倉策略由 analysis.py 輸出，generator.py 只換算股數與維持既有報文格式。
    return {
        "action": signal.get("action", "續抱"),
        "shares": action_shares,
        "note": signal.get("reason", "不加碼"),
        "level": signal.get("level", "HOLD"),
        "warning_price": signal.get("warning_price"),
        "hard_stop_price": signal.get("hard_stop_price"),
        "phase": signal.get("phase"),
        "allow_add": signal.get("allow_add", False),
        "add_status": signal.get("add_status", "BLOCK"),
        "add_blockers": signal.get("add_blockers", []),
        "risk_level": signal.get("risk_level", 1)
    }

def holding_risk_text(
    decision
):

    warning = price_text(
        decision.get("warning_price")
    )

    hard_stop = price_text(
        decision.get("hard_stop_price")
    )

    return f"警戒 {warning}｜停損 {hard_stop}"


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

    # 中文註釋：v19.1.3 持倉輸出補上倉位結果，讓加碼 / 減碼 / 洗盤觀察後的股數更清楚。
    return f"維持 {current_shares}股 ｜不加碼"


def holding_add_text(decision):

    level = decision.get("level")

    if level in [
        "ADD_30",
        "ADD_20",
        "ADD_10"
    ]:
        return f"成立 ｜{decision.get('action')}"

    if decision.get("add_status") == "FORBID":
        return "禁止"

    return "未成立"


def holding_control_text(decision, current_shares):

    return holding_position_text(decision, current_shares).replace(" ｜", "｜")


def holding_blocker_text(decision):

    level = decision.get("level")

    if level == "ADD_30":
        return "強勢突破、RR足夠、品質達標"

    if level == "ADD_20":
        return "趨勢延續、RR足夠、品質達標"

    if level == "ADD_10":
        return "小幅轉強、RR達標、信心達標"

    if level in ["TAKE_PROFIT_25", "TAKE_PROFIT_50"]:
        return "浮盈達標、過熱急漲、分批鎖利"

    if level == "STOP_100":
        return "停損優先、避免虧損擴大"

    if level in ["REDUCE_25", "REDUCE_50"]:
        return "結構轉弱、先降風險"

    if level == "WATCH":
        return "輕虧或盤勢弱、暫不加碼"

    if level == "SHAKEOUT":
        return "縮量回測、未見出貨、等量價確認"

    if level == "HOLD_CORE":
        return "保留核心倉、暫不加碼、等待冷卻"

    if level == "HOLD":
        note = decision.get("note") or ""

        if "RR不足" in note:
            return "RR不足、續抱不加碼"

        if "突破成立" in note:
            return "浮盈不足、等量價確認"

        return "買點未成立、暫不加碼"

    blockers = decision.get("add_blockers") or []

    if not blockers:
        if decision.get("add_status") == "ALLOW":
            return "條件成立"
        return "持倉管理優先"

    return "、".join(blockers[:4])


def execution_reply_markup(results_map):
    return {
        "inline_keyboard": [
            [{"text": "輸入買入：3231 300 149.5", "callback_data": "noop"}],
            [{"text": "輸入賣出：3231 500", "callback_data": "noop"}],
            [{"text": "輸入清倉：清倉 3231", "callback_data": "noop"}],
            [{"text": "輸入設定：設定 3231 440 140.92", "callback_data": "noop"}],
        ]
    }


def snapshot_bucket_from_result(result):

    blockers = entry_blockers(result)
    phase = result.get("structure_phase")

    if result.get("is_best_candidate"):
        return "最強候選"

    if result.get("decision") == "BUY" and result.get("action", 0) > 0 and not blockers:
        return "有效買點"

    if "RR不足" in blockers:
        return "RR不足"

    if "漲停不追" in blockers:
        return "漲停不追"

    if "過熱觀察" in blockers or any(item.startswith("過熱") for item in blockers):
        return "過熱阻斷"

    if phase == "WEAK_REBOUND":
        return "弱反彈"

    if phase == "LIMIT_REBOUND":
        return "漲停反彈"

    if "市場弱" in blockers:
        return "市場弱"

    if result.get("decision") == "FAIL":
        return "突破失敗"

    return result.get("decision", "其他")


def snapshot_bucket_from_row(row):

    reasons = row.get("reasons") or []
    pattern = row.get("pattern")

    if row.get("is_best_candidate"):
        return "最強候選"

    if row.get("action") == "BUY" and row.get("is_tradeable"):
        return "有效買點"

    if "RR不足" in reasons or (row.get("rr") is not None and row.get("rr") < 1):
        return "RR不足"

    if pattern == "LOCK_LIMIT" or "不追高" in reasons:
        return "漲停不追"

    if (row.get("heat_level") or 0) >= 2:
        return "過熱阻斷"

    if pattern == "WEAK_REBOUND":
        return "弱反彈"

    if pattern == "LIMIT_REBOUND":
        return "漲停反彈"

    if row.get("market_state") == "D":
        return "市場弱"

    if row.get("action") == "FAIL":
        return "突破失敗"

    return row.get("action", "其他")


PATTERN_LABELS = {
    "BREAKOUT_CONFIRM": "突破確認",
    "BREAKOUT_WATCH": "接近突破",
    "LOCK_LIMIT": "漲停鎖價",
    "LIMIT_REBOUND": "漲停反彈",
    "WEAK_REBOUND": "弱勢反彈",
    "WEAK": "弱勢",
    "BASE": "整理",
    "SHAKEOUT": "洗盤回測",
    "FAILED_BREAKOUT": "突破失敗",
    "DISTRIBUTION": "出貨",
    "HEALTHY_PULLBACK": "健康回測"
}

POSITION_LABELS = {
    "BREAKOUT": "已突破",
    "NEAR_BREAKOUT": "臨界",
    "WATCH_BREAKOUT": "接近",
    "FAR": "遠離",
    "UNKNOWN": "位置不明"
}


def volume_bucket_label(value):

    try:
        ratio = float(value)
    except:
        return "量能不明"

    if ratio >= 2:
        return "爆量"

    if ratio >= 1.3:
        return "放量"

    if ratio >= 0.8:
        return "正常量"

    return "低量"


def position_bucket_from_distance(distance):

    if distance is None:
        return "UNKNOWN"

    if distance < 0:
        return "BREAKOUT"

    if distance < 1:
        return "NEAR_BREAKOUT"

    if distance < 4:
        return "WATCH_BREAKOUT"

    return "FAR"


def setup_bucket_label(pattern, volume_bucket, position_bucket):

    pattern_text = PATTERN_LABELS.get(pattern, pattern or "型態不明")
    position_text = POSITION_LABELS.get(position_bucket, position_bucket or "位置不明")

    return f"{pattern_text}/{volume_bucket}/{position_text}"


def setup_bucket_from_row(row):

    pattern = row.get("pattern")
    volume_bucket = volume_bucket_label(row.get("volume_ratio"))
    position_bucket = row.get("position_state") or "UNKNOWN"

    return (
        pattern,
        volume_bucket,
        position_bucket
    )


def setup_bucket_from_result(result, data):

    pattern = result.get("structure_phase")
    volume_bucket = volume_bucket_label(
        data.get("volume_ratio")
        or volume_ratio(data.get("volumes") or [])
    )
    distance = result.get("breakout_distance")

    if distance is None:
        distance = breakout_distance(
            data.get("price"),
            data.get("closes") or []
        )

    position_bucket = position_bucket_from_distance(
        distance
    )

    return (
        pattern,
        volume_bucket,
        position_bucket
    )


def parse_trade_date(value):

    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except:
        return None


def build_price_lookup(price_rows):

    by_stock = {}

    for row in price_rows:
        stock_id = row.get("stock_id")
        trade_date = parse_trade_date(row.get("trade_date"))
        close = row.get("close")

        if not stock_id or trade_date is None or close is None:
            continue

        by_stock.setdefault(stock_id, []).append((trade_date, float(close)))

    for stock_id in by_stock:
        by_stock[stock_id].sort(key=lambda item: item[0])

    return by_stock


def forward_return(price_lookup, stock_id, trade_date, horizon=3):

    prices = price_lookup.get(stock_id) or []

    for idx, (date_value, close) in enumerate(prices):
        if date_value != trade_date:
            continue

        target_idx = idx + horizon

        if target_idx >= len(prices) or not close:
            return None

        target_close = prices[target_idx][1]
        return (target_close - close) / close * 100

    return None


def market_forward_return(price_lookup, trade_date, horizon=3):

    returns = []

    for stock_id in price_lookup:
        result = forward_return(price_lookup, stock_id, trade_date, horizon)

        if result is not None:
            returns.append(result)

    if not returns:
        return None

    return sum(returns) / len(returns)


def summarize_validation(returns, mode):

    if len(returns) < 6:
        return None

    wins = sum(1 for value in returns if value > 0)
    win_rate = wins / len(returns) * 100
    avg_return = sum(returns) / len(returns)

    if mode == "blocked":
        if avg_return <= 0.3 and win_rate < 55:
            verdict = "歷史沒有明顯優勢"
            action = "維持不買"
        elif avg_return >= 1.5 or win_rate >= 65:
            verdict = "歷史偏強，但今日阻斷仍有效"
            action = "列觀察，不追價"
        else:
            verdict = "樣本中性"
            action = "依今日阻斷"
    else:
        if avg_return >= 1 and win_rate >= 55:
            verdict = "買點有效"
            action = "可依策略執行"
        elif avg_return <= 0 or win_rate < 45:
            verdict = "買點偏弱"
            action = "降低信心"
        else:
            verdict = "樣本中性"
            action = "依今日條件"

    if mode == "holding":
        if avg_return >= 0.5 and win_rate >= 55:
            verdict = "持倉同型相對偏強"
            action = "續抱；未達加碼不追"
        elif avg_return <= -0.5 or win_rate < 45:
            verdict = "加碼樣本偏弱"
            action = "依風控續抱，不加碼"
        else:
            verdict = "樣本中性"
            action = "依持倉規則"

    if mode == "risk":
        if avg_return <= 0.3 and win_rate < 55:
            verdict = "支持風控"
            action = "維持風控"
        else:
            verdict = "樣本未否定風控"
            action = "風控優先，不改判"

    return {
        "mode": mode,
        "sample": len(returns),
        "win_rate": round(win_rate),
        "avg_return": round(avg_return, 1),
        "verdict": verdict,
        "action": action
    }


def backtest_context(version, scope, summary, setup_label=None):

    if not summary:
        return None

    label = scope

    if setup_label:
        label = f"{scope} {setup_label}"

    return {
        "version": version,
        "scope": scope,
        "setup": setup_label,
        "label": label,
        "sample": summary["sample"],
        "win_rate": summary["win_rate"],
        "avg_return": summary["avg_return"],
        "metric": "3日相對股票池",
        "verdict": summary["verdict"],
        "action": summary["action"]
    }


def render_backtest_context(context):

    if not context:
        return ""

    if isinstance(context, str):
        return f"├─ 驗證：{context}\n"

    setup = context.get("setup")
    scope = context.get("scope") or context.get("label")
    if scope == "持倉同型":
        case_scope = "持倉"
    else:
        case_scope = "未持倉"

    if setup:
        condition = f"{case_scope}｜{setup}"
    else:
        condition = case_scope

    avg_return = context.get("avg_return", 0)
    relative_text = (
        f"{avg_return:+.1f}%"
        if avg_return is not None
        else "-"
    )

    verdict = context.get("verdict")
    action = context.get("action")
    sample = context.get("sample") or 0
    win_rate = context.get("win_rate")

    if sample < 10:
        reading = "樣本少，僅參考"
    elif verdict == "歷史偏強，但今日阻斷仍有效" and win_rate is not None and win_rate < 50:
        reading = "報酬偏正但勝率不足"
    elif verdict == "歷史偏強，但今日阻斷仍有效":
        reading = "偏強但阻斷有效"
    elif verdict == "歷史沒有明顯優勢":
        reading = "無優勢，維持不買"
    elif verdict == "樣本中性":
        reading = "中性，依今日條件"
    elif verdict == "加碼樣本偏弱":
        reading = "加碼偏弱，不加碼"
    elif verdict == "持倉同型相對偏強":
        reading = "持倉偏強，續抱"
    elif verdict and action:
        reading = f"{verdict}，{action}"
    else:
        reading = verdict or action or ""

    return (
        f"├─ 回測："
        f"{condition}"
        f"｜樣本 {sample}\n"
        f"├─ 統計："
        f"3日勝率 {win_rate}%"
        f"｜相對 {relative_text}"
        f"｜{reading}\n"
    )


def load_backtest_context(results_map):

    try:
        client = get_supabase_client()
        since = (datetime.now(tz).date() - timedelta(days=90)).isoformat()
        rows = []
        history_version = VERSION

        min_history_rows = max(len(stocks) * 6, 60)

        for candidate_version in [VERSION, "v19.1", "v19.0"]:
            candidate_rows = (
                client.table("daily_signal_snapshot")
                .select("stock_id,trade_date,version,pattern,market_state,structure_state,position_state,volume_ratio,rr,heat_level,action,reasons,is_tradeable,is_best_candidate")
                .eq("version", candidate_version)
                .gte("trade_date", since)
                .execute()
                .data
                or []
            )

            if len(candidate_rows) >= min_history_rows:
                rows = candidate_rows
                history_version = candidate_version
                break

            if not rows and candidate_rows:
                rows = candidate_rows
                history_version = candidate_version

        price_rows = (
            client.table("daily_price")
            .select("stock_id,trade_date,close")
            .gte("trade_date", since)
            .execute()
            .data
            or []
        )
    except:
        return {}

    price_lookup = build_price_lookup(price_rows)
    bucket_returns = {}
    setup_returns = {}
    stock_buy_returns = {}
    today = datetime.now(tz).date()

    for row in rows:
        bucket = snapshot_bucket_from_row(row)
        stock_id = row.get("stock_id")
        trade_date = parse_trade_date(row.get("trade_date"))

        if trade_date is None or trade_date >= today:
            continue

        result = forward_return(price_lookup, stock_id, trade_date, 3)

        if result is None:
            continue

        market_result = market_forward_return(price_lookup, trade_date, 3)

        if market_result is None:
            continue

        relative_result = result - market_result

        bucket_returns.setdefault(bucket, []).append(relative_result)
        setup_returns.setdefault(setup_bucket_from_row(row), []).append(relative_result)

        if row.get("action") == "BUY" and row.get("is_tradeable"):
            stock_buy_returns.setdefault(stock_id, []).append(relative_result)

    context = {}
    for name, data in results_map.items():
        result = data.get("result", {})
        stock_id = data.get("stock_code")

        if data.get("holding"):
            holding_decision = data.get("holding_decision") or result.get("_holding_decision") or {}

            if holding_decision.get("level") not in ["ADD_10", "ADD_20", "ADD_30"]:
                setup_bucket = setup_bucket_from_result(result, data)
                mode = (
                    "risk"
                    if holding_decision.get("level") in [
                        "STOP_100",
                        "REDUCE_25",
                        "REDUCE_50",
                        "TAKE_PROFIT_25",
                        "TAKE_PROFIT_50",
                        "HOLD_CORE"
                    ]
                    else "holding"
                )
                summary = summarize_validation(setup_returns.get(setup_bucket, []), mode)

                if summary:
                    context[name] = backtest_context(
                        history_version,
                        "持倉同型",
                        summary,
                        setup_bucket_label(*setup_bucket)
                    )

                continue

            summary = summarize_validation(stock_buy_returns.get(stock_id, []), "buy")

            if summary:
                context[name] = backtest_context(
                    history_version,
                    "本股加碼",
                    summary
                )

            continue

        mode = (
            "buy"
            if result.get("decision") == "BUY"
            and result.get("action", 0) > 0
            and not entry_blockers(result)
            else "blocked"
        )

        setup_bucket = setup_bucket_from_result(result, data)
        summary = summarize_validation(setup_returns.get(setup_bucket, []), mode)

        if summary:
            context[name] = backtest_context(
                history_version,
                "同型",
                summary,
                setup_bucket_label(*setup_bucket)
            )

    return context


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
    today_events = data.get("position_events") or {}

    # 中文註釋：v19.1.3 顯示層只讀 condition_engine 映射結果，不自行判斷交易條件。
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
            if holding.get("avg_price")
            else 0
        )

        holding_decision = holding_status(
            result,
            price,
            holding["avg_price"],
            holding["shares"],
            price_source,
            change,
            holding.get("realized_profit_taken_ratio", 0),
            holding.get("realized_profit_taken_date"),
            datetime.now(tz).date().isoformat()
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
        # 中文註釋：v19.1.3 持倉非加碼完全隱藏買點條件，避免「RR -」卻顯示 RR 足夠或洗盤又顯示量能不足。
        condition_items = []

    # header
    stock_code = data.get("stock_code") or stocks.get(name) or ""
    title_name = f"{name} {stock_code}".strip()

    if holding:

        header = (
            f"【{title_name}】 "
            f"📌 持倉 ｜{holding_decision['action']}"
        )

    else:

        header = (

            f"【{title_name}】 "
            f"{entry_header(result)}"
        )

    if (
        entry
        and result.get("decision") != "NO_TRADE"
        and (holding or not entry_blockers(result))
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

        # 中文註釋：v19.1.3 只對已持有股票增加持倉管理資訊，其餘原始技術資料全部保留。
        msg += (
            f"├─ 持倉："
            f"{holding['shares']}股"
            f"｜均價 {price_text(holding['avg_price'])}"
            f"｜損益 {signed_pct(pnl)}\n"
        )

        today_text = event_summary_text(today_events)
        if today_text:
            msg += (
                f"├─ 今日："
                f"{today_text}\n"
            )

        action_text = holding_decision["action"]
        if holding_decision["shares"] > 0:
            action_text += f" {holding_decision['shares']}股"

        msg += (
            f"├─ 決策："
            f"{action_text}"
            f"｜{holding_decision['note']}\n"
        )

        msg += (
            f"├─ 倉控："
            f"{holding_control_text(holding_decision, holding['shares'])}\n"
        )

        msg += (
            f"├─ 風控："
            f"{holding_risk_text(holding_decision)}\n"
        )

        blocker_label = "依據" if holding_add_ready else "阻斷"

        msg += (
            f"├─ {blocker_label}："
            f"{holding_blocker_text(holding_decision)}\n"
        )

    msg += (
        f"├─ 盤面："
        f"{compact_market_line(result, dist)}\n"
    )

    if not holding:
        today_text = event_summary_text(today_events)
        if today_text:
            msg += (
                f"├─ 今日："
                f"{today_text}｜目前0股\n"
            )

        judgement = compact_entry_judgement(result)
        if judgement:
            msg += (
                f"├─ 判斷："
                f"{judgement}\n"
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

    if not holding and entry_blockers(result):
        show_condition_line = False

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
                # 中文註釋：v19.1.3 觀察型買點改用「條件」，避免和強買點「成立」混在一起。
                label_title = "條件"
            else:
                label_title = "成立"
        elif result.get("decision_type") == "watch_quality_c":
            # 中文註釋：v19.1.3 C 品質觀察即使缺口清單為空，也要顯示策略觀察條件。
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
        "-（持倉不看新倉RR）"
        if holding_decision and not holding_add_ready
        else rr_display_text(result, holding=bool(holding_decision))
    )

    # 中文註釋：v19.1.3 持倉非加碼時隱藏新進場 RR，避免用買點 RR 反向干擾續抱 / 停利判斷。
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
        # 中文註釋：v19.1.3 品質分只用於新進場 / 持倉加碼，停利與續抱不混用入場品質。
        msg += (
            f"├─ 品質："
            f"{quality} ｜信心 {confidence}\n"
        )

    if data.get("backtest_context"):
        msg += render_backtest_context(
            data.get("backtest_context")
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


def plain_label(text):

    if text is None:
        return "-"

    value = str(text)

    for token in [
        "📌", "⛔", "🔥", "🚨", "🎯", "💰", "🚀", "↗",
        "⚠", "🟢", "🟡", "🟠", "🔴", "⏳", "🔹", "📈", "🧽", "👀", "❌"
    ]:
        value = value.replace(token, "")

    return "｜".join(part.strip() for part in value.split("｜"))


def stock_title(name, data):

    code = data.get("stock_code") or stocks.get(name) or ""
    return f"{name} {code}".strip()


def stock_pnl(data):

    holding = data.get("holding") or {}
    avg_price = holding.get("avg_price")

    if not avg_price:
        return 0

    return (
        (data.get("price", 0) - avg_price)
        / avg_price
        * 100
    )


def today_event_weight(data):

    events = data.get("position_events") or {}
    return 0 if events.get("event_count") else 1


def risk_weight(data):

    result = data.get("result") or {}
    risky = (
        result.get("heat_state") in ["HOT", "EXTREME"]
        or result.get("price_behavior") == "LIMIT_LOCK"
        or result.get("extended_level", 0) >= 2
    )
    return 0 if risky else 1


def ordered_result_items(results_map):

    return sorted(
        results_map.items(),
        key=lambda item: (
            0 if item[1].get("holding") else 1,
            today_event_weight(item[1]),
            risk_weight(item[1]),
            stocks.get(item[0], "")
        )
    )


def ensure_holding_decision(name, data, signal_date=None):

    if data.get("holding_decision"):
        return data["holding_decision"]

    holding = data.get("holding")

    if not holding:
        return None

    decision = holding_status(
        data["result"],
        data["price"],
        holding["avg_price"],
        holding["shares"],
        data.get("price_source", "twse"),
        data.get("change"),
        holding.get("realized_profit_taken_ratio", 0),
        holding.get("realized_profit_taken_date"),
        signal_date or datetime.now(tz).date().isoformat()
    )

    data["holding_decision"] = decision
    return decision


def best_stock_text(results_map, best, score=None):

    if not best:
        return "無有效進場標的"

    result = results_map[best]["result"]
    return (
        f"{best}"
        f"｜排序★{safe_round(score)}"
        f"｜評級★{safe_round(result.get('strength'))}"
    )


def compact_risk_text(results_map):
    market_mode, _risk_level = derive_market_state(
        [
            (name, data)
            for name, data in results_map.items()
            if not data.get("holding")
        ]
    )

    if market_mode == "進攻偏熱":
        return "漲停/過熱股多，新倉禁止追高"

    if market_mode == "轉弱":
        return "市場轉弱，新倉保守"

    limit_or_hot = [
        name for name, data in results_map.items()
        if risk_weight(data) == 0
    ]

    if len(limit_or_hot) >= 3:
        return "漲停/過熱股多，不追高"

    if limit_or_hot:
        return "局部過熱，等冷卻"

    weak_count = sum(
        1 for data in results_map.values()
        if data["result"].get("market_grade") == "D"
    )

    if weak_count >= 4:
        return "弱勢標的偏多，控新倉"

    return "無明顯集中風險"


def focus_text(results_map, market_summary):

    if any(data.get("holding") for data in results_map.values()):
        if "過熱" in market_summary:
            return "先處理持倉，暫不新增"
        return "持倉優先，新增從嚴"

    if "局部機會" in market_summary:
        return "只看有效買點，不追高"

    return "暫不新增，等訊號確認"


def holding_summary_line(index, name, data):

    decision = ensure_holding_decision(name, data)
    note = position_summary_note(name, data)

    return (
        f"{index}. {name}"
        f"｜{signed_pct(stock_pnl(data))}"
        f"｜{position_summary_action(name, data)}"
        f"｜{note}"
    )


def derive_market_state(watchlist):

    total = len(watchlist)

    if total <= 0:
        return "中性觀察", "R2"

    hot_count = 0
    weak_count = 0

    for _name, data in watchlist:
        blockers = entry_blockers(data["result"])
        label = blockers[0] if blockers else final_label(data["result"])

        if label in ["漲停不追", "漲停反彈待確認", "過熱觀察", "RR不足"] or any(
            item.startswith("過熱") for item in blockers
        ):
            hot_count += 1

        if label in ["市場弱", "弱勢", "遠離觸發"]:
            weak_count += 1

    if hot_count / total >= 0.5:
        return "進攻偏熱", "R3"

    if weak_count / total >= 0.5:
        return "轉弱", "R4"

    return "中性觀察", "R2"


def classify_watchlist_group(name, data):

    result = data["result"]
    blockers = entry_blockers(result)

    if is_valid_entry(result):
        return "可觀察但不可買"

    label = blockers[0] if blockers else final_label(result)
    behavior = result.get("price_behavior")
    heat = result.get("heat_state")
    trade = result.get("trade_state")
    phase = result.get("structure_phase")
    market_grade = result.get("market_grade")

    if (
        label in ["市場弱", "弱勢", "弱反彈待確認", "遠離觸發"]
        or market_grade == "D"
        or phase in ["WEAK", "WEAK_REBOUND"]
    ):
        return "弱勢淘汰"

    if (
        label in ["漲停不追", "漲停反彈待確認"]
        or behavior == "LIMIT_LOCK"
        or heat == "EXTREME"
        or trade == "AVOID"
    ):
        return "禁止追高"

    if (
        heat == "HOT"
        or trade == "EXTENDED"
        or label == "過熱觀察"
        or "過熱觀察" in blockers
    ):
        return "等待冷卻"

    if (
        label == "RR不足"
        or trade == "LATE_ENTRY"
        or "RR不足" in blockers
        or (
            "量能不足" in blockers
            and market_grade != "D"
        )
    ):
        return "可觀察但不可買"

    return "可觀察但不可買"


def format_watchlist_summary_grouped(watchlist):

    groups = {
        "禁止追高": [],
        "等待冷卻": [],
        "可觀察但不可買": [],
        "弱勢淘汰": []
    }

    for _index, (name, data) in sort_watchlist_grouped(watchlist):
        groups[classify_watchlist_group(name, data)].append(name)

    lines = []

    for label in ["禁止追高", "等待冷卻", "可觀察但不可買", "弱勢淘汰"]:
        names = groups[label]
        if names:
            lines.append(f"【{label} {len(names)}】{'、'.join(names)}")

    return lines or ["無"]


def watchlist_item_sort_key(index, name, data):

    result = data["result"]
    group = classify_watchlist_group(name, data)
    group_rank = {
        "禁止追高": 0,
        "等待冷卻": 1,
        "可觀察但不可買": 2,
        "弱勢淘汰": 3,
    }
    stock_order = list(STOCKS).index(name) if name in STOCKS else index

    if group == "禁止追高":
        subgroup = 0 if result.get("price_behavior") in ["LIMIT_LOCK", "LIMIT_REBOUND"] else 1
    else:
        subgroup = 0

    return (
        group_rank.get(group, 9),
        subgroup,
        stock_order,
        index,
    )


def sort_watchlist_grouped(watchlist):

    return sorted(
        enumerate(watchlist),
        key=lambda item: watchlist_item_sort_key(item[0], item[1][0], item[1][1])
    )


def unheld_summary_line(name, data):

    result = data["result"]
    blocker = entry_blockers(result)
    if is_valid_entry(result):
        return f"{name}｜可買｜{entry_size_text(result)}"

    label = blocker[0] if blocker else final_label(result)
    return f"{name}｜{label}"


def sort_position_summary(positions):

    return sorted(
        positions,
        key=lambda item: position_summary_rank(item[0], item[1])
    )


def position_summary_rank(name, data):

    decision = ensure_holding_decision(name, data)
    today_text = event_summary_text(data.get("position_events") or {})
    pnl = stock_pnl(data)
    action = decision.get("action", "") if decision else ""
    level = decision.get("level", "") if decision else ""

    if "核心" in action or level == "HOLD_CORE":
        bucket = 0
    elif "賣" in today_text:
        bucket = 1
    elif level in ["SHAKEOUT", "HOLD_WATCH", "SHAKEOUT_WARN", "RISK_WATCH"]:
        bucket = 2
    elif "買" in today_text and pnl >= 0:
        bucket = 2
    elif pnl < 0 or data["result"].get("market_grade") == "D":
        bucket = 4
    else:
        bucket = 3

    return (bucket, -pnl)


def position_summary_action(name, data):

    decision = ensure_holding_decision(name, data)
    today_text = event_summary_text(data.get("position_events") or {})
    action = decision.get("action", "") if decision else ""
    level = decision.get("level", "") if decision else ""
    pnl = stock_pnl(data)

    if level in ["TAKE_PROFIT_25", "TAKE_PROFIT_50"]:
        return "停利"

    if level in ["REDUCE_25", "REDUCE_50", "STOP_100"]:
        return "減碼"

    if level == "RISK_WATCH":
        return "風控觀察"

    if "核心" in action or level == "HOLD_CORE":
        return "核心續抱"

    if "賣" in today_text:
        return "底倉續抱"

    if level == "SHAKEOUT_WARN":
        return "洗盤警戒"

    if level == "SHAKEOUT":
        return "洗盤續抱"

    if level == "HOLD_WATCH":
        return "續抱觀察"

    if pnl < 0 or data["result"].get("market_grade") == "D":
        return "續抱觀察"

    return "續抱"


def position_summary_note(name, data):

    decision = ensure_holding_decision(name, data)
    today_text = event_summary_text(data.get("position_events") or {})
    note = decision.get("note") if decision else ""

    if "賣" in today_text:
        return "已減碼，觀察是否轉弱"

    action = position_summary_action(name, data)

    if action == "核心續抱":
        return decision.get("note") or "高浮盈回落，暫不加碼"

    if action == "洗盤續抱":
        return "縮量回測，未見出貨"

    if action == "洗盤警戒":
        return "小虧，暫不加碼"

    if action == "風控觀察":
        return decision.get("note") or "跌破警戒價優先風控"

    if action == "續抱觀察":
        return decision.get("note") or "轉弱觀察，不加碼"

    if risk_weight(data) == 0 and decision:
        return "過熱，不加碼"

    if "突破成立" in note:
        return "突破成立，等量價確認"

    return note or semantic_reason(data["result"])


def is_valid_entry(result):
    return (
        result.get("decision") == "BUY"
        and result.get("action", 0) > 0
        and not entry_blockers(result)
        and result.get("entry_quality") in ["A+", "A", "B"]
        and result.get("heat_state") not in ["HOT", "EXTREME"]
    )


def entry_size_text(result):
    action = result.get("action", 0)

    try:
        if action and action > 0:
            return f"{round(action * 100)}%倉"
    except:
        pass

    return "觀察"


def entry_wait_text(result):

    blockers = entry_blockers(result)

    if not blockers:
        if is_valid_entry(result):
            return "現在可分批"
        return "等條件確認"

    first = blockers[0]

    if first == "RR不足":
        return "等RR達標"

    if first in ["過熱觀察"] or first.startswith("過熱"):
        return "等冷卻"

    if first == "漲停不追":
        return "等開板回測"

    if first in ["弱反彈待確認", "漲停反彈待確認"]:
        return "等隔日確認"

    if first == "量能不足":
        return "等量能補上"

    if first == "市場弱":
        return "等市場轉強"

    if first == "遠離觸發":
        return "等回接近買點"

    return f"等{first}解除"


def daily_write_warning_text(signal_result=None, snapshot_result=None):

    missing = []

    for result in [snapshot_result or {}, signal_result or {}]:
        for stock_id in result.get("missing_stock_ids") or []:
            if stock_id not in missing:
                missing.append(stock_id)

    if missing:
        return f"每日快照未寫入：缺少 {', '.join(missing)}"

    if (snapshot_result or {}).get("reason") == "validation_failed":
        return "Snapshot驗證失敗，未寫入每日快照"

    return None


def source_summary_text(results_map):

    price_sources = {
        data.get("price_source") or "-"
        for data in results_map.values()
    }
    daily_sources = {
        data.get("daily_source") or "-"
        for data in results_map.values()
    }

    price_source = next(iter(price_sources)) if len(price_sources) == 1 else "mixed"
    daily_source = next(iter(daily_sources)) if len(daily_sources) == 1 else "mixed"

    return f"📡 資料：即時價 {price_source}｜日線 {daily_source}"


def formatTelegramSummary(results_map, best, score, market_summary, now, position_warning=None, daily_write_warning=None):

    holding_items = [
        (name, data)
        for name, data in ordered_result_items(results_map)
        if data.get("holding")
    ]
    holding_items = sort_position_summary(holding_items)
    watch_items = [
        (name, data)
        for name, data in ordered_result_items(results_map)
        if not data.get("holding")
    ]
    market_mode, risk_level = derive_market_state(watch_items)

    lines = [
        f"【{now.strftime('%m/%d')} {get_market_phase()}｜{VERSION}】",
    ]

    if position_warning:
        lines.append(f"⚠ {position_warning}，持倉狀態不可信")

    if daily_write_warning:
        lines.append(f"⚠ {daily_write_warning}")

    holding_names = "、".join(name for name, _data in holding_items) or "無"
    lines.extend([
        f"📊 市場：{market_mode}｜{risk_level}",
    ])

    if get_market_phase() == "盤中":
        lines.append(source_summary_text(results_map))

    lines.extend([
        f"📌 持倉：{holding_names}",
        f"🔥 最強：{best_stock_text(results_map, best, score)}",
        f"🚨 風險：{compact_risk_text(results_map)}",
        f"🎯 今日重點：{focus_text(results_map, market_summary)}",
        "",
        "持倉摘要："
    ])

    if holding_items:
        for index, (name, data) in enumerate(holding_items, start=1):
            lines.append(holding_summary_line(index, name, data))
    else:
        lines.append("無")

    lines.extend(["", "未持倉標的："])
    lines.extend(format_watchlist_summary_grouped(watch_items))

    return "\n".join(lines)


def formatTelegramPositionCard(name, data):

    holding = data["holding"]
    decision = ensure_holding_decision(name, data)
    result = data["result"]
    today_text = event_summary_text(data.get("position_events") or {}) or "無"
    dist = data.get("breakout_distance", result.get("breakout_distance"))
    decision_line, condition_line = holding_detail_decision_lines(name, data)
    rr_text = (
        "-（持倉不看新倉RR）"
        if decision and not decision.get("allow_add")
        else rr_display_text(result, holding=True)
    )

    lines = [
        f"【{stock_title(name, data)}】📌 {position_summary_action(name, data)}｜{signed_pct(stock_pnl(data))}",
        f"倉位：{holding['shares']}股｜均價 {price_text(holding.get('avg_price'))}｜今日 {today_text}",
        f"風控：{holding_risk_text(decision)}",
        f"盤面：{plain_label(compact_market_line(result, dist))}",
        f"決策：{decision_line}",
        f"條件：{condition_line}",
        f"數據：RR {rr_text}｜S {data.get('structure_score', '-')}/5｜V {data.get('volume_ratio', '-')}x",
        compact_backtest_line(data.get("backtest_context")),
        price_change_line(data.get("price"), data.get("change")),
    ]

    return "\n".join(lines)


def holding_detail_decision_lines(name, data):

    decision = ensure_holding_decision(name, data)
    today_text = event_summary_text(data.get("position_events") or {})
    summary_action = position_summary_action(name, data)

    if summary_action == "核心續抱":
        return "核心續抱，暫不加碼", "跌破警戒價優先風控，等待冷卻"

    if summary_action == "洗盤續抱":
        return "洗盤續抱，暫不加碼", "跌破警戒價優先風控"

    if summary_action == "洗盤警戒":
        return "洗盤警戒，暫不加碼", "若跌破停損或轉弱，優先風控"

    if summary_action == "風控觀察":
        return "風控觀察，暫不加碼", "跌破警戒價優先風控"

    if summary_action == "底倉續抱":
        return "保留底倉，暫不加碼", "觀察減碼後是否轉弱，跌破警戒價優先風控"

    if summary_action == "續抱觀察":
        return "續抱觀察，暫不加碼", "若無法重新接近買點，降低優先級"

    if "買" in today_text:
        return "續抱，暫不加碼", "浮盈不足，等量價確認後再評估加碼"

    text = holding_blocker_text(decision)
    parts = [
        item.strip()
        for item in text.replace("、", "，").split("，")
        if item.strip()
    ]

    condition_keywords = ["等待", "等量", "冷卻", "確認", "RR", "信心", "品質"]
    condition_parts = [
        item for item in parts
        if any(keyword in item for keyword in condition_keywords)
    ]
    decision_parts = [
        item for item in parts
        if item not in condition_parts
    ]

    if not decision_parts:
        decision_parts = parts[:2]

    if not condition_parts:
        condition_parts = ["後續再評估"]

    return "，".join(decision_parts[:2]), "，".join(condition_parts[:2])


def compact_backtest_line(context):

    if not context:
        return "回測：-"

    if isinstance(context, str):
        return f"回測：{context}"

    avg_return = context.get("avg_return")
    relative = f"{avg_return:+.1f}%" if avg_return is not None else "-"

    return (
        f"回測：樣本{context.get('sample')}"
        f"｜3日勝率{context.get('win_rate')}%"
        f"｜相對{relative}"
    )


def formatTelegramUnheldCard(name, data):

    result = data["result"]
    dist = data.get("breakout_distance", result.get("breakout_distance"))
    blockers = entry_blockers(result)
    valid_entry = is_valid_entry(result)
    title_label = "買點成立" if valid_entry else (blockers[0] if blockers else final_label(result))
    group = classify_watchlist_group(name, data)

    if valid_entry:
        title_icon = "🟢"
        title_action = f"可買｜{entry_size_text(result)}"
    elif group == "等待冷卻":
        title_icon = "⏳"
        title_action = "等待冷卻"
    elif group == "可觀察但不可買":
        title_icon = "👀"
        title_action = "觀察"
    elif group == "弱勢淘汰":
        title_icon = "⛔"
        title_action = "淘汰"
    else:
        title_icon = "⛔"
        title_action = "不買"

    rr_text = rr_display_text(result, holding=False)
    risk_label = unheld_buy_risk_label(result, title_label)
    buy_line = (
        f"買點：可買｜建議 {entry_size_text(result)}｜{entry_wait_text(result)}"
        if valid_entry
        else f"買點：不買｜{risk_label}｜{entry_wait_text(result)}｜{entry_conclusion(result)}"
    )

    return "\n".join([
        f"【{stock_title(name, data)}】{title_icon} {title_action}｜{title_label}",
        f"盤面：{plain_label(compact_market_line(result, dist))}",
        buy_line,
        f"數據：RR {rr_text}｜S {data.get('structure_score', '-')}/5｜V {data.get('volume_ratio', '-')}x",
        compact_backtest_line(data.get("backtest_context")),
        price_change_line(data.get("price"), data.get("change")),
    ])


def unheld_buy_risk_label(result, title_label):

    blockers = entry_blockers(result)

    if title_label == "RR不足" and result.get("heat_state") not in ["HOT", "EXTREME"]:
        return "RR不足"

    if (
        title_label in ["漲停不追", "漲停反彈待確認", "過熱觀察"]
        or any(item.startswith("過熱") for item in blockers)
    ):
        return "追價風險"

    return title_label


def split_message(text, limit=3400):

    if len(text) <= limit:
        return [text]

    chunks = []
    current = ""

    for block in text.split("\n\n"):
        candidate = f"{current}\n\n{block}".strip() if current else block

        if len(candidate) <= limit:
            current = candidate
            continue

        if current:
            chunks.append(current)

        if len(block) <= limit:
            current = block
        else:
            for index in range(0, len(block), limit):
                chunks.append(block[index:index + limit])
            current = ""

    if current:
        chunks.append(current)

    return chunks


def formatTelegramMessages(results_map, full_msg, best, score, market_summary, now, position_warning=None, include_detail=False, daily_write_warning=None):

    ordered_items = ordered_result_items(results_map)
    holding_items = sort_position_summary([
        (name, data)
        for name, data in ordered_items
        if data.get("holding")
    ])
    position_cards = [
        formatTelegramPositionCard(name, data)
        for name, data in holding_items
    ]
    unheld_cards = [
        formatTelegramUnheldCard(name, data)
        for _index, (name, data) in sort_watchlist_grouped([
            (name, data)
            for name, data in ordered_items
            if not data.get("holding")
        ])
    ]

    messages = [
        formatTelegramSummary(results_map, best, score, market_summary, now, position_warning, daily_write_warning),
        "【持倉標的】\n\n" + ("\n\n".join(position_cards) if position_cards else "無持倉"),
        "【未持倉標的】\n\n" + ("\n\n".join(unheld_cards) if unheld_cards else "無"),
    ]

    if include_detail:
        for chunk in split_message("【完整詳情備份】\n" + full_msg):
            messages.append(chunk)

    return messages


REPORT_DAILY_MIN_ROWS = MIN_DATA_POINTS


def load_report_daily_kline(code):

    # 中文註釋：線上報文只需要 MA20 / 10日量 / 20日支撐壓力，不走 replay/backfill 的長歷史抓取口徑。
    yahoo = get_yahoo_history(
        code,
        months=1,
        min_rows=REPORT_DAILY_MIN_ROWS
    )

    if yahoo:
        return yahoo, "yahoo", None

    yahoo_error = get_last_error(code) or "yahoo_daily: no data"

    twse = get_twse(
        code,
        months=1,
        min_rows=REPORT_DAILY_MIN_ROWS,
        max_months=2
    )

    if twse:
        return twse, "twse", None

    twse_error = get_last_error(code) or "twse: no data"

    yahoo_retry = get_yahoo_history(
        code,
        months=2,
        min_rows=REPORT_DAILY_MIN_ROWS
    )

    if yahoo_retry:
        return yahoo_retry, "yahoo", None

    retry_error = get_last_error(code) or "yahoo_daily: no data"
    return None, None, f"{yahoo_error}；fallback {twse_error}；retry {retry_error}"


def load_stock_signal(name, code):

    try:
        daily, daily_source, daily_error = load_report_daily_kline(code)

        if not daily:
            return name, None, None, f"{name}({code}) {daily_error}"

        (
            t_price,
            t_change,
            ma5,
            ma20,
            closes,
            volumes
        ) = daily

        realtime = get_realtime_price(code)
        yahoo = None if realtime else get_yahoo(code)

        price, change, price_source = (
            get_live_price_data(
                realtime,
                yahoo,
                t_price,
                t_change
            )
        )

        if price_source == "twse" and daily_source != "twse":
            price_source = daily_source

        if not closes or not volumes:
            return name, None, None, f"{name}({code}) {daily_source}: empty kline"

        result = strategy(
            price,
            change,
            ma5,
            ma20,
            closes,
            volumes
        )

        display_closes = (
            closes[:-1] + [price]
            if closes else closes
        )
        result["breakout_distance"] = breakout_distance(
            price,
            display_closes
        )

        return name, {
            "result": result,

            "price": price,
            "change": change,
            "price_source": price_source,
            "daily_source": daily_source,
            "stock_code": code,

            "ma5": ma5,
            "ma20": ma20,

            "closes": display_closes,
            "volumes": volumes,
            "ohlcv": get_last_ohlcv(code),

            "holding": (
                holdings.get(name)
                if (holdings.get(name) or {}).get("shares", 0) > 0
                else None
            ),
            "position_events": position_events.get(name, {})
        }, result.get("decision"), None

    except Exception as exc:
        return name, None, None, f"{name} 錯誤：{exc}"


# ================================
# 🔥 generate
# ================================
def generate_report():
    global holdings
    global position_events
    holdings = load_positions()
    position_events = load_today_position_events()

    now = datetime.now(tz)

    msg = (

        f"【{now.strftime('%m/%d')} "
        f"{get_market_phase()}｜{VERSION}】\n"
    )

    msg += "====================\n\n"

    results_map = {}
    decisions = []
    data_errors = []

    # ================================
    # 🔥 scan
    # ================================
    with ThreadPoolExecutor(max_workers=min(8, max(len(stocks), 1))) as executor:
        futures = {
            name: executor.submit(load_stock_signal, name, code)
            for name, code in stocks.items()
        }

        for name in stocks:
            loaded_name, data, decision, error = futures[name].result()

            if error:
                data_errors.append(error)
                continue

            if not data:
                data_errors.append(f"{loaded_name} 無有效數據")
                continue

            decisions.append(decision)
            results_map[loaded_name] = data

    if not results_map:
        if data_errors:
            msg += "⚠ 無有效數據：行情來源未返回可用日線\n"
            for item in data_errors[:6]:
                msg += f"├─ {item}\n"
            if len(data_errors) > 6:
                msg += f"└─ 其餘 {len(data_errors) - 6} 檔同樣無資料\n"
            else:
                msg = msg.rstrip("\n") + "\n"
            return msg, None

        return msg + "\n⚠ 無有效數據", None

    position_warning = get_position_store_warning()

    if position_warning:
        msg += f"⚠ {position_warning}，持倉狀態不可信\n\n"
    elif not any((item or {}).get("shares", 0) > 0 for item in holdings.values()):
        msg += "⚠ 持倉DB目前全為0股，報文依未持倉邏輯顯示\n\n"

    backtest_context = load_backtest_context(results_map)

    for name, text in backtest_context.items():
        if name in results_map:
            results_map[name]["backtest_context"] = text

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

        # 中文註釋：v19.1.3 最強股只從有效 BUY 候選挑選，並同時顯示排序分與評級分。
        msg += (
            f"🔥 最強："
            f"{best}"
            f"（排序★{rank_score}"
            f"｜評級★{strength_score}）\n"
        )

    else:

        msg += "🔥 最強：無有效進場標的\n"

    holding_actions = []
    hot_holding_count = 0

    for name, data in results_map.items():

        if not data.get("holding"):
            continue

        if data["result"].get("heat_state") in ["HOT", "EXTREME"]:
            hot_holding_count += 1

        h_decision = holding_status(
            data["result"],
            data["price"],
            data["holding"]["avg_price"],
            data["holding"]["shares"],
            data.get("price_source", "twse"),
            data.get("change"),
            data["holding"].get("realized_profit_taken_ratio", 0),
            data["holding"].get("realized_profit_taken_date"),
            now.date().isoformat()
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
        # 中文註釋：v19.1.3 底部提示需要處理的持倉與明確加減碼等級。
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

        # 中文註釋：v19.1.3 全局弱勢優先於局部失敗數，避免底部總結只看兩檔 FAIL 而誤判盤面。
        market_summary = "⏳ 弱勢觀望"

    elif extreme_count >= 3:

        if hot_holding_count:
            market_summary = "🚨 過熱控倉，先處理持倉"
        else:
            market_summary = "🚨 過熱不追，等冷卻"

    elif fail_count >= 2:

        market_summary = "🔴 突破失敗增多"

    elif buy_count >= 3:

        market_summary = "🟢 市場偏強"

    elif buy_count > 0:

        market_summary = "🟡 局部機會"

    msg += market_summary

    try:
        # 中文註釋：v19.1.3 只在收盤/盤後把每日穩定訊號寫入 Supabase，盤中不入庫。
        signal_result = record_daily_signals(
            VERSION,
            get_market_phase(),
            msg,
            results_map,
            best,
            market_summary
        )
        # 中文註釋：v19.1.3 同步寫入 daily_price / daily_signal_snapshot，供 backfill 與每日樣本共用同一套口徑。
        snapshot_result = record_daily_snapshots(
            VERSION,
            get_market_phase(),
            results_map
        )

        daily_write_warning = daily_write_warning_text(signal_result, snapshot_result)

        if daily_write_warning:
            msg += f"\n⚠ {daily_write_warning}"
    except Exception as e:
        daily_write_warning = None
        msg += f"\n⚠ DB記錄失敗：{str(e)}"

    messages = formatTelegramMessages(
        results_map,
        msg,
        best,
        score,
        market_summary,
        now,
        position_warning,
        daily_write_warning=daily_write_warning
    )

    return messages, execution_reply_markup(results_map)


def generate():
    result = generate_report()[0]
    if isinstance(result, list):
        return "\n\n====================\n\n".join(result)
    return result
