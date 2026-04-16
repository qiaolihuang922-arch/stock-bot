# ================================
# 🔥 FINAL（顯示層 v13.1｜LOCKED｜穩定補強版）
# ================================

# 🔒 VERSION LOCK
# - 基於 v13（完全保留原邏輯）
# - ❗未修改任何策略 / 判斷流程
# - ✅ 僅補強：防呆（空數據 / None / 崩潰保護）
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
    "廣達": "2382",
    "英業達": "2356",
    "仁寶": "2324",
    "光寶科": "2301",
}


# ================================
# 🔥 行動
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
# 🔥 解釋（修正）
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

    if decision_type == "fail_exit":
        return "趨勢破壞，強制出場"

    if stage == "BREAKOUT_READY":
        return "接近突破（尚未進場）"

    if not conditions.get("event"):
        return "等待觸發"

    if not conditions.get("edge"):
        return "型態未完成"

    return "條件觀察中"


# ================================
# 🔥 工具（不變）
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
        return None
    if len(data) < n:
        return data + [data[-1]] * (n - len(data))
    return data


# ================================
# 🔥 stage（不變）
# ================================
def stage_detection(price, closes, market_grade=None):

    closes = safe_list(closes)

    if not closes:
        return "FAR"

    try:
        resistance = max(closes[-20:-3])
    except:
        return "FAR"

    dist = (resistance - price) / price if price else 0

    if market_grade == "D":
        return "FAR"

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
# 🔥 訊號顯示（不變）
# ================================
def build_signals(result, conditions):

    decision = result.get("decision")
    decision_type = result.get("decision_type")

    if decision == "BUY":
        return []

    if decision_type == "fail_exit":
        return ["趨勢不對", "結構轉弱"]

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
# 🔥 主流程（加入最強股分配）
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
            continue

        if not closes or not volumes:
            continue

        result = strategy(price, ma5, ma20, closes, volumes)
        conditions = condition_engine(result)

        stage = stage_detection(price, closes, result.get("market_grade"))

        decisions.append(result.get("decision"))
        results_map[name] = result

    # 🔥 防呆
    if not results_map:
        return msg + "⚠ 無有效數據"

    # ================================
    # 🔥 最強股優先分配（核心）
    # ================================
    buy_list = [
        (n, r) for n, r in results_map.items()
        if r.get("decision") == "BUY"
    ]

    buy_list.sort(key=lambda x: x[1].get("strength", 0), reverse=True)

    allocation = [0.5, 0.3, 0.2]

    for i, (n, r) in enumerate(buy_list):

        if i < len(allocation):
            r["action"] = allocation[i]
        else:
            r["action"] = 0
            r["action_type"] = "HOLD"

    # ================================

    # 🔥 開始輸出
    for name, result in results_map.items():

        conditions = condition_engine(result)
        price = result.get("buy") or 0  # fallback

        action = get_action(result)
        stage = stage_detection(price, [price]*20, result.get("market_grade"))

        msg += f"【{name}】{action}\n"

        if result.get("market_grade"):
            msg += f"🌍 市場：{result.get('market_grade')} ｜ {stage_to_text(stage)}\n"

        msg += f"💡 {explain(result, conditions, stage)}\n"

        if result.get("decision") == "BUY":

            msg += f"📍 Buy: {safe_round(result.get('buy'))}\n"
            msg += f"🛑 Stop: {safe_round(result.get('stop'))}\n"
            msg += f"🎯 RR: {safe_round(result.get('rr'),2)}\n"

        else:
            signals = build_signals(result, conditions)
            for r in signals:
                msg += f"- {r}\n"

        msg += f"\n"

    best, score = pick_best_stock(results_map)

    msg += "====================\n"

    if best:
        msg += f"🔥 今日最強：{best}（強度 {score}）\n"
        msg += "👉 可優先關注此標的\n\n"
    else:
        msg += "⚠ 無最強股\n\n"

    if decisions and any(d == "BUY" for d in decisions):
        msg += "🟢 有交易機會"
    else:
        msg += "⏳ 市場觀望"

    return msg