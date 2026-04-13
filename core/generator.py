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
    "華邦電": "2344",
    "技嘉": "2376"
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
def safe_round(val, n=1):
    try:
        return round(float(val), n)
    except:
        return "-"


def safe_list(data, n=20):
    if not data:
        return [0] * n
    if len(data) < n:
        return data + [data[-1]] * (n - len(data))
    return data


# ================================
# 🔥 ⭐ 評分系統（修正版）
# ================================
def score_to_text(conditions, result):

    # ❌ 只有市場真的弱才禁止
    if result.get("market_signal") == "WEAK":
        return "❌ 不成立（別碰）"

    # 🟢 完整成立
    if all([
        conditions["event"],
        conditions["edge"],
        conditions["risk"],
        conditions["rr"]
    ]):
        return "🟢 可進場"

    # 🟡 接近成立（最重要）
    if conditions["edge"] or conditions["event"]:
        return "🟡 準備中（接近機會）"

    # 👀 還在形成
    return "👀 觀察中"


# ================================
# 🔥 階段判斷
# ================================
def stage_detection(price, closes):

    closes = safe_list(closes)

    try:
        resistance = max(closes[-20:-3])
    except:
        return "FAR"

    if price < min(closes[-5:]):
        return "WEAK"

    dist = (resistance - price) / price if price else 0

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
# 🔥 訊號整理
# ================================
def build_signals(result, conditions, decision_type, price, ma5, ma20, closes):

    closes = safe_list(closes)

    main, sub, detail = [], [], []

    for k in ["event", "edge", "risk", "rr"]:
        if not conditions.get(k):
            main.append(translate_condition(k))

    for k in ["volume", "trend", "market"]:
        if not conditions.get(k):
            sub.append(translate_condition(k))

    # Edge細節
    if decision_type == "breakout":
        if result.get("edge_consolidation") is False:
            detail.append("盤整不夠")
        if result.get("edge_fake_breakout"):
            detail.append("疑似假突破")

    elif decision_type == "pullback":
        if result.get("edge_first_pullback") is False:
            detail.append("非第一次回踩")
        if result.get("edge_ma20_trend") is False:
            detail.append("MA20未上升")

    # 價格
    try:
        resistance = max(closes[-20:-3])
    except:
        resistance = price

    if price < ma20:
        detail.append("MA20下方（弱勢）")
    elif price > ma5 > ma20:
        detail.append("多頭排列")

    if ma5 and ma5 != 0 and abs(price - ma5) / ma5 < 0.02:
        detail.append("貼近MA5")

    dist = (resistance - price) / price if price else 0

    if dist < 0.02:
        detail.append("壓力貼近")
    elif dist < 0.05:
        detail.append("接近壓力")

    return list(dict.fromkeys(main)), list(dict.fromkeys(sub)), list(dict.fromkeys(detail))


# ================================
# 🔥 主流程（最終穩定版）
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

        buy = result.get("buy")
        stop = result.get("stop")
        rr = result.get("rr")
        risk = result.get("risk")
        position = result.get("position")

        conditions = condition_engine(result)
        stage = stage_detection(price, closes)

        decisions.append(decision)

        # ⭐ 修正這裡
        msg += f"【{name}】{score_to_text(conditions, result)}\n"

        if result.get("market_grade"):
            msg += f"🌍 市場：{result.get('market_grade')}\n"

        stage_text = stage_to_text(stage)
        if stage_text:
            msg += f"{stage_text}\n"

        if decision == "BUY":

            msg += "👉 🟢 可進場\n"
            msg += f"📍 Buy: {safe_round(buy)}\n"
            msg += f"🛑 Stop: {safe_round(stop)}\n"
            msg += f"🎯 RR: {safe_round(rr,2)}\n"

            if risk:
                msg += f"⚠️ Risk: {round(risk*100,1)}%\n"

            if position:
                msg += f"📊 倉位: {round(position*100)}%\n"

            record_trade(
                name=name,
                action=decision,
                price=price,
                buy=buy,
                stop=stop,
                ma5=ma5,
                ma20=ma20,
                volume=result.get("volume_state"),
                trend=result.get("trend"),
                extra_data=result
            )

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

        msg += f"💰 現價 {safe_round(price)}（{safe_round(change,2)}%）\n\n"

    msg += "====================\n"

    if any(d == "BUY" for d in decisions):
        msg += "🟢 今天有機會，可以挑著做\n"
    else:
        msg += "⏳ 今天沒好機會，先觀望\n"

    return msg