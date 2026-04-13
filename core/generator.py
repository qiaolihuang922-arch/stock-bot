# ================================
# 🔥 FINAL（顯示層 + 行動指令版）
# ================================

from datetime import datetime
import pytz

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
# 🔥 行動統一（🔥關鍵修正）
# ================================
def get_action(result, price, ma5):

    decision = result.get("decision")
    pos = result.get("position") or 0

    # ❌ 全出
    if decision == "NO_TRADE":
        return "🔴 賣出 100%"

    # 🟢 買（直接用倉位）
    if decision == "BUY":
        return f"🟢 買進 {round(pos*100)}%"

    # ===== WAIT =====

    if pos >= 0.4:
        return f"⚪ 持有（目標 {round(pos*100)}%）"

    if pos >= 0.2:
        return f"🟡 降至 {round(pos*100)}%"

    return "⏳ 空手觀望"


# ================================
# 🔥 人話（保留）
# ================================
def explain_buy(result):

    t = result.get("decision_type")

    if t == "breakout":
        return "突破壓力區"
    elif t == "pullback":
        return "回踩支撐轉強"
    elif t == "early":
        return "提前卡位"

    return "訊號成立"


def explain_wait(result, conditions, stage):

    if stage == "BREAKOUT_READY":
        return "接近突破，等觸發"

    if (result.get("position") or 0) >= 0.3:
        return "市場偏強，可留意"

    if not conditions.get("event"):
        return "等待觸發"

    if not conditions.get("edge"):
        return "型態未完成"

    return "條件觀察中"


# ================================
# 🔥 加碼提示（保留）
# ================================
def detect_add_position(result, price, ma5):

    if result.get("decision") != "BUY":
        return None

    if (
        result.get("trend") == "UP" and
        result.get("volume_state") == "STRONG" and
        ma5 and abs(price - ma5) / ma5 < 0.02
    ):
        return "📈 強勢延續，可考慮加碼"

    return None


# ================================
# 🔥 倉位顯示（保留但不主導）
# ================================
def build_action(result, conditions, stage):

    decision = result.get("decision")
    position = result.get("position") or 0

    if decision == "NO_TRADE":
        return "0%", "條件不成立"

    if decision == "BUY":
        return f"{round(position*100)}%", explain_buy(result)

    return f"{round(position*100)}%", explain_wait(result, conditions, stage)


# ================================
# 🔥 工具（全部保留）
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
    pos = result.get("position") or 0

    if decision == "NO_TRADE":
        return "❌ 不成立"

    if decision == "BUY":
        return "🟢 進場訊號"

    if pos >= 0.3:
        return "🟡 準備進場"

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
        "BREAKOUT_READY": "🔥 突破前",
        "APPROACH": "👀 接近壓力",
        "FAR": "⏳ 尚未接近"
    }.get(stage)


def translate_condition(k):
    return {
        "event": "尚未觸發",
        "edge": "型態未完成",
        "risk": "風控不合",
        "rr": "報酬不足",
        "volume": "量能不足",
        "trend": "趨勢不對",
        "market": "市場不佳"
    }.get(k, k)


def build_signals(result, conditions):

    msgs = []

    for k in ["event", "edge", "volume"]:
        if not conditions.get(k):
            msgs.append(translate_condition(k))

    return msgs[:3]


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
        conditions = condition_engine(result)
        stage = stage_detection(price, closes)

        decisions.append(result.get("decision"))

        # 🔥 行動（唯一主軸）
        action = get_action(result, price, ma5)

        msg += f"【{name}】{action}\n"

        if result.get("market_grade"):
            msg += f"🌍 市場：{result.get('market_grade')} ｜ {stage_to_text(stage)}\n"

        # 💡 理由
        _, reason = build_action(result, conditions, stage)
        msg += f"💡 {reason}\n"

        if result.get("decision") == "BUY":

            add = detect_add_position(result, price, ma5)
            if add:
                msg += f"{add}\n"

            msg += f"📍 Buy: {safe_round(result.get('buy'))}\n"
            msg += f"🛑 Stop: {safe_round(result.get('stop'))}\n"
            msg += f"🎯 RR: {safe_round(result.get('rr'),2)}\n"

        else:
            signals = build_signals(result, conditions)
            for r in signals:
                msg += f"- {r}\n"

        msg += f"💰 {safe_round(price)}（{safe_round(change,2)}%）\n\n"

    msg += "====================\n"

    if any(d == "BUY" for d in decisions):
        msg += "🟢 有交易機會"
    else:
        msg += "⏳ 市場觀望"

    return msg