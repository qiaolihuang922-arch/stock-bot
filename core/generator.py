# ================================
# 🔥 FINAL（顯示層 v13.4｜v15.3完全對齊穩定版）
# ================================

# 🔒 VERSION LOCK（重要）
# - 基於 v13（保留原結構）
# - ❗不動 strategy / condition_engine
# - ❗不重算任何市場資料
# - ✅ 修復：A+ 市場過熱判斷
# - ✅ 修復：strong fallback 風控
# - ✅ 修復：action=0 顯示錯誤
# - ✅ 補齊完整註釋（可維護）
# ================================


from datetime import datetime
import pytz

from services.stock_api import get_twse, get_yahoo, get_realtime_price
from services.analysis import strategy, pick_best_stock
from core.condition_engine import condition_engine

tz = pytz.timezone("Asia/Taipei")


# ================================
# 🔒 股票池（可自行調整）
# ================================
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
# 🔥 行動轉換（UI 顯示）
# ================================
def get_action(result):
    """
    將 strategy 的 action / action_type
    轉換為顯示文字
    """

    action = result.get("action", 0)
    action_type = result.get("action_type")

    if action_type == "SELL_ALL":
        return "🔴 賣出 100%"

    if action_type == "BUY":
        return f"🟢 買進 {round(action*100)}%"

    return "⏳ 不動"


# ================================
# 🔥 訊號解釋（UI 顯示）
# ================================
def explain(result, conditions, stage):
    """
    將 decision_type 翻譯成人話
    """

    decision = result.get("decision")
    decision_type = result.get("decision_type")

    if decision == "BUY":

        if decision_type == "pre_breakout":
            return "突破前試單"
        elif decision_type == "add_on":
            return "突破確認，加碼"
        elif decision_type == "strong":
            return "主升段（強勢延續）"   # 🔥 v15.3 新增
        elif decision_type == "breakout":
            return "突破壓力"

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
# 🔥 市場時間判斷（不動）
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
# 🔥 安全處理
# ================================
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
# 🔥 stage 判斷（不可重算）
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
# 🔥 訊號缺失提示
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
# 🔥 主流程
# ================================
def generate():

    now = datetime.now(tz)
    phase = get_market_phase()

    msg = f"【{now.strftime('%m/%d')} {phase}】\n\n"

    decisions = []
    results_map = {}

    # ================================
    # 🔒 第一輪：抓市場資料（不可動）
    # ================================
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

        results_map[name] = {
            "result": result,
            "conditions": conditions,
            "stage": stage,
            "price": price,
            "change": change,
            "closes": closes
        }

    if not results_map:
        return msg + "⚠ 無有效數據"

    # ================================
    # 🔥 v15.3 資金分配（核心）
    # ================================
    buy_list = [
        (n, d["result"]) for n, d in results_map.items()
        if d["result"].get("decision") == "BUY"
    ]

    buy_list.sort(key=lambda x: x[1].get("strength", 0), reverse=True)

    if buy_list:

        scaled = []

        for _, r in buy_list:

            base = r.get("position", 0)
            dtype = r.get("decision_type")
            strength = r.get("strength", 0)

            # 🔥 階段控制（避免亂放大）
            if dtype == "pre_breakout":
                stage_factor = 0.6
            elif dtype == "add_on":
                stage_factor = 1.0
            elif dtype == "strong":
                stage_factor = 1.2
            else:
                stage_factor = 0.8   # 🔥 fallback 保守

            # 🔥 強度控制
            if strength >= 11:
                strength_factor = 1.3
            elif strength >= 9:
                strength_factor = 1.1
            else:
                strength_factor = 0.9

            scaled.append(base * stage_factor * strength_factor)

        # 🔥 市場過熱（支援 A+）
        grades = [d["result"].get("market_grade") for d in results_map.values()]

        if grades.count("A+") >= 3 or grades.count("A") >= 5:
            scaled = [p * 0.7 for p in scaled]

        # 🔥 強股集中
        if len(buy_list) >= 2:
            gap = buy_list[0][1]["strength"] - buy_list[1][1]["strength"]
            if gap >= 2:
                scaled[0] *= 1.2

        # 🔥 總倉風控
        total = sum(scaled)
        if total > 1:
            scaled = [p / total for p in scaled]

        for i, (n, r) in enumerate(buy_list):
            r["action"] = round(scaled[i], 2)

            # 🔥 修正 UI bug
            if r["action"] == 0:
                r["action_type"] = "HOLD"

    # ================================
    # 🔒 第二輪：純顯示（不可動）
    # ================================
    for name, data in results_map.items():

        result = data["result"]
        conditions = data["conditions"]
        stage = data["stage"]

        action = get_action(result)

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

        msg += f"💰 {safe_round(data['price'])}（{safe_round(data['change'],2)}%）\n\n"

    best, score = pick_best_stock({k: v["result"] for k, v in results_map.items()})

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