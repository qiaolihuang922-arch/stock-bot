from datetime import datetime
import pytz

from services.learning import record_trade
from services.stock_api import get_twse, get_yahoo, get_realtime_price
from services.analysis import strategy
from core.condition_engine import condition_engine, summarize_conditions

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
# 🔥 工具
# ================================
def risk_to_text(risk):
    if risk >= 0.06:
        return "⚠️風險高"
    elif risk >= 0.03:
        return "⚠️風險中"
    return "✅風險低"


def score_to_text(score):
    if score >= 80:
        return "🔥 很強（可準備）"
    elif score >= 65:
        return "👍 不錯（差一步）"
    elif score >= 50:
        return "👌 普通（先觀察）"
    return "❌ 很弱（別碰）"


def safe_round(val, n=1):
    return round(val, n) if isinstance(val, (int, float)) else "-"


# ================================
# 🔥 🔥🔥 核心新增：階段判斷
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
# 🔥 價格細節
# ================================
def price_evidence(price, ma5, ma20, closes):

    evidence = []

    resistance = max(closes[-20:-3])
    support = min(closes[-20:])

    if price < ma20:
        if closes[-2] > ma20:
            evidence.append("跌破MA20（轉弱）")
        else:
            evidence.append("MA20下方（弱勢）")

    elif price > ma5 > ma20:
        evidence.append("多頭排列")

    if abs(price - ma5) / ma5 < 0.02:
        evidence.append("貼近MA5")

    dist = (resistance - price) / price

    if dist < 0.02:
        evidence.append("壓力貼近")
    elif dist < 0.05:
        evidence.append("接近壓力")

    return evidence


# ================================
# 🔥 動能 / 量能
# ================================
def momentum_explain(momentum):
    if momentum == "ACCELERATING":
        return "動能增強"
    elif momentum == "DECELERATING":
        return "動能轉弱"


def volume_explain(volume):
    if volume == "STRONG":
        return "量能放大"
    elif volume == "WEAK":
        return "量能不足"
    elif volume == "DISTRIBUTION":
        return "出貨量"


# ================================
# 🔥 Edge翻譯
# ================================
def explain_edge(result, decision_type):

    reasons = []

    if decision_type == "breakout":

        if result.get("event_breakout") is False:
            reasons.append("尚未突破")

        if result.get("edge_consolidation") is False:
            reasons.append("盤整不夠")

        if result.get("edge_not_high_zone") is False:
            reasons.append("位置太高")

        if result.get("edge_fake_breakout") is True:
            reasons.append("疑似假突破")

    elif decision_type == "pullback":

        if result.get("event_pullback") is False:
            reasons.append("還沒回踩")

        if result.get("edge_first_pullback") is False:
            reasons.append("非第一次回踩")

        if result.get("edge_ma20_trend") is False:
            reasons.append("MA20未上升")

        if result.get("edge_structure_hold") is False:
            reasons.append("結構未守")

    return reasons


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

        grade = result.get("market_grade")

        stage = stage_detection(price, closes)

        decisions.append(decision)

        msg += f"【{name}】{score_to_text(50)}\n"

        if grade:
            msg += f"🌍 市場：{grade}\n"

        stage_text = stage_to_text(stage)
        if stage_text:
            msg += f"{stage_text}\n"

        if decision != "BUY":

            msg += "👉 還不能做\n" if decision == "WAIT" else "👉 不要做\n"

            signals = []
            signals += explain_edge(result, decision_type)
            signals += price_evidence(price, ma5, ma20, closes)

            m = momentum_explain(result.get("momentum_state"))
            if m:
                signals.append(m)

            v = volume_explain(result.get("volume_state"))
            if v:
                signals.append(v)

            for r in signals[:3]:
                msg += f"- {r}\n"

        msg += f"💰 現價 {safe_round(price)}（{safe_round(change,2)}%）\n\n"

    msg += "====================\n"

    if any(d == "BUY" for d in decisions):
        msg += "🟢 今天有機會，可以挑著做\n"
    else:
        msg += "⏳ 今天沒好機會，先觀望\n"

    return msg