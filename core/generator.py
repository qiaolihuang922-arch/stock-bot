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
# 🔥 人話模組
# ================================
def explain_buy(result):
    reasons = []

    if result.get("decision_type") == "breakout":
        reasons.append("突破壓力區")

    if result.get("decision_type") == "pullback":
        reasons.append("回踩支撐轉強")

    if result.get("trend") == "UP":
        reasons.append("多頭趨勢")

    if result.get("volume_state") == "STRONG":
        reasons.append("量能放大")

    return "、".join(reasons[:2])


def explain_wait(conditions, stage):
    if stage == "BREAKOUT_READY":
        return "接近突破，等觸發"

    if not conditions["event"]:
        return "等待進場訊號"

    if not conditions["edge"]:
        return "型態還沒完成"

    if not conditions["risk"] or not conditions["rr"]:
        return "風報比不夠"

    return "條件尚未成熟"


# ================================
# 🔥 加碼
# ================================
def detect_add_position(result, price, ma5):

    trend = result.get("trend")
    volume = result.get("volume_state")

    if (
        trend == "UP" and
        volume == "STRONG" and
        ma5 and abs(price - ma5) / ma5 < 0.02
    ):
        return "📈 可考慮加碼（順勢）"

    return None


# ================================
# 🔥 統一決策（修正版）
# ================================
def build_action(result, price, ma5):

    decision = result.get("decision")
    trend = result.get("trend")
    volume = result.get("volume_state")
    position = result.get("position")
    buy = result.get("buy")

    # ❗️NO_TRADE 防呆
    if decision == "NO_TRADE":
        return "⚪ 觀望", "0%", "條件不成立"

    # 🟢 BUY
    if decision == "BUY":
        return "🟢 買進", f"{round(position*100)}%", explain_buy(result)

    # 🔴 強制出場
    if trend == "DOWN":
        return "🔴 賣出", "100%", "趨勢轉弱"

    if volume == "DISTRIBUTION":
        return "🔴 賣出", "100%", "主力出貨"

    # 🟡 停利（用價格，不用RR）
    if buy and price >= buy * 1.05:
        return "🟡 減碼", "30%", "已獲利5%"

    # 🟡 轉弱
    if ma5 and price < ma5 and trend != "UP":
        return "🟡 減碼", "50%", "跌破MA5"

    return "⚪ 觀望", "0%", None


# ================================
# 🔥 原邏輯（完全保留）
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


def score_to_text(conditions, result):
    decision = result.get("decision")

    if decision == "NO_TRADE":
        return "❌ 不成立（別碰）"

    if decision == "BUY":
        return "🟢 可進場"

    if conditions["event"] or conditions["edge"]:
        return "🟡 準備中（接近機會）"

    return "👀 觀察中"


def stage_detection(price, closes):
    closes = safe_list(closes)

    try:
        resistance = max(closes[-20:-3])
    except:
        return "FAR"

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
        "FAR": "⏳ 尚未接近壓力"
    }.get(stage)


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


def build_signals(result, conditions, decision, decision_type):
    main, sub, detail = [], [], []

    if decision == "NO_TRADE":
        for k in ["market", "trend", "volume"]:
            if not conditions.get(k):
                main.append(translate_condition(k))
        return main[:2], [], []

    for k in ["event", "edge", "risk", "rr"]:
        if not conditions.get(k):
            main.append(translate_condition(k))

    for k in ["volume", "trend", "market"]:
        if not conditions.get(k):
            sub.append(translate_condition(k))

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

    if result.get("trend") == "DOWN":
        detail.append("趨勢偏弱")
    elif result.get("trend") == "UP":
        detail.append("多頭結構")

    return list(dict.fromkeys(main)), list(dict.fromkeys(sub)), list(dict.fromkeys(detail))


# ================================
# 🔥 主流程（最終完整版）
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

        msg += f"【{name}】{score_to_text(conditions, result)}\n"

        if result.get("market_grade"):
            msg += f"🌍 市場：{result.get('market_grade')}\n"

        stage_text = stage_to_text(stage)
        if stage_text:
            msg += f"{stage_text}\n"

        # 🔥 統一決策
        action, size, reason = build_action(result, price, ma5)

        msg += f"👉 {action}（{size}）\n"

        if decision == "BUY":

            add = detect_add_position(result, price, ma5)
            if add:
                msg += f"{add}\n"

            msg += f"💡 {explain_buy(result)}\n"

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

            if reason:
                msg += f"💡 {reason}\n"
            else:
                msg += f"💡 {explain_wait(conditions, stage)}\n"

            main, sub, detail = build_signals(
                result, conditions, decision, decision_type
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