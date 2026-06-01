# ================================
# FINAL UI（v19.1.3｜Daily Signal Database）
# ================================

from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout
import io
import re
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
from core.market_theme_evidence import (
    build_market_theme_evidence,
    build_market_theme_evidence_provider,
    format_market_theme_summary_lines
)

from services.signal_store import record_daily_signals
from services.daily_snapshot_store import (
    get_supabase_client,
    record_daily_snapshots
)
from services.strategy_evidence import (
    format_strategy_evidence_summary,
    load_strategy_evidence_summary,
    record_strategy_evidence
)
from services.cross_day_context import build_cross_day_contexts
from services.market_theme_evidence_store import load_confirmed_market_theme_evidence

tz = pytz.timezone("Asia/Taipei")

VERSION = "v20.4.14"

PERSISTENT_CROSS_DAY_SOURCES = {
    "positions",
    "position_events",
    "daily_signal_snapshot",
    "signal_runs",
    "signal_items",
    "signal_outcomes",
}

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


def card_breakout_distance(data):
    result = data.get("result") or {}
    dist = data.get("breakout_distance")

    if dist is None or dist == "":
        dist = result.get("breakout_distance")

    if dist == "":
        return None

    return dist


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

    try:
        rr = float(result.get("rr"))
    except:
        return safe_round(result.get("rr"))

    if round(rr, 2) == 0:
        return "0.00（不足）"

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
    signal_date=None,
    position_events=None,
    observation_days=0
):

    signal = strategy_holding_signal(
        result,
        price,
        avg_price,
        price_source,
        change,
        realized_profit_taken_ratio,
        realized_profit_taken_date,
        signal_date,
        position_events,
        shares,
        observation_days
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
        return (
            "├─ 策略樣本 / 分類回測：不可用\n"
            f"├─ 原因：classification backtest 樣本不足（有效樣本 {sample}）\n"
            "├─ 解讀：本次不把策略樣本納入判斷；個股決策只看既有買點與風控。\n"
        )
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
        f"├─ 策略樣本 / 分類回測："
        f"{condition}"
        f"\n"
        f"├─ 樣本："
        f"{sample} 筆；觀察口徑：{context.get('version') or VERSION} classification backtest\n"
        f"├─ 解讀："
        f"3日勝率 {win_rate}%"
        f"｜相對 {relative_text}"
        f"｜{reading}；只作歷史分類參考\n"
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
            datetime.now(tz).date().isoformat(),
            today_events,
            holding.get("observation_days", data.get("observation_days", 0))
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
        signal_date or datetime.now(tz).date().isoformat(),
        data.get("position_events") or {},
        holding.get("observation_days", data.get("observation_days", 0))
    )

    data["holding_decision"] = decision
    return decision


def best_stock_text(results_map, best, score=None, report_context=None):

    if not best:
        return "無有效進場標的"

    if not _unheld_decision_source_eligible(report_context, best):
        eligible_results = {
            name: data["result"]
            for name, data in results_map.items()
            if not data.get("holding")
            and is_valid_entry(data.get("result") or {})
            and _unheld_decision_source_eligible(report_context, name)
        }
        best, score = pick_best_stock(eligible_results)
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


def r3_no_new_reason(watch_items):

    if any(is_valid_entry(data.get("result") or {}) for _name, data in watch_items):
        return None

    groups = {
        "禁止追高": 0,
        "等待冷卻": 0,
        "可觀察但不可買": 0,
        "弱勢淘汰": 0,
    }
    rr_count = 0

    for name, data in watch_items:
        group = classify_watchlist_group(name, data)
        groups[group] = groups.get(group, 0) + 1
        if "RR不足" in entry_blockers(data.get("result") or {}):
            rr_count += 1

    if groups.get("禁止追高", 0) and groups.get("等待冷卻", 0) and rr_count:
        return "強勢股多已過熱，RR不足，禁止追高"

    if groups.get("禁止追高", 0) + groups.get("等待冷卻", 0) >= max(2, len(watch_items) // 2):
        return "漲停/過熱偏多，新倉只等冷卻"

    if rr_count >= max(2, len(watch_items) // 2):
        return "RR不足偏多，強勢股不追價"

    if groups.get("弱勢淘汰", 0) >= max(2, len(watch_items) // 2):
        return "弱勢淘汰偏多，暫不擴倉"

    return "強勢股多已過熱，RR不足，禁止追高"


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
        return "可買"

    label = blockers[0] if blockers else final_label(result)
    behavior = result.get("price_behavior")
    heat = result.get("heat_state")
    trade = result.get("trade_state")
    phase = result.get("structure_phase")
    market_grade = result.get("market_grade")

    if (
        label in ["市場弱", "弱勢", "弱反彈待確認", "突破失敗"]
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


def tomorrow_watch_state(name, data):

    result = data["result"]
    blockers = entry_blockers(result)

    if is_valid_entry(result):
        return "可買"

    label = blockers[0] if blockers else final_label(result)
    behavior = result.get("price_behavior")
    heat = result.get("heat_state")
    trade = result.get("trade_state")
    phase = result.get("structure_phase")
    market_grade = result.get("market_grade")

    if (
        label in ["市場弱", "弱勢", "弱反彈待確認", "突破失敗"]
        or market_grade == "D"
        or phase in ["WEAK", "WEAK_REBOUND"]
    ):
        return "弱勢淘汰"

    if label == "遠離觸發":
        return "等回測"

    if behavior in ["LIMIT_LOCK", "LIMIT_REBOUND"] or label in ["漲停不追", "漲停反彈待確認"]:
        return "等回測" if behavior == "LIMIT_LOCK" or label == "漲停不追" else "隔日確認"

    if heat in ["HOT", "EXTREME"] or trade in ["EXTENDED", "AVOID"] or label == "過熱觀察":
        return "等冷卻"

    if label == "RR不足" or trade == "LATE_ENTRY" or "RR不足" in blockers:
        return "等RR修復"

    if "量能不足" in blockers and market_grade != "D":
        return "等量能"

    return "隔日確認"


def tomorrow_trigger_text(state, data):

    result = data.get("result") or {}

    if state == "可買":
        return "依買點分批，不追高"

    if state == "等冷卻":
        return "過熱降溫且回測不破"

    if state == "等回測":
        return "回測不破且非漲停追價"

    if state == "等RR修復":
        return "RR修復至達標，不追高"

    if state == "等量能":
        return "量能回升且非追高"

    if state == "隔日確認":
        return "站回突破區且量能不失控"

    if state == "弱勢淘汰":
        return "重新轉強前不列優先"

    if result.get("breakout_distance") is not None:
        return "重新接近買點再評估"

    return None


def backtest_tracking_adjustment(context):

    if not context or isinstance(context, str):
        return 0

    sample = context.get("sample")
    avg_return = context.get("avg_return")

    if sample is None or sample < 10 or avg_return is None:
        return 0

    if avg_return >= 1.0:
        return -1 if sample >= 30 else -0.5

    if avg_return <= -0.5:
        return 1 if sample >= 30 else 0.5

    return 0


def cross_day_context(data):

    context = data.get("cross_day_context")
    return context if isinstance(context, dict) else {}


def cross_day_ready(data):

    context = cross_day_context(data)
    sources = context.get("source_of_truth") or []
    if isinstance(sources, str):
        sources = [sources]
    return (
        context.get("source_status") == "ready"
        and bool(sources)
        and all(source in PERSISTENT_CROSS_DAY_SOURCES for source in sources)
    )


def cross_day_sort_adjustment(data):

    context = cross_day_context(data)
    if not cross_day_ready(data):
        return 0

    weight = context.get("historical_evidence_weight") or 0
    repair = context.get("repair_status")
    guard = context.get("dedupe_guard")
    adjustment = 0

    if repair in ["repaired", "improving"]:
        adjustment -= 0.75
    elif repair in ["failed", "deteriorating"]:
        adjustment += 0.75

    if weight > 0:
        adjustment -= min(weight, 2) * 0.25
    elif weight < 0:
        adjustment += min(abs(weight), 2) * 0.25

    if guard in ["prior_take_profit_completed", "prior_reduce_completed", "same_day_executed", "new_position_guard"]:
        adjustment += 0.25

    return adjustment


def cross_day_repair_label(data):

    context = cross_day_context(data)
    if not cross_day_ready(data):
        return None

    days = context.get("consecutive_observe_days") or 0
    repair = context.get("repair_status")
    if repair in ["repaired", "improving"]:
        if days:
            return f"修復中｜連續觀察 {days} 天"
        return "修復中"
    if repair in ["failed", "deteriorating"]:
        if days:
            return f"連續失效｜連續觀察 {days} 天"
        return "連續失效"
    if days >= 2:
        return f"連續觀察 {days} 天"
    return None


def cross_day_detail_line(data):

    context = cross_day_context(data)
    if not cross_day_ready(data):
        return None

    parts = []
    previous_state = context.get("previous_state")
    if previous_state and previous_state != "unknown":
        parts.append(f"前次 {previous_state}")
    repair = cross_day_repair_label(data)
    if repair:
        parts.append(repair)
    weight = context.get("historical_evidence_weight")
    if weight not in [None, 0]:
        parts.append(f"權重 {weight:+}")
    reasons = context.get("weight_reason") or []
    if reasons:
        parts.append("、".join(str(item) for item in reasons[:2]))
    if not parts:
        return None
    return "歷史：" + "｜".join(parts[:4])


def cross_day_prepare_promotion(data):

    context = cross_day_context(data)
    if not cross_day_ready(data):
        return False

    result = data.get("result") or {}
    return (
        context.get("previous_state") == "eliminated"
        and context.get("repair_status") in ["repaired", "improving"]
        and (context.get("historical_evidence_weight") or 0) > 0
        and result.get("decision") != "BUY"
        and result.get("action", 0) <= 0
        and (
            result.get("market_grade") in ["A+", "A", "B"]
            or result.get("entry_quality") in ["A+", "A", "B"]
            or result.get("price_behavior") in ["LIMIT_LOCK", "VOLUME_BREAKOUT", "NORMAL"]
        )
    )


def cross_day_higher_priority_risk_action(decision):

    decision = decision or {}
    level = decision.get("level")
    action = str(decision.get("action") or "")
    note = str(decision.get("note") or "")
    risk_text = f"{action} {note}"

    if level in ["STOP_100", "REDUCE_50"]:
        return True

    return (
        action.startswith("硬風控")
        or action.startswith("硬停損")
        or action.startswith("停損")
        or "風控升級" in risk_text
        or "硬停損" in risk_text
    )


def cross_day_duplicate_action(data, decision=None):

    context = cross_day_context(data)
    if not cross_day_ready(data):
        return None

    decision = decision or data.get("holding_decision") or {}
    if cross_day_higher_priority_risk_action(decision):
        return None

    level = decision.get("level")
    guard = context.get("dedupe_guard")
    previous_action = context.get("previous_action")

    if level in ["TAKE_PROFIT_25", "TAKE_PROFIT_50"] and (
        guard in ["prior_take_profit_completed", "same_day_executed"]
        or previous_action == "take_profit"
    ):
        return "take_profit"

    if level in ["REDUCE_25", "REDUCE_50"] and (
        guard in ["prior_reduce_completed", "same_day_executed"]
        or previous_action == "reduce"
    ):
        return "reduce"

    if level in ["ADD_10", "ADD_20", "ADD_30"] and (
        guard in ["new_position_guard", "same_day_executed"]
        or previous_action == "buy"
    ):
        return "buy"

    return None


def tracking_sort_key(index, name, data):

    state = tomorrow_watch_state(name, data)
    state_rank = {
        "可買": 0,
        "等冷卻": 1,
        "等回測": 2,
        "等RR修復": 3,
        "等量能": 4,
        "隔日確認": 5,
        "弱勢淘汰": 9,
    }
    pnl_rank = 0
    result = data.get("result") or {}

    if result.get("market_grade") in ["A+", "A"]:
        pnl_rank -= 0.25

    return (
        state_rank.get(state, 8)
        + backtest_tracking_adjustment(data.get("backtest_context"))
        + cross_day_sort_adjustment(data)
        + pnl_rank,
        list(STOCKS).index(name) if name in STOCKS else index,
    )


def next_day_tracking_items(watch_items, limit=5):

    candidates = []

    for index, (name, data) in enumerate(watch_items):
        state = tomorrow_watch_state(name, data)
        trigger = tomorrow_trigger_text(state, data)

        if state in ["可買", "弱勢淘汰"] or not trigger:
            continue

        candidates.append((index, name, data, state, trigger))

    candidates.sort(key=lambda item: tracking_sort_key(item[0], item[1], item[2]))
    return candidates[:limit]


def format_next_day_tracking(watch_items):

    items = next_day_tracking_items(watch_items)

    if not items:
        return ["無"]

    lines = []
    for idx, (_index, name, data, state, trigger) in enumerate(items, start=1):
        lines.append(f"{idx}. {name}｜{state}｜明日觸發：{trigger}")

    return lines


def format_pending_candidates_grouped(watch_items):

    groups = {
        "可買": [],
        "等冷卻": [],
        "等回測": [],
        "等RR修復": [],
        "等量能": [],
        "隔日確認": [],
        "弱勢淘汰": [],
    }

    for index, (name, data) in enumerate(watch_items):
        state = tomorrow_watch_state(name, data)
        groups.setdefault(state, []).append((index, name, data))

    lines = []
    for label in ["可買", "等冷卻", "等回測", "等RR修復", "等量能", "隔日確認", "弱勢淘汰"]:
        values = sorted(
            groups.get(label, []),
            key=lambda item: tracking_sort_key(item[0], item[1], item[2])
        )
        if values:
            lines.append(f"【{label} {len(values)}】{'、'.join(name for _index, name, _data in values)}")

    return lines or ["無"]


def format_watchlist_summary_grouped(watchlist):

    groups = {
        "可買": [],
        "禁止追高": [],
        "等待冷卻": [],
        "可觀察但不可買": [],
        "弱勢淘汰": []
    }

    for _index, (name, data) in sort_watchlist_grouped(watchlist):
        groups[classify_watchlist_group(name, data)].append(name)

    lines = []

    for label in ["可買", "禁止追高", "等待冷卻", "可觀察但不可買", "弱勢淘汰"]:
        names = groups[label]
        if names:
            lines.append(f"【{label} {len(names)}】{'、'.join(names)}")

    return lines or ["無"]


def watchlist_item_sort_key(index, name, data):

    result = data["result"]
    group = classify_watchlist_group(name, data)
    group_rank = {
        "可買": 0,
        "禁止追高": 1,
        "等待冷卻": 2,
        "可觀察但不可買": 3,
        "弱勢淘汰": 4,
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

    if level == "STOP_100":
        bucket = 0
    elif level in ["REDUCE_50", "REDUCE_25", "TAKE_PROFIT_50", "TAKE_PROFIT_25"]:
        bucket = 1
    elif is_today_buy_holding(data):
        bucket = 2
    elif level in ["ADD_30", "ADD_20", "ADD_10"]:
        bucket = 3
    elif "核心" in action or level == "HOLD_CORE":
        bucket = 4
    elif "賣" in today_text:
        bucket = 5
    elif level in ["SHAKEOUT", "HOLD_WATCH", "SHAKEOUT_WARN", "RISK_WATCH"]:
        bucket = 6
    elif "買" in today_text and pnl >= 0:
        bucket = 6
    elif pnl < 0 or data["result"].get("market_grade") == "D":
        bucket = 8
    else:
        bucket = 7

    return (bucket, -pnl)


def numeric_execution_value(record, *keys):

    for key in keys:
        try:
            value = record.get(key)
            if value is not None:
                return int(value)
        except (TypeError, ValueError, AttributeError):
            pass

    return 0


def sold_shares_from_execution_record(record):

    if not isinstance(record, dict):
        return 0

    explicit_sold = numeric_execution_value(
        record,
        "sold_shares",
        "today_sold_qty",
        "executed_sell_shares",
        "sell_shares",
    )
    if explicit_sold > 0:
        return explicit_sold

    shares_delta = numeric_execution_value(record, "shares_delta", "delta_shares")
    if shares_delta < 0:
        return abs(shares_delta)

    action_text = " ".join(
        str(record.get(key) or "")
        for key in ["action", "action_label", "action_code", "event_type", "side"]
    ).upper()
    if any(token in action_text for token in ["賣", "停利", "REDUCE", "TAKE_PROFIT", "SELL", "STOP"]):
        return numeric_execution_value(record, "shares", "qty", "quantity", "executed_shares")

    return 0


def today_sold_shares_from_execution_data(data):

    for key in [
        "db_execution",
        "db_execution_record",
        "today_execution",
        "execution",
        "local_execution",
    ]:
        sold_shares = sold_shares_from_execution_record(data.get(key) or {})
        if sold_shares > 0:
            return sold_shares, key

    for key in [
        "db_executions",
        "today_executions",
        "executions",
        "local_executions",
    ]:
        total = sum(
            sold_shares_from_execution_record(record)
            for record in data.get(key) or []
        )
        if total > 0:
            return total, key

    events = data.get("position_events") or {}
    return sold_shares_from_execution_record(events), "position_events"


def second_take_profit_execution_state(data, decision=None):

    decision = decision or ensure_holding_decision("", data) or {}
    holding = data.get("holding") or {}

    sold_shares, source = today_sold_shares_from_execution_data(data)

    try:
        suggested_shares = int(decision.get("shares") or 0)
    except (TypeError, ValueError):
        suggested_shares = 0

    try:
        remaining_shares = int(holding.get("shares") or 0)
    except (TypeError, ValueError):
        remaining_shares = 0

    is_take_profit = (
        data.get("holding")
        and decision.get("level") in ["TAKE_PROFIT_25", "TAKE_PROFIT_50"]
        and suggested_shares > 0
    )
    try:
        realized_ratio = float(holding.get("realized_profit_taken_ratio") or 0)
    except (TypeError, ValueError):
        realized_ratio = 0
    is_second_stage = is_take_profit and realized_ratio > 0
    context = cross_day_context(data)
    execution_memory = context.get("execution_memory") or {}
    memory_labels = " ".join(str(item) for item in execution_memory.get("labels") or [])
    sell_deltas = execution_memory.get("sell_deltas") or []
    confirmed_second_stage_memory = (
        "第二" in memory_labels
        or "SECOND" in memory_labels.upper()
        or "TP2" in memory_labels.upper()
        or len(sell_deltas) >= 2
    )
    historical_take_profit_completed = (
        is_second_stage
        and context.get("source_status") == "ready"
        and (
            context.get("dedupe_guard") in ["prior_take_profit_completed", "same_day_executed"]
            or context.get("previous_action") == "take_profit"
        )
        and execution_memory.get("sold_shares", 0) > 0
        and confirmed_second_stage_memory
    )
    historical_take_profit_memory_insufficient = (
        is_second_stage
        and context.get("source_status") == "ready"
        and (
            context.get("dedupe_guard") in ["prior_take_profit_completed", "same_day_executed"]
            or context.get("previous_action") == "take_profit"
        )
        and (
            execution_memory.get("sold_shares", 0) <= 0
            or not confirmed_second_stage_memory
        )
    )
    execution_memory_blocked = (
        is_second_stage
        and (
            context.get("source_status") in ["source-error", "missing-source", "insufficient-data"]
            or historical_take_profit_memory_insufficient
        )
    )

    if historical_take_profit_completed:
        status = "completed"
        sold_shares = execution_memory.get("sold_shares", 0)
        source = "cross_day_position_events"
    elif execution_memory_blocked:
        status = "blocked"
    elif not is_take_profit or sold_shares <= 0:
        status = "none"
    elif sold_shares >= suggested_shares:
        status = "completed"
    else:
        status = "partial"

    return {
        "status": status,
        "sold_shares": sold_shares,
        "suggested_shares": suggested_shares,
        "remaining_suggestion": max(suggested_shares - sold_shares, 0),
        "remaining_shares": remaining_shares,
        "source": source,
        "is_second_stage": is_second_stage,
        "execution_memory": execution_memory,
        "realized_profit_taken_ratio": realized_ratio,
        "confirmed_second_stage_memory": confirmed_second_stage_memory,
    }


def is_same_day_second_take_profit(data, decision=None):

    return second_take_profit_execution_state(data, decision).get("status") in ["completed", "partial"]


def second_take_profit_context_text(data, decision=None):

    state = second_take_profit_execution_state(data, decision)

    if state["status"] == "completed":
        if state.get("source") == "cross_day_position_events":
            memory = state.get("execution_memory") or {}
            deltas = "、".join(str(value) for value in memory.get("sell_deltas") or [])
            return (
                f"production latest_trade_date={memory.get('latest_trade_date')}"
                f"｜已賣出 {deltas or state['sold_shares']}"
                f"｜realized_profit_taken_ratio={state.get('realized_profit_taken_ratio')}"
                f"｜剩餘 {state['remaining_shares']} 股"
                f"｜第二段已執行"
            )
        return (
            f"今日已賣 {state['sold_shares']} 股"
            f"｜剩餘 {state['remaining_shares']} 股"
            f"｜第二段已執行"
        )

    if state["status"] == "blocked":
        return "execution memory insufficient-data｜不輸出重複停利股數"

    if state["status"] == "partial":
        return (
            f"第二段停利剩餘建議 {state['remaining_suggestion']} 股"
            f"｜今日已賣 {state['sold_shares']} 股"
            f"｜原建議 {state['suggested_shares']} 股"
            f"｜剩餘持倉 {state['remaining_shares']} 股"
        )

    return (
        f"本次建議 {state['suggested_shares']} 股"
        f"｜剩餘 {state['remaining_shares']} 股"
    )


def holding_today_trade_text(data, decision=None):

    state = second_take_profit_execution_state(data, decision)
    if state["status"] in ["completed", "partial"] and state["sold_shares"] > 0:
        if state.get("source") == "cross_day_position_events":
            return f"最近交易日賣 {state['sold_shares']}股"
        return f"賣 {state['sold_shares']}股"

    return event_summary_text(data.get("position_events") or {})


def position_summary_action(name, data):

    decision = ensure_holding_decision(name, data)
    today_text = event_summary_text(data.get("position_events") or {})
    action = decision.get("action", "") if decision else ""
    level = decision.get("level", "") if decision else ""
    pnl = stock_pnl(data)

    if level == "STOP_100":
        return "停損"

    if str(action).startswith("硬風控"):
        return "硬風控減碼"

    if str(action).startswith("增量"):
        return "增量減碼"

    second_profit_state = second_take_profit_execution_state(data, decision)
    if second_profit_state.get("status") == "completed":
        return "第二段停利後觀察"

    if second_profit_state.get("status") == "partial":
        return "第二段停利剩餘建議"

    if second_profit_state.get("status") == "blocked":
        return "停利記憶不足"

    if second_profit_state.get("is_second_stage"):
        return "第二段停利"

    if is_today_buy_holding(data):
        return "新倉風控觀察"

    duplicate_action = cross_day_duplicate_action(data, decision)
    if duplicate_action == "take_profit":
        return "停利後觀察"
    if duplicate_action == "reduce":
        return "減碼後觀察"
    if duplicate_action == "buy":
        return "新倉風控觀察"

    if level in ["TAKE_PROFIT_25", "TAKE_PROFIT_50"]:
        return "停利"

    if level == "POST_PROFIT_WATCH":
        return "停利後觀察"

    if level in ["REDUCE_25", "REDUCE_50"]:
        return "減碼"

    if level == "POST_REDUCE_WATCH":
        return "減碼後觀察"

    if level == "NEW_POSITION_RISK_WATCH":
        return "新倉風控觀察"

    if level == "ADD_30":
        return "加碼30"

    if level == "ADD_20":
        return "加碼20"

    if level == "ADD_10":
        return "加碼10"

    if is_new_position_loss(data):
        if is_holding_shakeout_warning_display(data):
            return "洗盤警戒"
        return "新倉風控觀察"

    if level == "RISK_WATCH":
        return "風控觀察"

    if is_reduce_after_observation(data):
        return "減碼後觀察"

    if is_core_risk_watch_display(data):
        return "核心風控觀察"

    if "核心" in action or level == "HOLD_CORE":
        if (data.get("holding") or {}).get("realized_profit_taken_ratio", 0) > 0:
            return "停利後核心倉"
        return "核心續抱"

    if "賣" in today_text and not str(action).startswith("硬風控"):
        return "減碼後觀察"

    if level == "SHAKEOUT_WARN":
        return "洗盤警戒"

    if is_holding_shakeout_warning_display(data):
        return "洗盤警戒"

    if level == "SHAKEOUT":
        return "洗盤續抱"

    if level == "HOLD_WATCH":
        return "續抱觀察"

    if pnl < 0 or data["result"].get("market_grade") == "D":
        return "續抱觀察"

    return "續抱"


def is_today_buy_holding(data):

    if not data.get("holding"):
        return False

    events = data.get("position_events") or {}
    if events.get("bought_shares", 0) > 0:
        return True

    today_action = str(data.get("today_action") or "").upper()
    return today_action in ["BUY", "買", "買入", "今日買入"]


def is_reduce_after_observation(data):

    events = data.get("position_events") or {}
    decision = ensure_holding_decision("", data)
    level = decision.get("level") if decision else ""

    return (
        data.get("holding")
        and events.get("sold_shares", 0) > 0
        and level not in ["STOP_100", "REDUCE_25", "REDUCE_50", "TAKE_PROFIT_25", "TAKE_PROFIT_50"]
    )


def is_core_risk_watch_display(data):

    decision = ensure_holding_decision("", data)
    result = data.get("result") or {}
    level = decision.get("level") if decision else ""

    return (
        data.get("holding")
        and level == "HOLD_CORE"
        and stock_pnl(data) >= 8
        and (
            result.get("heat_state") in ["HOT", "EXTREME"]
            or result.get("trade_state") == "EXTENDED"
            or result.get("extended_level", 0) >= 2
        )
        and result.get("price_behavior") in ["VOLUME_DROP", "LOW_VOLUME_PULLBACK", "NORMAL", "LIMIT_LOCK", None]
    )


def is_new_position_loss(data):

    events = data.get("position_events") or {}
    return (
        data.get("holding")
        and events.get("bought_shares", 0) > 0
        and stock_pnl(data) < 0
    )


def is_holding_shakeout_warning_display(data):

    result = data.get("result") or {}

    return (
        data.get("holding")
        and stock_pnl(data) < 0
        and (
            result.get("price_behavior") == "LOW_VOLUME_PULLBACK"
            or result.get("structure_phase") == "SHAKEOUT"
        )
        and (
            result.get("volume_state") == "WEAK"
            or result.get("volume_price_state") == "COILING"
        )
    )


def position_summary_note(name, data):

    decision = ensure_holding_decision(name, data)
    today_text = event_summary_text(data.get("position_events") or {})
    note = decision.get("note") if decision else ""

    action = position_summary_action(name, data)

    if "賣" in today_text and action == "減碼後觀察":
        return note or "已減碼，觀察是否轉弱"

    if action in ["加碼10", "加碼20", "加碼30"]:
        return f"{decision.get('action')}，{decision.get('note') or '條件成立'}"

    if action == "停損":
        return decision.get("note") or "停損優先，避免虧損擴大"

    if action in ["第二段停利", "第二段停利剩餘建議", "第二段停利後觀察", "停利記憶不足"]:
        return second_take_profit_context_text(data, decision)

    if action == "停利":
        return f"{decision.get('action')}，鎖定部分獲利"

    if action == "停利後觀察":
        return decision.get("note") or "同級停利已完成，等待新條件"

    if action == "減碼":
        return f"{decision.get('action')}，降低風險"

    if action == "硬風控減碼":
        return f"{decision.get('action')}，{note or '今日事件後仍需降低風險'}"

    if action == "增量減碼":
        return f"{decision.get('action')}，{note or '補足增量風控'}"

    if action == "核心續抱":
        return "現有持倉保留，按風控續抱；新增倉位等觸發"

    if action == "核心風控觀察":
        return "按風控續抱，守警戒價；新增倉位等觸發"

    if action == "停利後核心倉":
        return "保留核心倉，等待冷卻"

    if action == "減碼後觀察":
        return note or "觀察是否重新站回突破區"

    if action == "洗盤續抱":
        return "縮量回測，未見出貨"

    if action == "洗盤警戒":
        if is_new_position_loss(data):
            return "新倉小虧，守風控"
        return "小虧，暫不加碼"

    if action == "風控觀察":
        return decision.get("note") or "跌破警戒價優先風控"

    if action == "新倉風控觀察":
        return note or "今日剛買入，先看是否守住警戒"

    if action == "續抱觀察":
        return decision.get("note") or "按風控續抱觀察；新增倉位等觸發"

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


def unheld_entry_size_detail_text(result):
    action = result.get("action", 0)

    try:
        if float(action) >= 0.6:
            return "首筆最多 30%，總上限 60%"
    except (TypeError, ValueError):
        pass

    return entry_size_text(result)


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


def unheld_entry_wait_text(result, state, funnel_state):

    if state == "弱勢淘汰" or funnel_state == "淘汰":
        reason = rejected_primary_reason(result)

        if reason == "市場弱":
            return "等市場轉強"

        if reason in ["結構弱", "弱反彈待確認"]:
            return "等結構修復"

        if reason == "突破失敗":
            return "等重新轉強"

        return "重新轉強前不列優先"

    return entry_wait_text(result)


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


def _manifest_status(status):
    if status in ["ready", "ok", "confirmed", "consumed"]:
        return "available"
    if status in ["missing-source", "source-error", "insufficient-data", "not-applicable"]:
        return status
    if status in ["available", "derived"]:
        return status
    return "insufficient-data"


def _manifest_field(
    field_name,
    visible_section,
    value,
    source_status,
    source_of_truth,
    *,
    db_table="unknown",
    as_of_date=None,
    trade_date=None,
    decision_eligible=False,
    fallback_rule="fail closed",
    input_fields=None,
):
    status = _manifest_status(source_status)
    return {
        "field_name": field_name,
        "visible_section": visible_section,
        "value": value,
        "source_status": status,
        "source_of_truth": source_of_truth,
        "db_table": db_table,
        "as_of_date": as_of_date,
        "trade_date": trade_date,
        "decision_eligible": bool(decision_eligible and status in ["available", "derived"]),
        "fallback_rule": fallback_rule,
        "input_fields": input_fields or [],
    }


def _readonly_quote_source(source):
    source = source or "unknown"
    if source in {"realtime", "yahoo", "twse"}:
        return f"approved readonly service: services.stock_api.{source}"
    return "none"


def _price_source_status(data):
    if data.get("price") is None:
        return "insufficient-data"
    if data.get("price_source") in {"realtime", "yahoo", "twse"}:
        return "available"
    return "missing-source"


def _daily_source_status(data):
    if data.get("daily_source") in {"yahoo", "twse"}:
        if data.get("closes") == [] or data.get("volumes") == []:
            return "insufficient-data"
        return "available"
    if not data.get("closes") or not data.get("volumes"):
        return "insufficient-data"
    return "missing-source"


def _derived_status(*statuses):
    if all(status == "available" for status in statuses):
        return "derived"
    if any(status == "source-error" for status in statuses):
        return "source-error"
    if any(status == "missing-source" for status in statuses):
        return "missing-source"
    return "insufficient-data"


def _strategy_sample_status(strategy_evidence_summary):
    text = strategy_evidence_summary or ""
    if not text:
        return "missing-source", "缺 classification backtest source-of-truth"
    if "讀取失敗" in text or "source-error" in text:
        return "source-error", "classification backtest 讀取失敗"
    if "樣本不足" in text or "insufficient" in text:
        return "insufficient-data", "classification backtest 樣本不足或欄位不足"
    if "缺 classification backtest source-of-truth" in text or "狀態：不可用" in text:
        return "missing-source", "缺 classification backtest source-of-truth"
    return "available", "classification backtest source 可用"


def _holding_source_status(data):
    if data.get("holding"):
        return "available"
    return "not-applicable"


def _position_events_source_status(data):
    events = data.get("position_events") or {}
    if not data.get("holding"):
        return "not-applicable"
    if events.get("_source_status") == "unavailable" or events.get("available") is False:
        return "source-error"
    return "available"


def _field_by_key(report_context, key):
    for field in report_context.get("evidence_manifest") or []:
        if field.get("field_name") == key:
            return field
    return {}


def _stock_field(report_context, name, suffix):
    return _field_by_key(report_context, f"stock.{name}.{suffix}")


def _source_status_line(report_context, name, holding=False):
    price = _stock_field(report_context, name, "price").get("source_status", "missing-source")
    rr = _stock_field(report_context, name, "rr").get("source_status", "missing-source")
    daily = _stock_field(report_context, name, "daily_ohlcv").get("source_status", "missing-source")
    if holding:
        position = _stock_field(report_context, name, "position").get("source_status", "missing-source")
        risk = _stock_field(report_context, name, "risk").get("source_status", "missing-source")
        return f"Source：position {position}｜price {price}｜risk {risk}｜RR {rr}"
    score = _stock_field(report_context, name, "score").get("source_status", "missing-source")
    volume = _stock_field(report_context, name, "volume").get("source_status", "missing-source")
    return f"Source：price {price}｜OHLCV {daily}｜RR {rr}｜score {score}｜volume {volume}"


def _stock_decision_source_status(report_context, name):
    if not report_context:
        return "available"
    statuses = [
        _stock_field(report_context, name, "price").get("source_status", "missing-source"),
        _stock_field(report_context, name, "daily_ohlcv").get("source_status", "missing-source"),
        _stock_field(report_context, name, "rr").get("source_status", "missing-source"),
    ]
    if all(status in {"available", "derived"} for status in statuses):
        return "available"
    if "source-error" in statuses:
        return "source-error"
    if "missing-source" in statuses:
        return "missing-source"
    return "insufficient-data"


def _unheld_decision_source_eligible(report_context, name):
    return _stock_decision_source_status(report_context, name) == "available"


def _unheld_source_status_from_fields(price_status, daily_status, rr_status):
    statuses = [price_status, daily_status, rr_status]
    if all(status in {"available", "derived"} for status in statuses):
        return "available"
    if "source-error" in statuses:
        return "source-error"
    if "missing-source" in statuses:
        return "missing-source"
    return "insufficient-data"


def build_report_context(
    results_map,
    market_summary,
    now,
    *,
    strategy_evidence_summary=None,
    report_phase=None,
    position_warning=None,
):
    report_phase = report_phase or get_market_phase()
    as_of_date = now.date().isoformat() if hasattr(now, "date") else None
    trade_date = as_of_date
    if isinstance(market_summary, dict):
        trade_date = market_summary.get("trade_date") or market_summary.get("as_of") or trade_date

    manifest = [
        _manifest_field(
            "report.version",
            "header",
            VERSION,
            "available",
            "core.generator.VERSION",
            db_table="none",
            as_of_date=as_of_date,
            trade_date=trade_date,
            decision_eligible=False,
            fallback_rule="block report if version is absent",
        ),
        _manifest_field(
            "report.report_date",
            "header",
            as_of_date,
            "available" if as_of_date else "insufficient-data",
            "runtime report clock",
            db_table="none",
            as_of_date=as_of_date,
            trade_date=trade_date,
            decision_eligible=False,
            fallback_rule="header shows date unavailable",
        ),
        _manifest_field(
            "report.trade_date",
            "header",
            trade_date,
            "available" if trade_date else "insufficient-data",
            "production report context or market data calendar source",
            db_table="unknown",
            as_of_date=as_of_date,
            trade_date=trade_date,
            decision_eligible=False,
            fallback_rule="fail closed when trade date cannot be confirmed",
        ),
    ]

    market_evidence = market_theme_summary_evidence(results_map, market_summary)
    market_status = _manifest_status(market_evidence.get("source_status"))
    manifest.append(_manifest_field(
        "evidence.market_theme",
        "Evidence",
        market_evidence.get("theme_status") or market_evidence.get("level"),
        market_status,
        "production.market_theme_confirmed_evidence",
        db_table="market_theme_confirmed_evidence",
        as_of_date=market_evidence.get("as_of") or as_of_date,
        trade_date=trade_date,
        decision_eligible=False,
        fallback_rule="market/theme is background only and never upgrades stock action to BUY",
    ))

    strategy_status, strategy_reason = _strategy_sample_status(strategy_evidence_summary)
    manifest.append(_manifest_field(
        "evidence.strategy_sample",
        "Evidence",
        strategy_reason,
        strategy_status,
        "classification backtest source-of-truth" if strategy_status == "available" else "none",
        db_table="daily_signal_snapshot" if strategy_status == "available" else "unknown",
        as_of_date=as_of_date,
        trade_date=trade_date,
        decision_eligible=False,
        fallback_rule="not included in stock decisions when unavailable, insufficient, or source-error",
    ))

    holding_count = 0
    unheld_count = 0
    funnel_inputs = []
    unheld_source_statuses = []
    unheld_source_eligible_count = 0
    for name, data in ordered_result_items(results_map):
        section = "持倉" if data.get("holding") else "新倉"
        holding_count += 1 if data.get("holding") else 0
        unheld_count += 0 if data.get("holding") else 1
        price_status = _price_source_status(data)
        daily_status = _daily_source_status(data)
        rr_status = _derived_status(price_status, daily_status)
        unheld_source_status = _unheld_source_status_from_fields(price_status, daily_status, rr_status)
        score_status = _derived_status(daily_status)
        volume_status = _derived_status(daily_status)
        position_status = _holding_source_status(data)
        event_status = _position_events_source_status(data)
        cross_day = cross_day_context(data)
        cross_day_sources = cross_day.get("source_of_truth") or []
        if isinstance(cross_day_sources, str):
            cross_day_sources = [cross_day_sources]
        if cross_day.get("source_status") in ["source-error", "missing-source", "insufficient-data"]:
            execution_status = cross_day.get("source_status")
        elif cross_day.get("source_status") == "ready" and "position_events" in cross_day_sources:
            execution_status = "available"
        else:
            execution_status = event_status
        risk_status = _derived_status(
            position_status if position_status != "not-applicable" else "available",
            price_status,
            event_status if event_status != "not-applicable" else "available",
        )
        source_truth = _readonly_quote_source(data.get("price_source"))
        daily_truth = _readonly_quote_source(data.get("daily_source"))
        stock_key = f"stock.{name}"
        manifest.extend([
            _manifest_field(
                f"{stock_key}.price",
                section,
                data.get("price"),
                price_status,
                source_truth,
                db_table="unknown",
                as_of_date=as_of_date,
                trade_date=trade_date,
                decision_eligible=price_status == "available",
                fallback_rule="do not output precise entry/exit price when unavailable",
            ),
            _manifest_field(
                f"{stock_key}.volume",
                section,
                data.get("volume_ratio"),
                volume_status,
                "derived-from fields",
                db_table="unknown",
                as_of_date=as_of_date,
                trade_date=trade_date,
                decision_eligible=volume_status == "derived",
                fallback_rule="volume judgment is not decision eligible when daily source is incomplete",
                input_fields=[f"{stock_key}.daily_ohlcv"],
            ),
            _manifest_field(
                f"{stock_key}.rr",
                section,
                (data.get("result") or {}).get("rr"),
                rr_status,
                "derived-from fields",
                db_table="none",
                as_of_date=as_of_date,
                trade_date=trade_date,
                decision_eligible=rr_status == "derived",
                fallback_rule="do not show RR as buy reason unless price and daily inputs are available",
                input_fields=[f"{stock_key}.price", f"{stock_key}.daily_ohlcv"],
            ),
            _manifest_field(
                f"{stock_key}.score",
                section,
                data.get("structure_score") or (data.get("result") or {}).get("strength"),
                score_status,
                "derived-from fields",
                db_table="none",
                as_of_date=as_of_date,
                trade_date=trade_date,
                decision_eligible=score_status == "derived",
                fallback_rule="score cannot upgrade stock action by itself",
                input_fields=[f"{stock_key}.daily_ohlcv"],
            ),
            _manifest_field(
                f"{stock_key}.daily_ohlcv",
                section,
                data.get("daily_source"),
                daily_status,
                daily_truth,
                db_table="unknown",
                as_of_date=as_of_date,
                trade_date=trade_date,
                decision_eligible=daily_status == "available",
                fallback_rule="stock is not decision eligible when OHLCV is unavailable",
            ),
            _manifest_field(
                f"{stock_key}.position",
                "持倉",
                data.get("holding"),
                position_status,
                "production DB position source" if data.get("holding") else "none",
                db_table="positions" if data.get("holding") else "none",
                as_of_date=as_of_date,
                trade_date=trade_date,
                decision_eligible=position_status == "available",
                fallback_rule="do not output sell/reduce shares without position source",
            ),
            _manifest_field(
                f"{stock_key}.execution_memory",
                "持倉",
                cross_day.get("execution_memory") or data.get("position_events"),
                execution_status,
                "production DB position_events",
                db_table="position_events",
                as_of_date=as_of_date,
                trade_date=trade_date,
                decision_eligible=execution_status == "available",
                fallback_rule="fail closed for second take-profit when position_events cannot confirm execution",
            ),
            _manifest_field(
                f"{stock_key}.risk",
                "持倉" if data.get("holding") else section,
                position_summary_action(name, data) if data.get("holding") else unheld_funnel_state(name, data),
                risk_status if data.get("holding") else rr_status,
                "existing stock decision / risk logic",
                db_table="none",
                as_of_date=as_of_date,
                trade_date=trade_date,
                decision_eligible=(risk_status == "derived" if data.get("holding") else rr_status == "derived"),
                fallback_rule="source gaps downgrade to observation or not actionable; never override BUY/SELL",
                input_fields=[f"{stock_key}.position", f"{stock_key}.execution_memory", f"{stock_key}.price", f"{stock_key}.rr"],
            ),
        ])
        if not data.get("holding"):
            funnel_inputs.append(f"{stock_key}.risk")
            unheld_source_statuses.append(unheld_source_status)
            if unheld_source_status == "available":
                unheld_source_eligible_count += 1

    funnel_status = "derived"
    if unheld_source_statuses and not unheld_source_eligible_count:
        if "source-error" in unheld_source_statuses:
            funnel_status = "source-error"
        elif "missing-source" in unheld_source_statuses:
            funnel_status = "missing-source"
        else:
            funnel_status = "insufficient-data"
    manifest.append(_manifest_field(
        "funnel.unheld_counts",
        "漏斗",
        {"holding_count": holding_count, "unheld_count": unheld_count},
        funnel_status,
        "report evidence manifest aggregate",
        db_table="none",
        as_of_date=as_of_date,
        trade_date=trade_date,
        decision_eligible=funnel_status == "derived",
        fallback_rule="do not show fake 0-count conclusion when source is missing",
        input_fields=funnel_inputs,
    ))
    manifest.append(_manifest_field(
        "tomorrow.plan",
        "明日計畫",
        "derived from final report decisions",
        funnel_status,
        "derived-from fields",
        db_table="none",
        as_of_date=as_of_date,
        trade_date=trade_date,
        decision_eligible=funnel_status == "derived",
        fallback_rule="items with source gaps stay out of tomorrow execution plan",
        input_fields=["funnel.unheld_counts"],
    ))

    if position_warning:
        position_status = "missing-source" if "missing" in str(position_warning).lower() else "source-error"
    elif holding_count:
        position_status = "available"
    else:
        position_status = "not-applicable"

    context = {
        "report_context": {
            "version": VERSION,
            "report_phase": report_phase,
            "as_of_date": as_of_date,
            "trade_date": trade_date,
        },
        "evidence_manifest": manifest,
        "market_theme_evidence": market_evidence,
        "source_status_summary": {
            "price": "available" if any(
                _price_source_status(data) == "available"
                for data in results_map.values()
            ) else "insufficient-data",
            "position": position_status,
            "strategy_sample": strategy_status,
            "market_theme": market_status,
            "funnel": funnel_status,
        },
    }
    context["source_status_text"] = (
        f"核心價格 {context['source_status_summary']['price']}；"
        f"持倉 {context['source_status_summary']['position']}；"
        f"策略樣本 {context['source_status_summary']['strategy_sample']}；"
        f"market/theme {context['source_status_summary']['market_theme']}"
    )
    return context


def holding_tomorrow_trigger(name, data):

    decision = ensure_holding_decision(name, data)
    action = position_summary_action(name, data)
    level = decision.get("level") if decision else ""

    if level == "STOP_100":
        return "清出後等重新買點"

    if action in ["第二段停利", "第二段停利剩餘建議", "第二段停利後觀察", "停利記憶不足"]:
        return second_take_profit_context_text(data, decision)

    duplicate_action = cross_day_duplicate_action(data, decision)
    if duplicate_action == "take_profit":
        return "歷史停利已完成，等待新條件"
    if duplicate_action == "reduce":
        return "歷史減碼已完成，等待新條件"

    if level in ["REDUCE_25", "REDUCE_50"]:
        return "無法重新站回突破區，繼續降低優先級"

    if level == "POST_REDUCE_WATCH":
        return "修復才恢復優先級"

    if level == "NEW_POSITION_RISK_WATCH":
        return "明日未修復降級"

    if level in ["TAKE_PROFIT_25", "TAKE_PROFIT_50"]:
        return "保留核心倉，等待冷卻後再評估"

    if level == "POST_PROFIT_WATCH":
        return "等待新高、過熱升級或風控訊號"

    if action == "新倉風控觀察":
        return "明日未修復降級"

    if level in ["ADD_10", "ADD_20", "ADD_30"]:
        return "加碼後守警戒價，量價未延續則停止加碼"

    if action == "洗盤警戒":
        return "跌破警戒升級風控"

    if action == "核心風控觀察":
        return "守警戒價"

    if action == "減碼後觀察":
        return "修復才恢復優先級"

    if action == "停利後核心倉":
        return "等待冷卻後再評估"

    if action == "洗盤續抱":
        return "跌破警戒升級風控"

    if action == "核心續抱":
        return "守警戒價，觀察是否轉弱"

    if action == "續抱觀察":
        return "無法接近買點則降級"

    return "暫不加碼"


def position_priority_rank(name, data):

    action = position_summary_action(name, data)
    level = (ensure_holding_decision(name, data) or {}).get("level", "")
    rank = {
        "停損": 0,
        "硬風控減碼": 1,
        "增量減碼": 1,
        "減碼": 1,
        "第二段停利": 1,
        "第二段停利剩餘建議": 1,
        "停利記憶不足": 2,
        "停利": 1,
        "新倉風控觀察": 2,
        "風控觀察": 3,
        "核心風控觀察": 3,
        "減碼後觀察": 4,
        "停利後觀察": 4,
        "洗盤警戒": 5,
        "洗盤續抱": 6,
        "停利後核心倉": 7,
        "核心續抱": 7,
        "續抱觀察": 8,
        "續抱": 9,
    }

    if level in ["STOP_100"]:
        return (0, stock_pnl(data))

    return (rank.get(action, 9), stock_pnl(data))


def format_position_priority(holding_items):

    if not holding_items:
        return ["無持倉"]

    ordered = sorted(holding_items, key=lambda item: position_priority_rank(item[0], item[1]))
    lines = []

    for index, (name, data) in enumerate(ordered, start=1):
        lines.append(
            f"{index}. {name}"
            f"｜{position_summary_action(name, data)}"
            f"｜{holding_tomorrow_trigger(name, data)}"
        )

    return lines


def holding_execution_label(name, data):

    action = position_summary_action(name, data)

    if action == "續抱":
        return "續抱觀察"

    return action


def holding_execution_priority(name, data):

    action = holding_execution_label(name, data)
    level = (ensure_holding_decision(name, data) or {}).get("level", "")
    rank = {
        "停損": 0,
        "硬風控減碼": 1,
        "增量減碼": 1,
        "減碼": 1,
        "第二段停利": 2,
        "第二段停利剩餘建議": 2,
        "停利記憶不足": 3,
        "停利": 2,
        "新倉風控觀察": 3,
        "風控觀察": 4,
        "核心風控觀察": 4,
        "洗盤警戒": 5,
        "減碼後觀察": 6,
        "停利後觀察": 6,
        "洗盤續抱": 7,
        "停利後核心倉": 8,
        "核心續抱": 8,
        "續抱觀察": 9,
    }

    if level == "STOP_100":
        return (0, stock_pnl(data))

    return (rank.get(action, 9), stock_pnl(data))


def holding_execution_item(name, data):

    label = holding_execution_label(name, data)
    trigger = holding_tomorrow_trigger(name, data)
    events = data.get("position_events") or {}
    decision = ensure_holding_decision(name, data) or {}
    second_profit_state = second_take_profit_execution_state(data, decision)

    if label == "續抱觀察" and trigger == "暫不加碼":
        trigger = "暫不加碼，守警戒"

    if second_profit_state["status"] == "completed":
        context = second_take_profit_context_text(data, decision)
        return {
            "name": name,
            "kind": "holding",
            "state": "已執行",
            "priority": holding_execution_priority(name, data),
            "is_control": True,
            "control_line": f"{name}｜第二段停利後觀察｜{context}",
            "line": f"{name}｜已執行｜{context}",
        }

    if (
        events.get("sold_shares", 0) > 0
        and decision.get("level") == "POST_PROFIT_WATCH"
    ):
        sold_shares = events.get("sold_shares", 0)
        remaining_shares = (data.get("holding") or {}).get("shares", 0)
        executed_text = (
            f"今日已執行停利 {sold_shares} 股"
            if sold_shares
            else "今日已執行停利"
        )
        remaining_text = (
            f"成交後剩餘 {remaining_shares} 股"
            if remaining_shares
            else "剩餘部位觀察"
        )
        return {
            "name": name,
            "kind": "holding",
            "state": "已執行",
            "priority": holding_execution_priority(name, data),
            "is_control": True,
            "control_line": (
                f"{name}"
                f"｜停利後觀察"
                f"｜{remaining_text}"
                f"｜同級停利已完成"
            ),
            "line": (
                f"{name}"
                f"｜已執行"
                f"｜{executed_text}"
                f"｜{remaining_text}"
                f"｜同級停利已完成"
            ),
        }

    return {
        "name": name,
        "kind": "holding",
        "state": label,
        "priority": holding_execution_priority(name, data),
        "is_control": label in [
            "停損",
            "硬風控減碼",
            "增量減碼",
            "減碼",
            "第二段停利",
            "第二段停利剩餘建議",
            "停利",
            "新倉風控觀察",
            "風控觀察",
            "核心風控觀察",
            "洗盤警戒",
            "停利後觀察",
            "停利記憶不足",
        ],
        "line": (
            f"{name}"
            f"｜{signed_pct(stock_pnl(data))}"
            f"｜{label}"
            f"｜{trigger}"
        ),
    }


def strong_prepare_bucket(data):

    result = data.get("result") or {}
    blockers = entry_blockers(result)
    behavior = result.get("price_behavior")
    heat = result.get("heat_state")
    trade = result.get("trade_state")
    distance = result.get("breakout_distance")
    phase = result.get("structure_phase")

    if behavior in ["LIMIT_LOCK", "LIMIT_REBOUND"] or any(item in blockers for item in ["漲停不追", "漲停反彈待確認"]):
        return "漲停鎖價", "不可追高，待開板回測"

    if (
        heat in ["HOT", "EXTREME"]
        or trade in ["EXTENDED", "AVOID"]
        or any(item.startswith("過熱") for item in blockers)
    ):
        return "過熱降溫", "不可買，待降溫後重評"

    blocker_set = set(blockers)
    near_breakout = (
        phase == "BREAKOUT_NEAR"
        or behavior == "BREAKOUT_NEAR"
        or (distance is not None and 0 <= distance <= 4)
    )
    if near_breakout and not blocker_set.intersection({"RR不足", "量能不足", "市場弱", "弱反彈待確認"}):
        return "突破回測", "待觸發，不追高"

    return None, None


def unheld_funnel_state(name, data, market_mode=None, report_context=None):

    result = data.get("result") or {}
    state = tomorrow_watch_state(name, data)
    blockers = entry_blockers(result)

    if is_valid_entry(result) and not _unheld_decision_source_eligible(report_context, name):
        return "淘汰"

    if is_valid_entry(result):
        return "可買"

    if cross_day_prepare_promotion(data):
        return "可準備"

    if state == "弱勢淘汰":
        return "淘汰"

    prepare_label, _prepare_action = strong_prepare_bucket(data)
    if market_mode == "進攻偏熱" and prepare_label:
        return "可準備"

    if state == "等冷卻":
        return "等冷卻"

    if state == "等回測":
        return "等回測"

    if state == "等RR修復":
        return "等RR修復"

    if state == "等量能":
        return "等量能"

    if (
        state == "隔日確認"
        or result.get("market_grade") in ["A+", "A", "B"]
        or result.get("entry_quality") in ["A+", "A", "B"]
        or any(item in blockers for item in ["弱反彈待確認", "漲停反彈待確認"])
    ):
        return "可準備"

    return "淘汰"


def unheld_execution_trigger(funnel_state, data):

    watch_state = tomorrow_watch_state("", data)
    trigger = tomorrow_trigger_text(watch_state, data)
    result = data.get("result") or {}
    action = result.get("action", 0)

    if funnel_state == "可買":
        try:
            size_pct = round(float(action) * 100)
        except (TypeError, ValueError):
            size_pct = 0

        if size_pct >= 60:
            return "首筆最多 30%，總上限 60%｜分批，不追價"

        return "分批，不追價"

    if funnel_state == "可準備":
        return f"不可買，{trigger or '等條件確認'}"

    if funnel_state == "等冷卻":
        return "不追價，等冷卻降溫"

    if funnel_state == "等回測":
        return "不追價，回測不破且降溫再評估"

    if funnel_state == "等RR修復":
        return "不追價，等RR達標"

    if funnel_state == "等量能":
        return "不買，等量能回升"

    return trigger or "重新轉強前不列優先"


def unheld_execution_priority(index, name, data, market_mode=None, report_context=None):

    funnel_state = unheld_funnel_state(name, data, market_mode=market_mode, report_context=report_context)
    rank = {
        "可買": 0,
        "可準備": 3,
        "等冷卻": 4,
        "等回測": 5,
        "等RR修復": 6,
        "等量能": 7,
        "淘汰": 9,
    }
    stock_order = list(STOCKS).index(name) if name in STOCKS else index

    return (
        rank.get(funnel_state, 9)
        + backtest_tracking_adjustment(data.get("backtest_context"))
        + cross_day_sort_adjustment(data),
        stock_order,
    )


def unheld_execution_item(index, name, data, market_mode=None, report_context=None):

    state = unheld_funnel_state(name, data, market_mode=market_mode, report_context=report_context)

    if state != "可買":
        return None

    return {
        "name": name,
        "kind": "watch",
        "state": state,
        "priority": unheld_execution_priority(index, name, data, market_mode=market_mode),
        "is_control": False,
        "line": (
            f"{name}"
            f"｜{state}"
            f"｜{unheld_execution_trigger(state, data)}"
        ),
    }


def build_unheld_funnel(watch_items, market_mode=None, report_context=None):

    groups = {
        "可買": [],
        "可準備": [],
        "等冷卻": [],
        "等回測": [],
        "等RR修復": [],
        "等量能": [],
        "淘汰": [],
    }

    for name, data in watch_items:
        groups[unheld_funnel_state(name, data, market_mode=market_mode, report_context=report_context)].append(name)

    return groups


def dominant_reject_reasons(watch_items, market_mode=None, report_context=None):

    reason_counts = {}

    for name, data in watch_items:
        if unheld_funnel_state(name, data, market_mode=market_mode, report_context=report_context) != "淘汰":
            continue

        source_status = _stock_decision_source_status(report_context, name)
        reason = "source missing" if source_status != "available" else rejected_primary_reason(data.get("result") or {})
        if not reason:
            reason = "條件不足"
        reason_counts[reason] = reason_counts.get(reason, 0) + 1

    if not reason_counts:
        return "無"

    ordered = sorted(reason_counts.items(), key=lambda item: (-item[1], item[0]))
    return "、".join(reason for reason, _count in ordered[:2])


def rejected_primary_reason(result):

    blockers = entry_blockers(result)
    phase = result.get("structure_phase")

    if result.get("decision") == "FAIL" or phase == "FAILED_BREAKOUT" or "突破失敗" in blockers:
        return "突破失敗"

    if phase == "WEAK_REBOUND" or result.get("price_behavior") == "WEAK_REBOUND" or "弱反彈待確認" in blockers:
        return "弱反彈待確認"

    if result.get("market_grade") == "D" or "市場弱" in blockers:
        return "市場弱"

    if "RR不足" in blockers:
        return "RR不可用"

    if phase in ["WEAK", "DISTRIBUTION"]:
        return "結構弱"

    for reason in blockers:
        if reason not in ["RR不足", "量能不足", "遠離觸發", "過熱觀察"] and not reason.startswith("過熱"):
            return reason

    return final_label(result)


def unheld_tracking_count(funnel):

    return sum(
        len(funnel[label])
        for label in ["可準備", "等冷卻", "等回測", "等RR修復", "等量能"]
    )


def unheld_tracking_only_count(funnel):

    return sum(
        len(funnel[label])
        for label in ["等冷卻", "等回測", "等RR修復", "等量能"]
    )


def today_conclusion_text(holding_items, watch_items, market_mode, risk_level, report_phase=None, report_context=None):

    funnel = build_unheld_funnel(watch_items, market_mode=market_mode, report_context=report_context)
    pending_count = len(pending_trade_items(holding_items, watch_items, market_mode=market_mode, report_context=report_context))
    executed_count = len(executed_trade_items(holding_items, watch_items, market_mode=market_mode, report_context=report_context))
    tracking_count = unheld_tracking_count(funnel)
    prepare_count = len(funnel["可準備"])
    tracking_only_count = unheld_tracking_only_count(funnel)
    holding_count = len(holding_items)
    intraday = report_phase in (None, "盤中")
    execution_label = "交易執行" if intraday else "明日計畫"
    no_new_entry_text = "交易執行：無新增下單" if intraday else "新倉：無有效進場"

    if pending_count:
        base = f"{risk_level} {market_mode}"
        if holding_count and not intraday:
            base += f"；持倉風控檢查 {holding_count} 檔；{execution_label} {pending_count} 項"
        else:
            base += f"；{execution_label} {pending_count} 項"
        if holding_count and intraday:
            base += f"；持倉風控檢查 {holding_count} 檔"
        if executed_count:
            base += f"；已執行 {executed_count} 項不重複"
        if prepare_count and tracking_only_count:
            return f"{base}；未持倉 {prepare_count} 檔可準備、{tracking_only_count} 檔僅追蹤"
        if prepare_count:
            return f"{base}；未持倉 {prepare_count} 檔可準備"
        if tracking_only_count:
            return f"{base}；未持倉 {tracking_count} 檔僅追蹤"
        return f"{base}；未持倉無追蹤"

    if holding_count:
        base = f"{risk_level} {market_mode}；{no_new_entry_text}；持倉風控檢查 {holding_count} 檔"
        if executed_count:
            base += f"；已執行 {executed_count} 項不重複"
        if prepare_count and tracking_only_count:
            return f"{base}；未持倉 {prepare_count} 檔可準備、{tracking_only_count} 檔僅追蹤"
        if prepare_count:
            return f"{base}；未持倉 {prepare_count} 檔可準備"
        if tracking_only_count:
            return f"{base}；未持倉 {tracking_count} 檔僅追蹤"
        return f"{base}；未持倉無追蹤"

    if prepare_count and tracking_only_count:
        return f"{risk_level} {market_mode}；{no_new_entry_text}；未持倉 {prepare_count} 檔可準備、{tracking_only_count} 檔僅追蹤"

    if prepare_count:
        return f"{risk_level} {market_mode}；{no_new_entry_text}；未持倉 {prepare_count} 檔可準備"

    if tracking_only_count:
        return f"{risk_level} {market_mode}；{no_new_entry_text}；未持倉 {tracking_count} 檔僅追蹤"

    return f"{risk_level} {market_mode}；{no_new_entry_text}；未持倉無追蹤"


def today_reason_text(watch_items, market_mode, report_phase=None, report_context=None):

    funnel = build_unheld_funnel(watch_items, market_mode=market_mode, report_context=report_context)

    if funnel["可買"]:
        if report_phase not in (None, "盤中"):
            return "盤後只列明日追蹤，開盤後再確認，不追價"
        return "存在合格買點，分批執行，不追價"

    if market_mode == "進攻偏熱":
        if funnel["等RR修復"]:
            return "強勢股多過熱，RR不足，不追高"
        return "強勢股多過熱，新倉等回測與降溫"

    if market_mode == "轉弱":
        return "弱勢淘汰偏多，先控新倉"

    if funnel["等RR修復"] and funnel["等回測"]:
        return "RR與追價風險仍在，等觸發再評估"

    if funnel["等RR修復"]:
        return "RR不足，不追價"

    if funnel["等回測"]:
        return "追價風險仍在，等回測確認"

    return "依今日條件排序，未觸發不新增"


def build_execution_items(holding_items, watch_items, market_mode=None, report_context=None):

    holding_items = sorted(holding_items, key=lambda item: holding_execution_priority(item[0], item[1]))
    watch_items = sorted(
        enumerate(watch_items),
        key=lambda item: unheld_execution_priority(
            item[0], item[1][0], item[1][1], market_mode=market_mode, report_context=report_context
        )
    )

    items = [
        holding_execution_item(name, data)
        for name, data in holding_items
    ]

    for index, (name, data) in watch_items:
        item = unheld_execution_item(index, name, data, market_mode=market_mode, report_context=report_context)
        if item:
            items.append(item)

    return items


def pending_trade_items(holding_items, watch_items, market_mode=None, report_context=None):

    pending_states = {
        "可買",
        "停損",
        "硬風控減碼",
        "增量減碼",
        "減碼",
        "第二段停利",
        "第二段停利剩餘建議",
        "停利",
        "加碼10",
        "加碼20",
        "加碼30",
    }
    return [
        item for item in build_execution_items(
            holding_items, watch_items, market_mode=market_mode, report_context=report_context
        )
        if item.get("state") in pending_states
    ]


def executed_trade_items(holding_items, watch_items, market_mode=None, report_context=None):

    return [
        item for item in build_execution_items(
            holding_items, watch_items, market_mode=market_mode, report_context=report_context
        )
        if item.get("state") == "已執行"
    ]


def holding_control_items(holding_items):

    return [
        holding_execution_item(name, data)
        for name, data in sorted(holding_items, key=lambda item: holding_execution_priority(item[0], item[1]))
    ]


def post_market_plan_line(item):

    if item.get("kind") == "watch":
        return f"{item['name']}｜明日追蹤｜開盤後確認，不追價"

    if item.get("state") in ["加碼10", "加碼20", "加碼30"]:
        return f"{item['name']}｜待觸發{item.get('state')}"

    return f"{item['name']}｜明日風控｜{item.get('state') or '待確認'}"


def format_execution_checklist(holding_items, watch_items, limit=5, report_phase=None, market_mode=None, report_context=None):

    items = pending_trade_items(holding_items, watch_items, market_mode=market_mode, report_context=report_context)
    funnel = build_unheld_funnel(watch_items, market_mode=market_mode, report_context=report_context)
    tracking_count = unheld_tracking_count(funnel)
    prepare_count = len(funnel["可準備"])
    tracking_only_count = unheld_tracking_only_count(funnel)
    intraday = report_phase in (None, "盤中")
    tracking_suffix = (
        "不列入今日盤中交易執行"
        if intraday
        else "不列入明日計畫"
    )

    if not items:
        lines = ["無新增下單"]
        if prepare_count and tracking_only_count:
            lines.append(f"未持倉 {prepare_count} 檔可準備、{tracking_only_count} 檔僅追蹤，等觸發，{tracking_suffix}")
        elif prepare_count:
            lines.append(f"未持倉 {prepare_count} 檔可準備，等觸發，{tracking_suffix}")
        elif tracking_only_count:
            lines.append(f"未持倉 {tracking_count} 檔僅追蹤，等觸發，{tracking_suffix}")
        return lines

    displayed = items[:limit]
    lines = [
        f"{index}. {item['line'] if intraday else post_market_plan_line(item)}"
        for index, item in enumerate(displayed, start=1)
    ]

    if len(items) > len(displayed):
        if intraday:
            lines.append(f"另有 {len(items) - len(displayed)} 項交易執行見詳情")
        else:
            lines.append(f"另有 {len(items) - len(displayed)} 項明日計畫見詳情")

    if prepare_count and tracking_only_count:
        lines.append(f"未持倉 {prepare_count} 檔可準備、{tracking_only_count} 檔只等觸發，{tracking_suffix}")
    elif prepare_count:
        lines.append(f"未持倉 {prepare_count} 檔可準備，{tracking_suffix}")
    elif tracking_only_count:
        lines.append(f"未持倉 {tracking_count} 檔只等觸發，{tracking_suffix}")

    return lines


def format_executed_checklist(holding_items, watch_items, limit=3):

    items = executed_trade_items(holding_items, watch_items)

    if not items:
        return []

    lines = [
        f"{index}. {item['line']}"
        for index, item in enumerate(items[:limit], start=1)
    ]

    if len(items) > limit:
        lines.append(f"另有 {len(items) - limit} 項已執行見詳情")

    return lines


def intraday_holding_control_line(item, report_phase):

    line = item["line"]

    if item.get("state") in ["加碼10", "加碼20", "加碼30"]:
        return f"{item['name']}｜風控：守警戒線，不追價"

    if report_phase != "盤中":
        return line

    if item.get("state") == "已執行":
        if item.get("control_line"):
            return item["control_line"]
        return f"{item['name']}｜剩餘部位觀察｜不加碼"

    if "明日未修復" in line or "隔日未修復" in line:
        parts = line.split("｜")
        if len(parts) >= 4:
            return "｜".join(parts[:3] + ["盤中觀察修復狀況"])

    return line


def format_holding_control_checklist(holding_items, limit=5, report_phase=None):

    items = holding_control_items(holding_items)

    if not items:
        return ["無持倉"]

    lines = [
        f"{index}. {intraday_holding_control_line(item, report_phase)}"
        for index, item in enumerate(items[:limit], start=1)
    ]

    if len(items) > limit:
        lines.append(f"另有 {len(items) - limit} 項持倉風控見詳情")

    return lines


def format_unheld_funnel(watch_items, market_mode=None, report_context=None):
    funnel = build_unheld_funnel(watch_items, market_mode=market_mode, report_context=report_context)
    tracking_count = unheld_tracking_count(funnel)
    tracking_only_count = unheld_tracking_only_count(funnel)
    prepare_count = len(funnel["可準備"])
    split_parts = [
        f"{label} {len(funnel[label])}"
        for label in ["等冷卻", "等回測", "等RR修復", "等量能"]
        if funnel[label]
    ]
    lines = [
        f"未持倉總數 {sum(len(items) for items in funnel.values())} 檔",
        (
            f"可買 {len(funnel['可買'])}"
            f"｜可準備 {prepare_count}（不可買）"
            f"｜僅追蹤 {tracking_only_count}"
            f"｜淘汰 {len(funnel['淘汰'])}"
        ),
    ]

    if split_parts:
        lines.append(f"其中僅追蹤 {tracking_only_count} 檔拆分：" + "、".join(split_parts))

    if prepare_count and tracking_only_count:
        lines.append(f"非執行準備/追蹤合計 {tracking_count} 檔（可準備 {prepare_count}｜僅追蹤 {tracking_only_count}）")
    elif prepare_count:
        lines.append(f"可準備 {prepare_count} 檔，不列入交易執行")
    elif tracking_only_count:
        lines.append(f"僅追蹤 {tracking_only_count} 檔，不列入交易執行")

    return "\n".join(lines)


def detail_index_text(holding_items, watch_items, report_phase=None, market_mode=None, report_context=None):

    funnel = build_unheld_funnel(watch_items, market_mode=market_mode, report_context=report_context)
    execution_count = len(pending_trade_items(
        holding_items, watch_items, market_mode=market_mode, report_context=report_context
    ))
    prepare_count = len(funnel["可準備"])
    tracking_only_count = unheld_tracking_only_count(funnel)
    rejected = funnel["淘汰"]
    execution_label = "明日計畫" if report_phase not in (None, "盤中") else "交易執行"
    parts = [f"📎 詳情索引：持倉 {len(holding_items)}"]

    if report_phase in (None, "盤中") or execution_count:
        parts.append(f"{execution_label} {execution_count}")

    if prepare_count:
        parts.append(f"可準備 {prepare_count}")
    if tracking_only_count:
        parts.append(f"僅追蹤 {tracking_only_count}")
    parts.append(f"淘汰 {len(rejected)}")

    return "｜".join(parts)


def rejected_trace_line(watch_items, market_mode=None, report_context=None):

    funnel = build_unheld_funnel(watch_items, market_mode=market_mode, report_context=report_context)
    rejected = funnel["淘汰"]

    if not rejected:
        return None

    return (
        f"淘汰 {len(rejected)} 檔｜主因："
        f"{dominant_reject_reasons(watch_items, market_mode=market_mode, report_context=report_context)}"
        "｜詳情見未持倉卡"
    )


def ai_supply_chain_mainline_supported(market_summary):

    if isinstance(market_summary, dict):
        evidence = market_theme_summary_evidence({}, market_summary)
        return bool(
            evidence.get("confirmed")
            and evidence.get("theme_direction") == "bullish"
        )

    return False


def market_theme_summary_evidence(results_map, market_summary, evidence_loader=None):
    loader = evidence_loader or load_confirmed_market_theme_evidence

    if isinstance(market_summary, dict):
        evidence = market_summary.get("market_theme_evidence")
        if not evidence:
            loaded = loader(
                trade_date=market_summary.get("trade_date")
            )
            evidence = loaded
        report_date = market_summary.get("as_of")
        return build_market_theme_evidence_provider(
            results_map=results_map,
            formatter_report_input=market_summary,
            market_theme_evidence=evidence,
            as_of=report_date,
        )

    loaded = loader()
    if loaded.get("status") in {"confirmed", "absent", "missing-source", "source-error", "insufficient-data"}:
        return build_market_theme_evidence_provider(
            results_map=results_map,
            formatter_report_input=market_summary,
            market_theme_evidence=loaded,
            as_of=loaded.get("as_of"),
        )

    return build_market_theme_evidence(
        results_map=results_map,
        formatter_report_input=market_summary,
        missing_db_evidence=True,
    )


def build_market_theme_production_trend_consumption_check(client=None, trade_date=None, limit=20):
    load_result = {}

    def loader(trade_date=None):
        nonlocal load_result
        load_result = load_confirmed_market_theme_evidence(
            client=client,
            trade_date=trade_date,
            limit=limit,
        )
        return load_result

    market_summary = {
        "trade_date": trade_date,
        "as_of": trade_date,
    }
    evidence = market_theme_summary_evidence(
        {},
        market_summary,
        evidence_loader=loader,
    )
    trend = evidence.get("evidence_trend") or {}
    uses_history = bool(
        evidence.get("confirmed")
        and evidence.get("source_status") == "ready"
        and trend.get("observed_days", 0) > 0
    )
    source_status = load_result.get("status") or evidence.get("source_status") or "insufficient-data"
    confirmed_table_status = (
        "consumed"
        if uses_history
        else source_status
        if source_status in {"missing-source", "source-error", "insufficient-data"}
        else "insufficient-data"
    )
    blocked_reasons = []
    if not uses_history:
        blocked_reasons.append("official generator path does not consume production evidence trend")
        reason = load_result.get("reason")
        if reason:
            blocked_reasons.append(reason)

    return {
        "mode": "market-theme-production-trend-consumption-check",
        "schema_change": False,
        "data_write": False,
        "live_telegram": False,
        "source_of_truth": "production.market_theme_confirmed_evidence",
        "local_context_cleared": True,
        "fresh_runner_rebuild": "passed" if uses_history else "blocked",
        "generator_consumption": {
            "entrypoint": "core.generator.market_theme_summary_evidence",
            "uses_market_theme_confirmed_evidence_history": uses_history,
            "uses_only_daily_signal_snapshot": False,
            "uses_runtime_or_local_cache_as_history": False,
            "observed_days": trend.get("observed_days", 0),
            "recent_supporting_days": trend.get("recent_supporting_days", 0),
            "support_streak_days": trend.get("support_streak_days", 0),
        },
        "table_status": {
            "market_theme_confirmed_evidence": confirmed_table_status,
            "sector_theme_members": "latest-only-blocked",
            "market_theme_index_daily_bars": "not-consumed",
        },
        "blocked_reasons": blocked_reasons,
    }


def _integrity_status_from_source_status(status):
    if status in {"passed", "consumed", "ok"}:
        return "passed"
    if status in {"missing-source", "source-error", "insufficient-data", "blocked"}:
        return "blocked"
    return "failed"


def _extract_messages_from_report(report_result):
    if isinstance(report_result, tuple):
        report_result = report_result[0]
    if isinstance(report_result, list):
        return [str(message) for message in report_result]
    if isinstance(report_result, str):
        return [report_result]
    return []


def _report_conflicts(messages):
    if not messages:
        return ["dry-run report sample missing"]

    joined = "\n\n".join(messages)
    summary = messages[-1]
    conflicts = []
    buy_markers = re.findall(r"新倉[:：][^\n]*?([\u4e00-\u9fffA-Za-z0-9]{2,12})\s*可買", summary)
    blocking_terms = ("不可買", "等冷卻", "等回測", "等RR修復", "等量能", "淘汰")
    for marker in buy_markers:
        if marker in {"無有效進場", "無", "今日"}:
            continue
        for line in joined.splitlines():
            if marker in line and any(term in line for term in blocking_terms):
                conflicts.append(f"summary says BUY but report blocks {marker}: {line.strip()}")
                break

    for message in messages:
        if "已執行" in message and "待執行" in message:
            conflicts.append("same section mixes executed and pending wording")
            break

    return conflicts


def analyze_report_cross_section_integrity(messages, telegram_header_version=VERSION):
    messages = _extract_messages_from_report(messages)
    joined = "\n\n".join(messages)
    summary = messages[-1] if messages else ""
    conflicts = _report_conflicts(messages)
    has_funnel = "未持倉漏斗" in joined or "Funnel" in joined
    has_cards = "【持倉標的】" in joined or "【未持倉標的】" in joined
    has_checklist = "今日盤中交易執行" in joined or "交易執行" in summary
    version_ok = bool(messages) and telegram_header_version in summary

    action_status = "passed" if not conflicts else "blocked"
    counts_status = "passed" if has_funnel else "blocked"
    categories_status = "passed" if has_cards and not conflicts else "blocked"
    checklist_status = "passed" if has_checklist and not conflicts else "blocked"

    blocked_reasons = list(conflicts)
    if not version_ok:
        blocked_reasons.append(f"Telegram header version {telegram_header_version} not found in summary")
    if messages and not has_funnel:
        blocked_reasons.append("dry-run report lacks unheld funnel for count/category trace")
    if messages and not has_cards:
        blocked_reasons.append("dry-run report lacks holding/unheld cards for decision trace")
    if messages and not has_checklist:
        blocked_reasons.append("dry-run report lacks execution checklist wording")

    return {
        "decision_display_consistency": {
            "strategy_vs_summary": action_status if version_ok else "blocked",
            "strategy_vs_cards": categories_status,
            "strategy_vs_checklist": checklist_status,
            "strategy_vs_funnel": counts_status if not conflicts else "blocked",
        },
        "report_cross_section_consistency": {
            "counts": counts_status,
            "categories": categories_status,
            "actions": action_status,
            "executed_vs_pending": "passed" if not any("executed and pending" in item for item in conflicts) else "blocked",
            "version": "passed" if version_ok else "blocked",
        },
        "blocked_reasons": blocked_reasons,
    }


def build_may_data_strategy_report_full_integrity_check(
    client=None,
    trade_date=None,
    limit=20,
    report_generator=None,
    report_messages=None,
    source_check=None,
):
    if source_check is None:
        source_check = build_market_theme_production_trend_consumption_check(
            client=client,
            trade_date=trade_date,
            limit=limit,
        )
    source_table_status = source_check["table_status"]["market_theme_confirmed_evidence"]
    source_passed = source_check["fresh_runner_rebuild"] == "passed"
    blocked_reasons = list(source_check.get("blocked_reasons") or [])
    diagnostics = []

    generated_messages = _extract_messages_from_report(report_messages)
    if not generated_messages and report_generator is not None:
        stdout_buffer = io.StringIO()
        try:
            with redirect_stdout(stdout_buffer):
                generated_messages = _extract_messages_from_report(report_generator())
        except Exception as exc:
            blocked_reasons.append(f"dry-run report generation failed: {exc}")
        report_stdout = stdout_buffer.getvalue().strip()
        if report_stdout:
            diagnostics.append({
                "type": "dry_run_stdout",
                "message": report_stdout,
            })
            first_line = report_stdout.splitlines()[0]
            blocked_reasons.append(f"dry-run report generator wrote stdout warning: {first_line}")

    report_integrity = analyze_report_cross_section_integrity(generated_messages)
    blocked_reasons.extend(report_integrity["blocked_reasons"])

    return {
        "mode": "may-data-strategy-report-full-integrity-check",
        "schema_change": False,
        "data_write": False,
        "live_telegram": False,
        "telegram_header_version": VERSION,
        "source_integrity": {
            "production_db_readonly": "passed" if source_passed else _integrity_status_from_source_status(source_table_status),
            "may_data_available": "passed" if source_passed else _integrity_status_from_source_status(source_table_status),
            "market_theme_source_of_truth": (
                "production.market_theme_confirmed_evidence"
                if source_passed
                else "blocked"
            ),
            "uses_fake_or_local_as_market_theme_evidence": False,
            "uses_daily_signal_snapshot_as_market_theme_evidence": False,
        },
        "fresh_runner_dry_run": {
            "local_context_cleared": True,
            "report_generated": "passed" if generated_messages else "blocked",
            "live_telegram_disabled": True,
        },
        "decision_display_consistency": report_integrity["decision_display_consistency"],
        "report_cross_section_consistency": report_integrity["report_cross_section_consistency"],
        "blocked_reasons": blocked_reasons,
        "diagnostics": diagnostics,
        "followups": [],
    }


def market_execution_bridge_lines(holding_items, watch_items, market_mode, market_summary=None):

    funnel = build_unheld_funnel(watch_items, market_mode=market_mode)
    pending_count = len(pending_trade_items(holding_items, watch_items, market_mode=market_mode))
    tracking_count = unheld_tracking_count(funnel)

    if pending_count:
        return []

    if market_mode == "轉弱":
        mainline = "主線：盤勢轉弱，題材先降速觀察。"
    elif market_mode == "進攻偏熱":
        mainline = "主線：市場偏多但買點未成立。"
    else:
        mainline = "主線：題材仍可追蹤，不等於今日可買。"

    if funnel["等回測"]:
        execution = "執行：新增買點未成立，先等回測，不追高。"
    elif tracking_count:
        execution = "執行：新增買點未成立，等觸發，不追高。"
    else:
        execution = "執行：新增買點未成立，不追高。"

    return [
        f"🧭 {mainline}",
        f"🧭 {execution}",
        "🧭 新倉：無有效進場。",
    ]


def format_strong_prepare_summary(watch_items, market_mode, limit=3):

    if market_mode != "進攻偏熱":
        return []

    items = []
    for index, (name, data) in enumerate(watch_items):
        if unheld_funnel_state(name, data, market_mode=market_mode) != "可準備":
            continue
        label, action = strong_prepare_bucket(data)
        if label and action:
            items.append((unheld_execution_priority(index, name, data, market_mode=market_mode), label, name, action))

    if not items:
        return []

    items.sort(key=lambda item: item[0])
    lines = ["強勢準備："]
    for _priority, label, name, action in items[:limit]:
        lines.append(f"- {label}：{name} {action}")

    if len(items) > limit:
        hidden_items = items[limit:]
        hidden_labels = [label for _priority, label, _name, _action in hidden_items]
        if len(set(hidden_labels)) == 1:
            lines.append(f"- 另 {len(hidden_items)} 檔同狀態見詳情")
        else:
            label_counts = []
            for label in ["漲停鎖價", "過熱降溫", "突破回測"]:
                count = hidden_labels.count(label)
                if count:
                    label_counts.append(f"{label} {count}")
            lines.append(f"- 另 {len(hidden_items)} 檔：" + "、".join(label_counts) + "，見詳情")

    return lines


def format_cross_day_tracking_summary(watch_items, limit=3):

    items = []
    for index, (name, data) in enumerate(watch_items):
        if not cross_day_ready(data):
            continue
        if unheld_funnel_state(name, data, market_mode=None) == "可買":
            continue
        label = cross_day_repair_label(data)
        if not label:
            continue
        items.append((unheld_execution_priority(index, name, data), name, label))

    if not items:
        return []

    items.sort(key=lambda item: item[0])
    lines = ["追蹤最強："]
    for _priority, name, label in items[:limit]:
        lines.append(f"- {name} {label}，不可買，待觸發")
    if len(items) > limit:
        lines.append(f"- 另 {len(items) - limit} 檔見詳情")
    return lines


def formatTelegramSummary(results_map, best, score, market_summary, now, position_warning=None, daily_write_warning=None, strategy_evidence_summary=None, report_phase=None, report_context=None):

    if report_phase is None:
        report_phase = get_market_phase()
    if report_context is None:
        report_context = build_report_context(
            results_map,
            market_summary,
            now,
            strategy_evidence_summary=strategy_evidence_summary,
            report_phase=report_phase,
            position_warning=position_warning,
        )

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
        f"【{now.strftime('%m/%d')} {report_phase}｜{VERSION}】",
        f"報告日：{report_context['report_context'].get('as_of_date')}｜資料交易日：{report_context['report_context'].get('trade_date')}",
        f"Source：{report_context.get('source_status_text')}",
    ]

    if position_warning:
        lines.append(f"⚠ {position_warning}，持倉狀態不可信")

    if daily_write_warning:
        lines.append(f"⚠ {daily_write_warning}")

    holding_names = "、".join(name for name, _data in holding_items) or "無"
    lines.extend([
        f"📊 市場：{market_mode}｜{risk_level}",
    ])

    if report_phase == "盤中":
        lines.append(source_summary_text(results_map))

    lines.extend([
        f"🧭 今日結論：{today_conclusion_text(holding_items, watch_items, market_mode, risk_level, report_phase=report_phase, report_context=report_context)}",
        f"🧭 原因：{today_reason_text(watch_items, market_mode, report_phase=report_phase, report_context=report_context)}",
    ])

    if report_context.get("source_status_summary", {}).get("funnel") not in {"derived", "available"}:
        lines.append("🧭 新倉：無有效進場。")

    lines.extend([
        *market_execution_bridge_lines(holding_items, watch_items, market_mode, market_summary),
        *format_cross_day_tracking_summary(watch_items),
        *format_strong_prepare_summary(watch_items, market_mode),
        *format_market_theme_summary_lines(
            report_context.get("market_theme_evidence") or market_theme_summary_evidence(results_map, market_summary)
        ),
        f"🔥 最強：{best_stock_text(results_map, best, score, report_context=report_context)}",
        f"🚨 風險：{compact_risk_text(results_map)}",
        f"📌 持倉：{holding_names}",
    ])

    if report_phase == "盤中":
        lines.extend(["", "✅ 今日盤中交易執行"])
        lines.extend(format_execution_checklist(
            holding_items, watch_items, report_phase=report_phase, market_mode=market_mode, report_context=report_context
        ))
    else:
        lines.extend(["", "今日交易"])
        lines.append("新增交易建議：無")

    executed_lines = format_executed_checklist(holding_items, watch_items)
    if executed_lines:
        lines.extend(["", "已執行（不重複下單）"])
        lines.extend(executed_lines)

    lines.extend(["", "持倉風控檢查"])
    lines.extend(format_holding_control_checklist(holding_items, report_phase=report_phase))

    if report_phase != "盤中":
        plan_count = len(pending_trade_items(
            holding_items, watch_items, market_mode=market_mode, report_context=report_context
        ))
        if plan_count:
            lines.extend(["", f"明日計畫 {plan_count}"])
            lines.extend(format_execution_checklist(
                holding_items, watch_items, report_phase=report_phase, market_mode=market_mode, report_context=report_context
            ))

    lines.extend(["", "未持倉漏斗（非執行）："])
    lines.append(format_unheld_funnel(watch_items, market_mode=market_mode, report_context=report_context))

    lines.extend(["", detail_index_text(
        holding_items, watch_items, report_phase=report_phase, market_mode=market_mode, report_context=report_context
    )])

    rejected_line = rejected_trace_line(watch_items, market_mode=market_mode, report_context=report_context)
    if rejected_line:
        lines.append(rejected_line)

    if strategy_evidence_summary:
        lines.extend(["", strategy_evidence_summary])

    return "\n".join(lines)


def formatTelegramPositionCard(name, data, report_context=None):

    holding = data["holding"]
    decision = ensure_holding_decision(name, data)
    result = data["result"]
    today_text = holding_today_trade_text(data, decision) or "無"
    dist = card_breakout_distance(data)
    decision_line, condition_line = holding_detail_decision_lines(name, data)
    reason_line = holding_reason_line(name, data)
    next_step = holding_next_step_line(name, data)
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
        f"下一步：{next_step}",
        _source_status_line(report_context, name, holding=True) if report_context else None,
        f"數據：RR {rr_text}｜S {data.get('structure_score', '-')}/5｜V {data.get('volume_ratio', '-')}x",
        compact_backtest_line(data.get("backtest_context")),
        price_change_line(data.get("price"), data.get("change")),
    ]
    lines = [line for line in lines if line is not None]

    if reason_line:
        lines.insert(6, f"原因：{reason_line}")
    history_line = cross_day_detail_line(data)
    if history_line:
        lines.insert(-1, history_line)

    return "\n".join(lines)


def holding_reason_line(name, data):

    decision = ensure_holding_decision(name, data)
    level = decision.get("level") if decision else ""

    second_profit_state = second_take_profit_execution_state(data, decision).get("status")
    if second_profit_state == "completed":
        if second_take_profit_execution_state(data, decision).get("source") == "cross_day_position_events":
            return "production execution memory 顯示第二段已執行，避免重複賣出"
        return "今日第二段停利已執行，避免重複賣出"

    if second_profit_state == "partial":
        return "同日已賣後再次觸發停利，需標明第二段與股數"

    if second_profit_state == "blocked":
        return "execution memory 不足，fail closed 不輸出停利股數"

    if level in ["TAKE_PROFIT_25", "TAKE_PROFIT_50"]:
        if cross_day_duplicate_action(data, decision) == "take_profit":
            return "歷史停利已執行，避免同級重複"
        return "高浮盈且過熱延伸，先保留獲利"

    if level in ["REDUCE_25", "REDUCE_50"]:
        if cross_day_duplicate_action(data, decision) == "reduce":
            return "歷史減碼已執行，避免同級重複"
        if str(decision.get("action", "")).startswith("硬風控"):
            return decision.get("note") or "硬風控覆蓋，今日事件後仍需降風險"
        if str(decision.get("action", "")).startswith("增量"):
            return decision.get("note") or "補足今日未完成的風控差額"
        return "突破失敗或結構轉弱，先降低風險"

    if level == "STOP_100":
        return "跌破停損線，避免虧損擴大"

    if level in ["POST_REDUCE_WATCH", "NEW_POSITION_RISK_WATCH", "POST_PROFIT_WATCH"]:
        return decision.get("note")

    return None


def holding_next_step_line(name, data):

    decision = ensure_holding_decision(name, data)
    action = position_summary_action(name, data)
    level = decision.get("level") if decision else ""

    if level == "STOP_100":
        return "清出後不急回補，等重新出現買點"

    if action == "第二段停利後觀察":
        return "第二段已執行，剩餘部位回到風控觀察"

    if action == "第二段停利剩餘建議":
        return "只執行扣除今日已賣後的剩餘建議股數"

    if action == "第二段停利":
        return "執行本次建議後，剩餘部位回到風控觀察"

    if action == "停利記憶不足":
        return "先補 production execution memory，再評估是否有新停利條件"

    if level in ["REDUCE_25", "REDUCE_50"]:
        if cross_day_duplicate_action(data, decision) == "reduce":
            return "修復才恢復優先級，未修復續降級"
        return "若無法重新站回突破區，繼續降低優先級"

    if level == "POST_REDUCE_WATCH":
        return "修復才恢復優先級，未修復續降級"

    if level == "NEW_POSITION_RISK_WATCH":
        return "盤中先觀察，未修復再降級"

    if level in ["TAKE_PROFIT_25", "TAKE_PROFIT_50"]:
        if cross_day_duplicate_action(data, decision) == "take_profit":
            return "歷史停利已完成，等待新條件"
        return "保留核心倉，等待冷卻後再評估"

    if level == "POST_PROFIT_WATCH":
        return "等待新高、過熱升級或風控訊號"

    if action == "新倉風控觀察":
        return "盤中先觀察，未修復再降級"

    if level in ["ADD_10", "ADD_20", "ADD_30"]:
        return "加碼後守警戒價，量價未延續則停止加碼"

    if action == "洗盤警戒":
        return "守警戒價，跌破警戒升級風控"

    if action == "減碼後觀察":
        return "修復才恢復優先級，未修復續降級"

    if action == "洗盤續抱":
        return "守警戒價，等量價修復"

    if action == "續抱觀察":
        return "盤中先觀察，未修復再降級"

    if action == "風控觀察":
        return "跌破警戒升級風控"

    if action == "核心風控觀察":
        return "守警戒價，跌破警戒升級風控"

    if action == "停利後核心倉":
        return "保留核心倉，等待冷卻後再評估"

    if action == "停利後觀察":
        return "等待新高、過熱升級或風控訊號"

    if action == "核心續抱":
        return "保留核心倉，觀察是否轉弱"

    return "暫不加碼"


def holding_detail_decision_lines(name, data):

    decision = ensure_holding_decision(name, data)
    today_text = event_summary_text(data.get("position_events") or {})
    summary_action = position_summary_action(name, data)
    level = decision.get("level") if decision else ""
    action_text = decision.get("action") if decision else ""
    note = decision.get("note") if decision else ""

    if summary_action == "新倉風控觀察":
        return "新倉風控觀察，暫不加碼", "守警戒價，跌破停損或轉弱優先風控"

    if level == "ADD_30":
        return f"{action_text}，{note or '強勢突破確認'}", "RR足夠，品質達標"

    if level == "ADD_20":
        return f"{action_text}，{note or '趨勢延續'}", "RR足夠，品質達標"

    if level == "ADD_10":
        return f"{action_text}，{note or '小幅轉強'}", "RR達標，信心達標"

    if summary_action == "第二段停利後觀察":
        return (
            f"第二段停利後觀察，{second_take_profit_context_text(data, decision)}",
            "今日已執行，避免重複賣出"
        )

    if summary_action == "第二段停利剩餘建議":
        return (
            second_take_profit_context_text(data, decision),
            f"觸發條件：{note or '停利條件再次成立'}"
        )

    if summary_action == "第二段停利":
        return (
            f"第二段停利，{second_take_profit_context_text(data, decision)}",
            f"觸發條件：{note or '停利條件再次成立'}"
        )

    if summary_action == "停利記憶不足":
        return (
            "停利記憶不足，暫不輸出賣出股數",
            "production execution memory 缺失或矛盾，fail closed"
        )

    duplicate_action = cross_day_duplicate_action(data, decision)
    if duplicate_action == "take_profit":
        return "停利後觀察，暫不加碼", "歷史停利已完成，同級不重複"
    if duplicate_action == "reduce":
        return "減碼後觀察，暫不加碼", "歷史減碼已完成，同級不重複"

    if level in ["TAKE_PROFIT_25", "TAKE_PROFIT_50"]:
        return f"{action_text}，鎖定部分獲利", "高浮盈或過熱延伸，保留核心倉"

    if level in ["REDUCE_25", "REDUCE_50"]:
        if str(action_text).startswith("硬風控"):
            return f"{action_text}，{note or '今日事件後仍需降低風險'}", "硬風控覆蓋，高於今日交易事件"
        if str(action_text).startswith("增量"):
            return f"{action_text}，{note or '補足增量風控'}", "今日已減碼不足，新訊號要求補足風控"
        return f"{action_text}，降低風險", "結構轉弱或突破失敗，先降風險"

    if level == "STOP_100":
        return f"{action_text}，{note or '硬停損觸發'}", "停損優先，避免虧損擴大"

    if level == "POST_REDUCE_WATCH":
        return "減碼後觀察，暫不加碼", note or "今日已減碼接近原建議，等待新訊號"

    if level == "NEW_POSITION_RISK_WATCH":
        return "新倉風控觀察，暫不加碼", note or "今日剛買入，先觀察是否守住警戒 / 停損"

    if level == "POST_PROFIT_WATCH":
        return "停利後觀察，暫不加碼", note or "同級停利已完成，等待新條件"

    if summary_action == "核心續抱":
        return "核心續抱，暫不加碼", "跌破警戒價優先風控，等待冷卻"

    if summary_action == "洗盤續抱":
        return "洗盤續抱，暫不加碼", "跌破警戒價優先風控"

    if summary_action == "洗盤警戒":
        if is_new_position_loss(data):
            return "洗盤警戒，暫不加碼", "守警戒價，跌破停損或轉弱優先風控"
        return "洗盤警戒，暫不加碼", "若跌破停損或轉弱，優先風控"

    if summary_action == "風控觀察":
        return "風控觀察，暫不加碼", "跌破警戒價優先風控"

    if summary_action == "核心風控觀察":
        return "核心風控觀察，暫不加碼", "守警戒價，跌破警戒升級風控"

    if summary_action == "減碼後觀察":
        return "減碼後觀察，暫不加碼", "修復才恢復優先級，未修復續降級"

    if summary_action == "停利後核心倉":
        return "停利後核心倉，暫不加碼", "等待冷卻後再評估"

    if summary_action == "停利後觀察":
        return "停利後觀察，暫不加碼", "等待新高、過熱升級或風控訊號"

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
    sample = context.get("sample")
    win_rate = context.get("win_rate")

    if sample is None:
        return "回測：-"

    if sample < 10:
        return f"回測：不可用｜樣本不足（有效樣本{sample}）｜不納入判斷"
    elif sample < 30:
        confidence = "參考度中"
    else:
        confidence = "參考度高"

    if avg_return is None:
        verdict = "判讀不足"
    elif avg_return >= 1.0:
        verdict = "略優"
    elif avg_return > -0.5:
        verdict = "無明顯優勢"
    else:
        verdict = "偏弱"

    return (
        f"回測：樣本{sample}"
        f"｜{confidence}"
        f"｜3日勝率{win_rate}%"
        f"｜相對{relative}"
        f"｜{verdict}"
    )


def formatTelegramUnheldCard(name, data, report_phase=None, market_mode=None, report_context=None):

    result = data["result"]
    dist = card_breakout_distance(data)
    blockers = entry_blockers(result)
    source_status = _stock_decision_source_status(report_context, name)
    source_eligible = source_status == "available"
    valid_entry = is_valid_entry(result) and source_eligible
    title_label = "買點成立" if valid_entry else (blockers[0] if blockers else final_label(result))
    state = tomorrow_watch_state(name, data)
    funnel_state = unheld_funnel_state(name, data, market_mode=market_mode, report_context=report_context)
    prepare_label, prepare_action = strong_prepare_bucket(data)
    if is_valid_entry(result) and not source_eligible:
        title_label = "source missing" if source_status in {"missing-source", "insufficient-data"} else source_status
    elif state == "弱勢淘汰":
        title_label = rejected_primary_reason(result)
    elif funnel_state == "可準備" and prepare_label:
        title_label = prepare_label

    if valid_entry:
        title_icon = "🟢"
        if report_phase not in (None, "盤中"):
            title_action = f"明日追蹤｜{unheld_entry_size_detail_text(result)}"
        else:
            title_action = f"可買｜{unheld_entry_size_detail_text(result)}"
    elif is_valid_entry(result) and not source_eligible:
        title_icon = "⛔"
        title_action = "不可行動"
    elif funnel_state == "可準備":
        title_icon = "👀"
        title_action = "可準備"
    elif state in ["等冷卻", "等回測"]:
        title_icon = "⏳"
        title_action = state
    elif state in ["等RR修復", "等量能", "隔日確認"]:
        title_icon = "👀"
        title_action = state
    elif state == "弱勢淘汰":
        title_icon = "⛔"
        title_action = "淘汰"
    else:
        title_icon = "⛔"
        title_action = "不買"

    rr_text = rr_display_text(result, holding=False)
    risk_label = unheld_buy_risk_label(result, title_label)
    wait_text = unheld_entry_wait_text(result, state, funnel_state)
    detail_size_text = unheld_entry_size_detail_text(result)
    raw_size_text = entry_size_text(result)
    if is_valid_entry(result) and not source_eligible:
        buy_line = f"買點：不可買，source {source_status}"
        data_line = "數據：RR 不可用｜S 不可用｜V 不可用"
        price_line = "價格：不可用（source missing）"
    elif valid_entry and report_phase not in (None, "盤中"):
        buy_line = "買點：盤後追蹤｜開盤後確認｜不追價"
        data_line = f"數據：RR {rr_text}｜S {data.get('structure_score', '-')}/5｜V {data.get('volume_ratio', '-')}x"
        price_line = price_change_line(data.get("price"), data.get("change"))
    elif valid_entry and detail_size_text != raw_size_text:
        buy_line = f"買點：可買｜{detail_size_text}｜分批，不追價"
        data_line = f"數據：RR {rr_text}｜S {data.get('structure_score', '-')}/5｜V {data.get('volume_ratio', '-')}x"
        price_line = price_change_line(data.get("price"), data.get("change"))
    elif valid_entry:
        buy_line = f"買點：可買｜建議 {raw_size_text}｜{wait_text}"
        data_line = f"數據：RR {rr_text}｜S {data.get('structure_score', '-')}/5｜V {data.get('volume_ratio', '-')}x"
        price_line = price_change_line(data.get("price"), data.get("change"))
    elif funnel_state == "可準備" and prepare_action:
        buy_line = f"買點：{prepare_action}"
        data_line = f"數據：RR {rr_text}｜S {data.get('structure_score', '-')}/5｜V {data.get('volume_ratio', '-')}x"
        price_line = price_change_line(data.get("price"), data.get("change"))
    elif funnel_state == "等回測":
        buy_line = "買點：不買，等回測"
        data_line = f"數據：RR {rr_text}｜S {data.get('structure_score', '-')}/5｜V {data.get('volume_ratio', '-')}x"
        price_line = price_change_line(data.get("price"), data.get("change"))
    elif funnel_state == "淘汰":
        buy_line = f"買點：不可買，{wait_text}"
        data_line = f"數據：RR {rr_text}｜S {data.get('structure_score', '-')}/5｜V {data.get('volume_ratio', '-')}x"
        price_line = price_change_line(data.get("price"), data.get("change"))
    else:
        buy_line = f"買點：不買，{wait_text}"
        data_line = f"數據：RR {rr_text}｜S {data.get('structure_score', '-')}/5｜V {data.get('volume_ratio', '-')}x"
        price_line = price_change_line(data.get("price"), data.get("change"))
    trigger_label = "盤中觸發" if report_phase == "盤中" else "明日觸發"
    tomorrow_line = f"{trigger_label}：{tomorrow_trigger_text(state, data)}"
    reason_line = (
        f"原因：price/OHLCV/RR source {source_status}，不作新倉決策"
        if is_valid_entry(result) and not source_eligible
        else rejected_transition_reason_line(result) if funnel_state == "淘汰" else None
    )
    lines = [
        f"【{stock_title(name, data)}】{title_icon} {title_action}｜{title_label}",
        f"盤面：{plain_label(compact_market_line(result, dist))}",
        buy_line,
    ]

    if reason_line:
        lines.append(reason_line)

    lines.extend([
        tomorrow_line,
        _source_status_line(report_context, name, holding=False) if report_context else None,
        data_line,
        compact_backtest_line(data.get("backtest_context")),
        price_line,
    ])
    lines = [line for line in lines if line is not None]
    history_line = cross_day_detail_line(data)
    if history_line:
        lines.insert(-1, history_line)

    return "\n".join(lines)


def rejected_transition_reason_line(result):

    primary = rejected_primary_reason(result)
    blockers = entry_blockers(result)
    supplements = []

    if any(item.startswith("過熱") for item in blockers) or result.get("heat_state") in ["HOT", "EXTREME"]:
        supplements.append("追價風險 / 過熱")

    try:
        rr_unusable = result.get("rr") is not None and float(result.get("rr")) < 1
    except (TypeError, ValueError):
        rr_unusable = False

    if ("RR不足" in blockers or rr_unusable) and primary != "RR不可用":
        supplements.append("RR不可用")

    if "量能不足" in blockers and primary != "量能不足":
        supplements.append("量能不足")

    if "遠離觸發" in blockers and primary != "遠離觸發":
        supplements.append("遠離觸發")

    cause = "前次可買條件已失效"
    if primary == "突破失敗":
        cause += "：突破失敗或跌破進場條件"
    elif primary == "RR不可用":
        cause += "：RR不可用"
    elif primary == "弱反彈待確認":
        cause += "：結構未修復"
    elif primary:
        cause += f"：{primary}"

    industry_guard = "產業：未判斷產業多空"

    if supplements:
        return f"原因：{cause}｜補充：{'、'.join(supplements[:2])}，不作主因｜{industry_guard}"

    return f"原因：{cause}｜{industry_guard}"


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


def _natural_holding_evidence_line(holding_items, report_context):

    if not holding_items:
        return "持倉判斷依據：本輪沒有持倉標的；持倉側不輸出額外行動。"

    source_summary = (report_context.get("source_status_summary") or {}).get("position")
    if source_summary in {"missing-source", "source-error", "insufficient-data"}:
        return "持倉判斷依據：缺少可驗證的持久化交易紀錄，持倉狀態不升格為已確認倉位。"

    blocked_second_stage = []
    for name, data in holding_items:
        state = second_take_profit_execution_state(data, ensure_holding_decision(name, data))
        if state.get("is_second_stage") and state.get("status") != "completed":
            blocked_second_stage.append(name)

    if blocked_second_stage:
        names = "、".join(blocked_second_stage)
        return f"持倉判斷依據：已讀取持久化持倉紀錄；{names} 缺少可驗證的第二段停利執行紀錄，維持 fail-closed 風控。"

    return "持倉判斷依據：已讀取可驗證的持久化持倉紀錄，持倉處理以前兩則風控清單為準。"


def _natural_unheld_evidence_line(watch_items, report_context, market_mode=None):

    strategy = _field_by_key(report_context, "evidence.strategy_sample")
    strategy_status = strategy.get("source_status", "missing-source")

    if not watch_items:
        if strategy_status in {"missing-source", "source-error", "insufficient-data"}:
            return "未持倉判斷依據：今日策略樣本不足；本輪沒有候選可支持新倉結論。"
        return "未持倉判斷依據：今日沒有未持倉候選，未輸出新倉行動。"

    funnel = build_unheld_funnel(watch_items, market_mode=market_mode, report_context=report_context)
    actionable = len(funnel["可買"])
    blocked = [
        name for name, _data in watch_items
        if _stock_decision_source_status(report_context, name) != "available"
    ]

    if len(blocked) == len(watch_items):
        if strategy_status in {"missing-source", "source-error", "insufficient-data"}:
            return "未持倉判斷依據：今日策略樣本與候選來源不足，無法支持可行動新倉結論。"
        return "未持倉判斷依據：候選價格、日線或 RR 來源不足，無法支持可行動新倉結論。"

    if blocked:
        return f"未持倉判斷依據：候選清單中 {actionable} 檔具備可驗證來源；資料不足的標的維持追蹤或不可行動。"

    if strategy_status in {"missing-source", "source-error", "insufficient-data"}:
        return f"未持倉判斷依據：候選來源可讀，但今日策略樣本不足；可行動清單不因樣本缺口額外升級。"

    return f"未持倉判斷依據：候選清單來源可驗證；本輪可行動新倉 {actionable} 檔。"


def _natural_fail_closed_line(report_context, holding_items, watch_items):

    statuses = report_context.get("source_status_summary") or {}
    blocked_statuses = {"missing-source", "source-error", "insufficient-data"}
    blocked = []
    for key, label in [
        ("position", "持倉紀錄"),
        ("strategy_sample", "策略樣本"),
        ("funnel", "候選清單"),
    ]:
        status = statuses.get(key)
        if status in blocked_statuses:
            blocked.append(f"{label}（{status}）")

    if blocked:
        return f"資料不足處理：{'、'.join(blocked)}不足時採 fail-closed，不把缺證據項目輸出為行動建議。"

    if not holding_items and not watch_items:
        return "資料不足處理：本輪無持倉與候選，未產生行動建議。"

    return "資料不足處理：資料可讀項目以前兩則清單呈現；缺證據項目不升級為行動建議。"


def _natural_evidence_conclusion(holding_items, watch_items, report_context, market_mode=None):

    funnel = build_unheld_funnel(watch_items, market_mode=market_mode, report_context=report_context) if watch_items else {"可買": []}
    actionable = len(funnel["可買"])
    holding_blocked = []
    for name, data in holding_items:
        if position_summary_action(name, data) in {"停利記憶不足", "停利記憶待確認"}:
            holding_blocked.append(name)

    if actionable:
        new_position = f"新倉可行動候選 {actionable} 檔，以未持倉清單為準"
    else:
        new_position = "新倉無有效進場"

    if holding_blocked:
        holding_text = f"{'、'.join(holding_blocked)} 需先補足持倉執行紀錄"
    elif holding_items:
        holding_text = "持倉依風控清單處理"
    else:
        holding_text = "持倉無優先處理項"

    return f"結論：{new_position}；{holding_text}。資料不足的項目已關閉行動建議，避免把缺證據誤讀成推薦。"


def format_evidence_compact_message(results_map, report_context, holding_items, watch_items, market_mode=None):

    lines = [
        f"{VERSION} 簡短證據摘要",
        "",
        "本次證據摘要：",
        f"- {_natural_holding_evidence_line(holding_items, report_context)}",
        f"- {_natural_unheld_evidence_line(watch_items, report_context, market_mode=market_mode)}",
        f"- {_natural_fail_closed_line(report_context, holding_items, watch_items)}",
        "",
        _natural_evidence_conclusion(holding_items, watch_items, report_context, market_mode=market_mode),
    ]

    return "\n".join(lines)


def format_telegram_short_report_message(summary_message):

    noisy_prefixes = (
        "Source：核心價格",
        "證據日期：",
        "來源：",
        "趨勢：",
    )
    noisy_contains = (
        "latest_trade_date",
        "lookback_range",
        "source_of_truth",
        "db_table",
    )
    filtered = []
    skip_strategy_evidence = False
    for line in summary_message.splitlines():
        if line.startswith("📊 策略證據 v20.0"):
            skip_strategy_evidence = True
            continue
        if skip_strategy_evidence:
            if line == "":
                skip_strategy_evidence = False
            continue
        if any(line.startswith(prefix) for prefix in noisy_prefixes):
            continue
        if any(term in line for term in noisy_contains):
            continue
        filtered.append(line)

    while filtered and filtered[-1] == "":
        filtered.pop()

    return "\n".join(filtered)


def format_details_backup_messages(full_msg):

    if not full_msg:
        return []

    detail_text = (
        "【Details Backup】\n"
        "已壓縮 source/backtest/detail 長句；完整備查如下。\n\n"
        "【完整詳情備份】\n"
        f"{full_msg}"
    )
    return split_message(detail_text)


def formatTelegramMessages(results_map, full_msg, best, score, market_summary, now, position_warning=None, include_detail=False, daily_write_warning=None, strategy_evidence_summary=None, report_phase=None):

    ordered_items = ordered_result_items(results_map)
    if report_phase is None:
        report_phase = get_market_phase()
    watch_items_for_mode = [
        (name, data)
        for name, data in ordered_items
        if not data.get("holding")
    ]
    market_mode, _risk_level = derive_market_state(watch_items_for_mode)
    report_context = build_report_context(
        results_map,
        market_summary,
        now,
        strategy_evidence_summary=strategy_evidence_summary,
        report_phase=report_phase,
        position_warning=position_warning,
    )
    holding_items = sort_position_summary([
        (name, data)
        for name, data in ordered_items
        if data.get("holding")
    ])
    position_cards = [
        formatTelegramPositionCard(name, data, report_context=report_context)
        for name, data in holding_items
    ]
    unheld_cards = [
        formatTelegramUnheldCard(name, data, report_phase=report_phase, market_mode=market_mode, report_context=report_context)
        for _index, (name, data) in sort_watchlist_grouped([
            (name, data)
            for name, data in ordered_items
            if not data.get("holding")
        ])
    ]

    summary_message = formatTelegramSummary(
        results_map,
        best,
        score,
        market_summary,
        now,
        position_warning,
        daily_write_warning,
        strategy_evidence_summary,
        report_phase=report_phase,
        report_context=report_context
    )
    telegram_header = f"【{now.strftime('%m/%d')} {report_phase}｜{VERSION}】"
    holdings_message = (
        f"{telegram_header}\n"
        "【持倉標的】\n\n"
        + ("\n\n".join(position_cards) if position_cards else "無持倉")
    )
    unheld_message = (
        f"{telegram_header}\n"
        "【未持倉標的】\n\n"
        + ("\n\n".join(unheld_cards) if unheld_cards else "無")
    )
    evidence_message = format_evidence_compact_message(
        results_map,
        report_context,
        holding_items,
        [
            (name, data)
            for name, data in ordered_items
            if not data.get("holding")
        ],
        market_mode=market_mode,
    )
    short_report_message = format_telegram_short_report_message(summary_message)

    messages = []

    messages.append(holdings_message)
    messages.append(unheld_message)
    messages.append(f"{short_report_message}\n\n{evidence_message}")

    if include_detail:
        for chunk in format_details_backup_messages(full_msg):
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
def generate_report(dry_run=False):
    global holdings
    global position_events
    holdings = load_positions()
    position_events = load_today_position_events()

    now = datetime.now(tz)
    report_phase = get_market_phase()

    msg = (

        f"【{now.strftime('%m/%d')} "
        f"{report_phase}｜{VERSION}】\n"
    )

    msg += "====================\n\n"

    position_warning = get_position_store_warning()
    if position_warning:
        summary = "\n".join([
            f"【{now.strftime('%m/%d')} {report_phase}｜{VERSION}】",
            f"報告日：{now.date().isoformat()}｜資料交易日：unknown",
            "Source：核心價格 missing-source；持倉 missing-source；策略樣本 missing-source；market/theme missing-source",
            f"⚠ {position_warning}，持倉 / 今日交易狀態不可信",
            "今日結論",
            "新倉：無有效進場",
            "原因：missing-source",
            "持倉",
            "unavailable：持倉或今日交易來源缺失，不產生交易建議",
            "證據：production 來源不足，不作確認。",
            "詳情：runtime 觀察僅供診斷，非確認來源。",
        ])
        return [summary], None

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

    try:
        cross_day_contexts = build_cross_day_contexts(
            results_map,
            client=get_supabase_client(),
            today_position_events=position_events,
            now=now,
            version=VERSION,
        )
    except Exception:
        cross_day_contexts = build_cross_day_contexts(
            results_map,
            client=None,
            today_position_events=position_events,
            now=now,
        )

    for name, context in cross_day_contexts.items():
        if name in results_map:
            results_map[name]["cross_day_context"] = context

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
            now.date().isoformat(),
            data.get("position_events") or {},
            data["holding"].get("observation_days", data.get("observation_days", 0))
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

    strategy_evidence_summary = None

    if dry_run:
        daily_write_warning = None
        strategy_evidence_summary = None
    else:
        try:
            # 中文註釋：v19.1.3 只在收盤/盤後把每日穩定訊號寫入 Supabase，盤中不入庫。
            signal_result = record_daily_signals(
                VERSION,
                report_phase,
                msg,
                results_map,
                best,
                market_summary
            )
            # 中文註釋：v19.1.3 同步寫入 daily_price / daily_signal_snapshot，供 backfill 與每日樣本共用同一套口徑。
            snapshot_result = record_daily_snapshots(
                VERSION,
                report_phase,
                results_map
            )

            daily_write_warning = daily_write_warning_text(signal_result, snapshot_result)

            if daily_write_warning:
                msg += f"\n⚠ {daily_write_warning}"
        except Exception as e:
            daily_write_warning = None
            msg += f"\n⚠ DB記錄失敗：{str(e)}"

        try:
            # 中文註釋：v20.0 策略證據層只寫入研究資料與分類證據，不回寫或放寬任何交易決策。
            evidence_result = record_strategy_evidence(
                VERSION,
                report_phase,
                results_map,
                now
            )
            try:
                strategy_evidence_summary = load_strategy_evidence_summary(
                    get_supabase_client(),
                    VERSION
                )
            except Exception as summary_error:
                strategy_evidence_summary = format_strategy_evidence_summary(
                    error=summary_error
                )
        except Exception as e:
            strategy_evidence_summary = format_strategy_evidence_summary(
                error=e
            )

    messages = formatTelegramMessages(
        results_map,
        msg,
        best,
        score,
        market_summary,
        now,
        position_warning,
        daily_write_warning=daily_write_warning,
        strategy_evidence_summary=strategy_evidence_summary,
        report_phase=report_phase
    )

    return messages, execution_reply_markup(results_map)


def generate():
    result = generate_report()[0]
    if isinstance(result, list):
        return "\n\n====================\n\n".join(result)
    return result
