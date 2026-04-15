# ================================
# 🔥 FINAL（顯示層 v11｜LOCKED｜完全對齊 v12 strategy）
# ================================

# 🔒 VERSION LOCK
# - 基於 v10 顯示層
# - 對齊 strategy v12（fail_exit 修正 + fake_break）
# - ❗禁止刪減 / 重構 / 簡化
# ================================

from datetime import datetime
import pytz

from services.stock_api import get_twse, get_yahoo, get_realtime_price
from services.analysis import strategy, pick_best_stock
from core.condition_engine import condition_engine

tz = pytz.timezone("Asia/Taipei")

stocks = {
    "緯創": "3231",
    "建準": "2421",
    "智原": "3035",
    "聯電": "2303",
    "群創": "3481",
    "華邦電": "2344",
    "技嘉": "2376",

    # 🔥 新增
    "廣達": "2382",
    "英業達": "2356",
    "仁寶": "2324",
    "光寶科": "2301",
}


# ================================
# 🔥 行動（保留）
# ================================
def get_action(result):

    action = result.get("action", 0)
    action_type = result.get("action_type")

    if action_type == "SELL_ALL":
        return "🔴 賣出 100%"

    if action_type == "BUY":
        return f"🟢 買進 {round(action*100)}%"

    return "⏳ 不動"


# ================================
# 🔥 解釋（🔥升級：精準語意）
# ================================
def explain(result, conditions, stage):

    decision = result.get("decision")
    decision_type = result.get("decision_type")

    if decision == "BUY":

        if decision_type == "breakout":
            return "突破壓力"
        elif decision_type == "pullback":
            return "回踩轉強"
        elif decision_type == "early":
            return "提前卡位"
        elif decision_type == "pre_breakout":
            return "突破前試單"
        elif decision_type == "add_on":
            return "突破確認，加碼"

        return "訊號成立"

    # 🔥 fail_exit（升級語意）
    if decision_type == "fail_exit":
        return "趨勢破壞，強制出場"

    # ================================
    # 🔥 原邏輯（保留）
    # ================================
    if stage == "BREAKOUT_READY":
        return "接近突破，等觸發"

    if not conditions.get("event"):
        return "等待觸發"

    if not conditions.get("edge"):
        return "型態未完成"

    return "條件觀察中"


# ================================
# 🔥 工具（保留）
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


# ================================
# 🔥 訊號顯示（🔥微優化）
# ================================
def build_signals(result, conditions):

    decision = result.get("decision")
    decision_type = result.get("decision_type")

    # 🔥 BUY 不顯示負面
    if decision == "BUY":
        return []

    # 🔥 fail_exit → 顯示核心原因（避免誤導）
    if decision_type == "fail_exit":
        return ["趨勢不對", "結構轉弱"]

    # 🔴 NO_TRADE
    if decision == "NO_TRADE":
        keys = ["market", "trend", "volume"]
    else:
        keys = ["event", "edge", "volume"]

    mapping = {
        "event": "尚未觸發",
        "edge": "型態未完成",
        "volume": "量能不足",
        "trend": "趨勢不對",
        "market": "市場不佳"
    }

    msgs = []

    for k in keys:
        if not conditions.get(k):
            msgs.append(mapping.get(k, k))

    return msgs[:3]


# ================================
# 🔥 主流程（穩定版）
# ================================
def generate():

    now = datetime.now(tz)
    phase = get_market_phase()

    msg = f"【{now.strftime('%m/%d')} {phase}】\n\n"

    decisions = []
    results_map = {}

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
        results_map[name] = result

        action = get_action(result)

        msg += f"【{name}】{action}\n"

        if result.get("market_grade"):
            msg += f"🌍 市場：{result.get('market_grade')} ｜ {stage_to_text(stage)}\n"

        msg += f"💡 {explain(result, conditions, stage)}\n"

        # ================================
        # 🔥 BUY 顯示
        # ================================
        if result.get("decision") == "BUY":

            msg += f"📍 Buy: {safe_round(result.get('buy'))}\n"
            msg += f"🛑 Stop: {safe_round(result.get('stop'))}\n"
            msg += f"🎯 RR: {safe_round(result.get('rr'),2)}\n"

        else:
            signals = build_signals(result, conditions)
            for r in signals:
                msg += f"- {r}\n"

        msg += f"💰 {safe_round(price)}（{safe_round(change,2)}%）\n\n"

    # ================================
    # 🔥 最強股
    # ================================
    best, score = pick_best_stock(results_map)

    msg += "====================\n"
    msg += f"🔥 今日最強：{best}（強度 {score}）\n\n"

    if any(d == "BUY" for d in decisions):
        msg += "🟢 有交易機會"
    else:
        msg += "⏳ 市場觀望"

    return msg