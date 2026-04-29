# ================================
# 🔥 FINAL（顯示層 v16｜ALIGN v17｜STABLE）
# ================================

# 🔒 VERSION LOCK
# - ✅ 完整保留 strategy（v17）
# - ❌ 不動決策邏輯
# - ✅ 修正：UI 與 decision 對齊
# - ✅ 修正：距離 / stage 一致
# - ✅ 修正：顯示不再覆蓋交易結果
# - ✅ 強化：容錯（避免 crash）
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
    "南亞科": "2408",
    "英業達": "2356",
    "仁寶": "2324",
    "光寶科": "2301",
    "旺宏": "2337"
}


# ================================
# 🔥 距離（與 stage 對齊）
# ================================
def breakout_distance(price, closes):
    try:
        resistance = max(closes[-20:-3])
        dist = (resistance - price) / price * 100
        return round(dist, 2)
    except:
        return None


# ================================
# 🔥 型態（顯示用）
# ================================
def structure_progress(closes):
    try:
        score = 0
        if closes[-1] > closes[-2]: score += 1
        if closes[-2] > closes[-3]: score += 1
        if closes[-1] > sum(closes[-5:]) / 5: score += 1
        return score
    except:
        return 0


# ================================
# 🔥 量能（顯示用）
# ================================
def volume_ratio(volumes):
    try:
        avg10 = sum(volumes[-10:]) / len(volumes[-10:])
        if avg10 == 0:
            return 1
        return round(volumes[-1] / avg10, 2)
    except:
        return 1


# ================================
# 🔥 顯示評分（不影響交易）
# ================================
def translate_status(dist, struct, vol):

    # 距離
    if dist is None:
        d_text = "無資料"
    elif dist > 6:
        d_text = "很遠"
    elif dist > 3:
        d_text = "接近"
    elif dist > 1.5:
        d_text = "很近"
    else:
        d_text = "臨界"

    # 型態
    s_text = ["弱", "剛啟動", "成形中", "強勢"][min(struct, 3)]

    # 量能
    if vol > 1.5:
        v_text = "爆量"
    elif vol > 1.2:
        v_text = "放量"
    elif vol > 0.8:
        v_text = "普通"
    else:
        v_text = "無量"

    return d_text, s_text, v_text


# ================================
# 🔥 行為顯示（完全以 strategy 為準）
# ================================
def get_action(result):
    action_type = result.get("action_type")

    if action_type == "SELL_ALL":
        return "🔴 賣出 100%"
    if action_type == "BUY":
        return f"🟢 買進 {round(result.get('action', 0)*100)}%"
    return "⏳ 不動"


# ================================
# 🔥 決策顯示（關鍵修正）
# ================================
def get_final_label(result, market_grade, struct, vol):

    decision = result.get("decision")

    # 🔥 完全對齊 strategy（優先）
    if decision == "BUY":
        return "🔥 進場"
    if decision == "NO_TRADE":
        return "❌ 不用看"

    # 🔥 顯示輔助（僅 WAIT）
    if market_grade == "D":
        return "❌ 不用看"

    if struct <= 1:
        return "❌ 不用看"

    if vol < 0.8:
        return "👀 觀察"

    return "👀 觀察"


# ================================
# 🔥 市場階段
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
# 🔥 stage（與距離一致）
# ================================
def stage_detection(price, closes, market_grade=None):

    closes = safe_list(closes)

    if not closes:
        return "FAR"

    resistance = max(closes[-20:-3])
    dist = (resistance - price) / price

    if market_grade == "D":
        return "FAR"

    if dist < 0.02:
        return "BREAKOUT_READY"
    elif dist < 0.05:
        return "APPROACH"
    return "FAR"


def stage_to_text(stage):
    return {
        "BREAKOUT_READY": "🔥 突破前",
        "APPROACH": "👀 接近壓力",
        "FAR": "⏳ 尚未接近"
    }.get(stage)


# ================================
# 🔥 主流程
# ================================
def generate():

    now = datetime.now(tz)
    msg = f"【{now.strftime('%m/%d')} {get_market_phase()}】\n\n"

    decisions = []
    results_map = {}

    for name, code in stocks.items():

        twse = get_twse(code)
        yahoo = get_yahoo(code)

        if not twse:
            continue

        t_price, t_change, ma5, ma20, closes, volumes = twse

        realtime = get_realtime_price(code)

        if realtime:
            price, change = realtime
        elif yahoo:
            price, change = yahoo
        else:
            price, change = t_price, t_change

        if not closes or not volumes:
            continue

        result = strategy(price, ma5, ma20, closes, volumes)

        decisions.append(result.get("decision"))

        results_map[name] = {
            "result": result,
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

        dist = breakout_distance(data["price"], data["closes"])
        struct = structure_progress(data["closes"])
        vol = volume_ratio(data["volumes"])

        d_text, s_text, v_text = translate_status(dist, struct, vol)

        final = get_final_label(
            result,
            result.get("market_grade"),
            struct,
            vol
        )

        msg += f"【{name}】{get_action(result)}｜{final}\n"
        msg += f"🌍 {result.get('market_grade')}｜{stage_to_text(stage_detection(data['price'], data['closes'], result.get('market_grade')))}\n"
        msg += f"📊 {dist}%｜{struct}/3｜{vol}x\n"
        msg += f"   → {d_text} / {s_text} / {v_text}\n"
        msg += f"💰 {safe_round(data['price'])}（{safe_round(data['change'],2)}%）\n\n"

    best, score = pick_best_stock({k: v["result"] for k, v in results_map.items()})

    msg += "====================\n"
    msg += f"🔥 最強：{best}（{score}）\n" if best else "⚠ 無最強股\n"
    msg += "🟢 有機會" if any(d == "BUY" for d in decisions) else "⏳ 觀望"

    return msg