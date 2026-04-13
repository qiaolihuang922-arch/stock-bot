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
# 🔥 強度評分（權重版）
# ================================
def score_to_text(conditions):

    weights = {
        "event": 2,
        "edge": 2,
        "risk": 1.5,
        "rr": 1.5,
        "volume": 1,
        "trend": 1,
        "market": 1,
        "structure": 1
    }

    score = sum(weights[k] for k, v in conditions.items() if v)

    if score >= 8:
        return "🔥 很強（可準備）"
    elif score >= 6:
        return "👍 不錯（差一步）"
    elif score >= 4:
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
    return {
        "BREAKOUT_READY": "🔥 突破前（重點觀察）",
        "APPROACH": "👀 接近壓力（觀察）",
        "FAR": "⏳ 尚未接近壓力",
        "WEAK": "❌ 空方趨勢（避免）"
    }.get(stage)


# ================================
# 🔥 條件翻譯
# ================================
def translate_condition(k):
    return {
        "event": "尚未觸發",
        "edge": "型態不完整",
        "risk": "風控不合",
        "rr": "報酬不夠",
        "volume": "量能不足",
        "trend": "趨勢不對",
        "market": "市場不佳"
    }.get(k, k)


# ================================
# 🔥 訊號整理（主因 / 次因 / 細節）
# ================================
def build_signals(result, conditions, decision_type, price, ma5, ma20, closes):

    main = []
    sub = []
    detail = []

    # ===== 主因 =====
    for k in ["event", "edge", "risk", "rr"]:
        if not conditions[k]:
            main.append(translate_condition(k))

    # ===== 次因 =====
    for k in ["volume", "trend", "market"]:
        if not conditions[k]:
            sub.append(translate_condition(k))

    # ===== Edge細節 =====
    if decision_type == "breakout":
        if result.get("edge_consolidation") is False:
            detail.append("盤整不夠")
        if result.get("edge_fake_breakout") is True:
            detail.append("疑似假突破")

    elif decision_type == "pullback":
        if result.get("edge_first_pullback") is False:
            detail.append("非第一次回踩")
        if result.get("edge_ma20_trend") is False:
            detail.append("MA20未上升")

    # ===== 價格補充 =====
    resistance = max(closes[-20:-3])

    if price < ma20:
        detail.append("MA20下方（弱勢）")
    elif price > ma5 > ma20:
        detail.append("多頭排列")

    if ma5 and abs(price - ma5) / ma5 < 0.02:
        detail.append("貼近MA5")

    dist = (resistance - price) / price
    if dist < 0.02:
        detail.append("壓力貼近")
    elif dist < 0.05:
        detail.append("接近壓力")

    # ===== 去重 =====
    seen = set()
    final_detail = []
    for d in detail:
        if d not in seen:
            final_detail.append(d)
            seen.add(d)

    return main, sub, final_detail


# ================================
# 🔥 主流程（完整版）
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

        # ===== 交易數據 =====
        buy = result.get("buy")
        stop = result.get("stop")
        rr = result.get("rr")
        risk = result.get("risk")
        position = result.get("position")

        conditions = condition_engine(result)
        stage = stage_detection(price, closes)

        decisions.append(decision)

        # ===== 標題 =====
        msg += f"【{name}】{score_to_text(conditions)}\n"

        if result.get("market_grade"):
            msg += f"🌍 市場：{result.get('market_grade')}\n"

        stage_text = stage_to_text(stage)
        if stage_text:
            msg += f"{stage_text}\n"

        # =========================
        # 🔥 BUY
        # =========================
        if decision == "BUY":

            msg += "👉 🟢 可進場\n"
            msg += f"📍 Buy: {safe_round(buy)}\n"
            msg += f"🛑 Stop: {safe_round(stop)}\n"
            msg += f"🎯 RR: {safe_round(rr,2)}\n"

            if risk is not None:
                msg += f"⚠️ Risk: {round(risk*100,1)}%\n"

            if position is not None:
                msg += f"📊 倉位: {round(position*100)}%\n"

        # =========================
        # 🔥 非BUY
        # =========================
        else:

            msg += "👉 還不能做\n" if decision == "WAIT" else "👉 不要做\n"

            main, sub, detail = build_signals(
                result, conditions, decision_type,
                price, ma5, ma20, closes
            )

            for r in main[:2]:
                msg += f"- {r}\n"

            if len(main) < 2:
                for r in sub[:1]:
                    msg += f"- {r}\n"

            if detail:
                msg += f"（{' / '.join(detail[:2])}）\n"

        # ===== 價格 =====
        msg += f"💰 現價 {safe_round(price)}（{safe_round(change,2)}%）\n\n"

    msg += "====================\n"

    if any(d == "BUY" for d in decisions):
        msg += "🟢 今天有機會，可以挑著做\n"
    else:
        msg += "⏳ 今天沒好機會，先觀望\n"

    return msg