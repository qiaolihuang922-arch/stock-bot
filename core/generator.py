from datetime import datetime
import pytz

from services.learning import record_trade
from services.stock_api import get_twse, get_yahoo, get_realtime_price
from services.analysis import strategy
from core.condition_engine import condition_engine

tz = pytz.timezone("Asia/Taipei")

stocks = {
    "緯創": "3231",
    "建準": "2421",
    "智原": "3035",
    "聯電": "2303",
    "群創": "3481",
    "華邦電": "2344"
}


# ================================
# 🔥 時間系統
# ================================
def get_market_phase():
    now = datetime.now(tz)
    h, m = now.hour, now.minute

    if now.weekday() >= 5:
        return "假日"

    if h == 8 and 30 <= m < 40:
        return "盤前"
    elif 9 <= h < 13:
        return "盤中"
    elif h == 13 and m >= 20:
        return "收盤"

    return "盤後"


# ================================
# 🔥 強度評分（改 condition）
# ================================
def score_to_text(conditions):

    score = sum(conditions.values()) * 12.5

    if score >= 75:
        return "🔥 很強（可準備）"
    elif score >= 60:
        return "👍 不錯（差一步）"
    elif score >= 40:
        return "👌 普通（先觀察）"
    return "❌ 很弱（別碰）"


def safe_round(val, n=1):
    return round(val, n) if isinstance(val, (int, float)) else "-"


# ================================
# 🔥 階段判斷
# ================================
def stage_detection(price, closes):

    resistance = max(closes[-20:-3])
    dist = (resistance - price) / price

    if price < min(closes[-5:]):
        return "WEAK"

    if dist < 0.02:
        return "BREAKOUT_READY"
    elif dist < 0.05:
        return "APPROACH"
    else:
        return "FAR"


def stage_to_text(stage):

    mapping = {
        "BREAKOUT_READY": "🔥 突破前（重點觀察）",
        "APPROACH": "👀 接近壓力（觀察）",
        "FAR": "⏳ 尚未接近壓力",
        "WEAK": "❌ 空方趨勢（避免）"
    }

    return mapping.get(stage)


# ================================
# 🔥 訊號整理（核心優化）
# ================================
def build_signals(result, conditions, decision_type, price, ma5, ma20, closes):

    signals = []

    # ===== 1️⃣ 致命條件（最重要）=====
    if not conditions["event"]:
        signals.append("尚未觸發")

    if not conditions["edge"]:
        signals.append("型態不完整")

    if not conditions["volume"]:
        signals.append("量能不足")

    if not conditions["trend"]:
        signals.append("趨勢不對")

    if not conditions["market"]:
        signals.append("市場不佳")

    # ===== 2️⃣ Edge細節 =====
    if decision_type == "breakout":
        if result.get("edge_consolidation") is False:
            signals.append("盤整不夠")
        if result.get("edge_fake_breakout") is True:
            signals.append("疑似假突破")

    elif decision_type == "pullback":
        if result.get("edge_first_pullback") is False:
            signals.append("非第一次回踩")
        if result.get("edge_ma20_trend") is False:
            signals.append("MA20未上升")

    # ===== 3️⃣ 價格結構 =====
    resistance = max(closes[-20:-3])

    if price < ma20:
        signals.append("MA20下方（弱勢）")
    elif price > ma5 > ma20:
        signals.append("多頭排列")

    if abs(price - ma5) / ma5 < 0.02:
        signals.append("貼近MA5")

    dist = (resistance - price) / price
    if dist < 0.02:
        signals.append("壓力貼近")
    elif dist < 0.05:
        signals.append("接近壓力")

    # ===== 4️⃣ 動能 / 量能 =====
    momentum = result.get("momentum_state")
    volume = result.get("volume_state")

    if momentum == "ACCELERATING":
        signals.append("動能增強")
    elif momentum == "DECELERATING":
        signals.append("動能轉弱")

    if volume == "STRONG":
        signals.append("量能放大")
    elif volume == "DISTRIBUTION":
        signals.append("出貨量")

    # ===== 去重 =====
    seen = set()
    final = []
    for s in signals:
        if s not in seen:
            final.append(s)
            seen.add(s)

    return final


# ================================
# 🔥 主流程
# ================================
def generate():

    now = datetime.now(tz)
    phase = get_market_phase()

    msg = f"【{now.strftime('%m/%d')} {phase}】\n\n"

    decisions = []

    for name, code in stocks.items():

        twse = get_twse(code)
        yahoo = get_yahoo(code)

        if not twse and not yahoo:
            continue

        if twse:
            t_price, t_change, ma5, ma20, closes, volumes = twse
            realtime = get_realtime_price(code)

            if realtime:
                price, change = realtime
            elif yahoo:
                price, change = yahoo
            else:
                price, change = t_price, t_change
        else:
            price, change = yahoo
            closes = [price] * 20
            volumes = [1] * 20
            ma5 = price
            ma20 = price

        result = strategy(price, ma5, ma20, closes, volumes)

        decision = result.get("decision")
        decision_type = result.get("decision_type")

        if decision_type == "none":
            if result.get("event_breakout"):
                decision_type = "breakout"
            elif result.get("event_pullback"):
                decision_type = "pullback"

        conditions = condition_engine(result)

        grade = result.get("market_grade")
        stage = stage_detection(price, closes)

        decisions.append(decision)

        # ===== 標題 =====
        msg += f"【{name}】{score_to_text(conditions)}\n"

        if grade:
            msg += f"🌍 市場：{grade}\n"

        stage_text = stage_to_text(stage)
        if stage_text:
            msg += f"{stage_text}\n"

        # ===== 非BUY =====
        if decision != "BUY":

            msg += "👉 還不能做\n" if decision == "WAIT" else "👉 不要做\n"

            signals = build_signals(
                result, conditions, decision_type,
                price, ma5, ma20, closes
            )

            for r in signals[:3]:
                msg += f"- {r}\n"

        # ===== 價格 =====
        msg += f"💰 現價 {safe_round(price)}（{safe_round(change,2)}%）\n\n"

    msg += "====================\n"

    if any(d == "BUY" for d in decisions):
        msg += "🟢 今天有機會，可以挑著做\n"
    else:
        msg += "⏳ 今天沒好機會，先觀望\n"

    return msg