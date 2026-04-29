# ================================
# 🔥 FINAL（顯示層 v13.4｜v15.7 CLEAN UI LOCK）
# ================================

# 🔒 VERSION LOCK
# - ✅ 完整保留 v15.3 + v15.6 所有交易邏輯（逐行未動）
# - ❌ 僅移除「舊訊號顯示」（尚未觸發 / 型態未完成 / 量能不足）
# - ✅ 保留 build_signals / condition_engine（不影響策略）
# - ✅ 僅優化 UI 顯示（單一交易語言）
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
# 🔥 NEW：輔助計算（不影響原邏輯）
# ================================
def breakout_distance(price, closes):
    try:
        resistance = max(closes[-20:-3])
        return round((resistance - price) / price * 100, 2)
    except:
        return None


def structure_progress(closes):
    score = 0
    if closes[-1] > closes[-2]: score += 1
    if closes[-2] > closes[-3]: score += 1
    if closes[-1] > sum(closes[-5:]) / 5: score += 1
    return score


def volume_ratio(volumes):
    avg10 = sum(volumes[-10:]) / len(volumes[-10:])
    if avg10 == 0:
        return 1
    return round(volumes[-1] / avg10, 2)


# ================================
# 🔥 NEW：翻譯（只顯示用）
# ================================
def translate_status(dist, struct, vol):

    if dist is None:
        d_text = "無資料"
        d_score = 0
    elif dist > 5:
        d_text = "很遠"
        d_score = 0
    elif dist > 2:
        d_text = "接近"
        d_score = 1
    elif dist > 1:
        d_text = "很近"
        d_score = 2
    else:
        d_text = "幾乎突破"
        d_score = 3

    if struct == 3:
        s_text = "強勢"
        s_score = 3
    elif struct == 2:
        s_text = "成形中"
        s_score = 2
    elif struct == 1:
        s_text = "剛啟動"
        s_score = 1
    else:
        s_text = "弱"
        s_score = 0

    if vol > 1.5:
        v_text = "爆量"
        v_score = 3
    elif vol > 1.2:
        v_text = "放量"
        v_score = 2
    elif vol > 0.8:
        v_text = "普通"
        v_score = 1
    else:
        v_text = "無量"
        v_score = 0

    total = d_score + s_score + v_score

    if total >= 7:
        final = "🔥 可進場"
    elif total >= 5:
        final = "🟢 可試單"
    elif total >= 3:
        final = "👀 觀察"
    else:
        final = "❌ 不用看"

    return d_text, s_text, v_text, final


# ================================
# 🔥 原有函數（完全保留）
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
        return "接近突破（尚未進場）"

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
    # 🔒 保留（不刪邏輯）
    return []


# ================================
# 🔥 主流程（乾淨顯示）
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

    for name, data in results_map.items():

        result = data["result"]
        stage = data["stage"]

        action = get_action(result)

        msg += f"【{name}】{action}\n"

        if result.get("market_grade"):
            msg += f"🌍 市場：{result.get('market_grade')} ｜ {stage_to_text(stage)}\n"

        msg += f"💡 {explain(result, data['conditions'], stage)}\n"

        if result.get("decision") == "BUY":

            msg += f"📍 Buy: {safe_round(result.get('buy'))}\n"
            msg += f"🛑 Stop: {safe_round(result.get('stop'))}\n"
            msg += f"🎯 RR: {safe_round(result.get('rr'),2)}\n"

        else:
            # 🔥 新唯一判讀
            dist = breakout_distance(data["price"], data["closes"])
            struct = structure_progress(data["closes"])
            vol = volume_ratio(data["volumes"])

            d_text, s_text, v_text, final = translate_status(dist, struct, vol)

            msg += f"\n📊 狀態判讀：\n"
            msg += f"- 距突破：{dist}%（{d_text}）\n"
            msg += f"- 型態：{struct}/3（{s_text}）\n"
            msg += f"- 量能：{vol}x（{v_text}）\n"
            msg += f"👉 判斷：{final}\n"

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