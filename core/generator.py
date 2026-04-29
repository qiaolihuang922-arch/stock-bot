# ================================
# 🔥 FINAL（顯示層 v15.9 FINAL LOCK）
# ================================

# 🔒 VERSION LOCK
# - ✅ 完整保留 v15.3 / v15.6 / v15.7 所有交易邏輯
# - ❌ 不動 strategy / condition_engine / 資金分配
# - ✅ 新增：距離細化（更準）
# - ✅ 新增：先過濾垃圾（只影響顯示）
# - ✅ 優化：UI 排版（決策優先）
# ================================

from datetime import datetime
import pytz

from services.stock_api import get_twse, get_yahoo, get_realtime_price
from services.analysis import strategy, pick_best_stock
from core.condition_engine import condition_engine

tz = pytz.timezone("Asia/Taipei")


# ================================
# 🔒 股票池
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
# 🔥 距離（優化版）
# ================================
def breakout_distance(price, closes):
    try:
        resistance = max(closes[-20:-3])
        dist = (resistance - price) / price * 100
        return round(dist, 2)
    except:
        return None


# ================================
# 🔥 型態
# ================================
def structure_progress(closes):
    score = 0
    if closes[-1] > closes[-2]: score += 1
    if closes[-2] > closes[-3]: score += 1
    if closes[-1] > sum(closes[-5:]) / 5: score += 1
    return score


# ================================
# 🔥 量能
# ================================
def volume_ratio(volumes):
    avg10 = sum(volumes[-10:]) / len(volumes[-10:])
    if avg10 == 0:
        return 1
    return round(volumes[-1] / avg10, 2)


# ================================
# 🔥 狀態翻譯（🔥核心優化）
# ================================
def translate_status(dist, struct, vol):

    # === 距離（重新分級）===
    if dist is None:
        d_text, d_score = "無資料", 0
    elif dist > 6:
        d_text, d_score = "很遠", 0
    elif dist > 3:
        d_text, d_score = "接近", 1
    elif dist > 1.5:
        d_text, d_score = "很近", 2
    else:
        d_text, d_score = "臨界", 3

    # === 型態 ===
    if struct == 3:
        s_text, s_score = "強勢", 3
    elif struct == 2:
        s_text, s_score = "成形中", 2
    elif struct == 1:
        s_text, s_score = "剛啟動", 1
    else:
        s_text, s_score = "弱", 0

    # === 量能 ===
    if vol > 1.5:
        v_text, v_score = "爆量", 3
    elif vol > 1.2:
        v_text, v_score = "放量", 2
    elif vol > 0.8:
        v_text, v_score = "普通", 1
    else:
        v_text, v_score = "無量", 0

    # ================================
    # 🔥 核心優化：先過濾垃圾（只影響顯示）
    # ================================
    if struct <= 1:
        return d_text, s_text, v_text, "❌ 不用看"

    if vol < 0.8:
        return d_text, s_text, v_text, "👀 觀察"

    # ================================
    # 🔥 再評分
    # ================================
    total = d_score + s_score + v_score

    if total >= 7:
        final = "🔥 可進場"
    elif total >= 5:
        final = "🟢 可試單"
    else:
        final = "👀 觀察"

    return d_text, s_text, v_text, final


# ================================
# 🔥 原有函數（完全不動）
# ================================
def get_action(result):
    action = result.get("action", 0)
    action_type = result.get("action_type")

    if action_type == "SELL_ALL":
        return "🔴 賣出 100%"
    if action_type == "BUY":
        return f"🟢 買進 {round(action*100)}%"
    return "⏳ 不動"


def explain(result, conditions, stage):

    decision = result.get("decision")
    decision_type = result.get("decision_type")

    if decision == "BUY":
        if decision_type == "pre_breakout":
            return "突破前試單"
        elif decision_type == "add_on":
            return "突破確認，加碼"
        elif decision_type == "strong":
            return "主升段（強勢延續）"
        elif decision_type == "breakout":
            return "突破壓力"
        return "訊號成立"

    if decision_type == "fail_exit":
        return "趨勢破壞，強制出場"

    if stage == "BREAKOUT_READY":
        return "接近突破"
    if stage == "APPROACH":
        return "接近壓力"

    return "尚未形成"


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


def build_signals(result, conditions):
    return []


# ================================
# 🔥 主流程（排版優化）
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

        results_map[name] = {
            "result": result,
            "conditions": conditions,
            "stage": stage,
            "price": price,
            "change": change,
            "closes": closes,
            "volumes": volumes
        }

    if not results_map:
        return msg + "⚠ 無有效數據"

    # ================================
    # 🔥 顯示
    # ================================
    for name, data in results_map.items():

        result = data["result"]
        stage = data["stage"]

        action = get_action(result)

        dist = breakout_distance(data["price"], data["closes"])
        struct = structure_progress(data["closes"])
        vol = volume_ratio(data["volumes"])

        d_text, s_text, v_text, final = translate_status(dist, struct, vol)

        # 🔥 主顯示（重點）
        msg += f"【{name}】{action}｜{final}\n"

        if result.get("market_grade"):
            msg += f"🌍 {result.get('market_grade')}｜{stage_to_text(stage)}\n"

        # 🔥 核心數據
        msg += f"📊 {dist}%｜{struct}/3｜{vol}x\n"
        msg += f"   → {d_text} / {s_text} / {v_text}\n"

        # 🔥 價格
        msg += f"💰 {safe_round(data['price'])}（{safe_round(data['change'],2)}%）\n\n"

    best, score = pick_best_stock({k: v["result"] for k, v in results_map.items()})

    msg += "====================\n"

    if best:
        msg += f"🔥 最強：{best}（{score}）\n"
    else:
        msg += "⚠ 無最強股\n"

    msg += "🟢 有機會" if any(d == "BUY" for d in decisions) else "⏳ 觀望"

    return msg