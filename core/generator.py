# ================================
# 🔥 FINAL（顯示層 v17.4｜REAL TURN + REAL BREAKOUT）
# ================================

# 🔒 VERSION LOCK
# - ✅ 完全對齊 strategy v17.4
# - ✅ breakout threshold 全系統一致
# - ✅ 顯示 EXTENDED（過熱）
# - ✅ 顯示真實 RR
# - ✅ 顯示 volume 新分級
# - ✅ 修正：即時價格顯示
# - ✅ 修正：WAIT 分類
# - ✅ 保持：不干擾 strategy
# ================================


from datetime import datetime
import pytz

from services.stock_api import (
    get_twse,
    get_yahoo,
    get_realtime_price
)

from services.analysis import (
    strategy,
    pick_best_stock,
    BREAKOUT_THRESHOLD
)

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
# 🔥 safe_list
# ================================
def safe_list(data, n=20):

    if not data:
        return None

    if len(data) < n:
        return data + [data[-1]] * (n - len(data))

    return data


# ================================
# 🔥 safe_round
# ================================
def safe_round(val, n=2):

    try:
        return round(float(val), n)

    except:
        return "-"


# ================================
# 🔥 breakout_distance（v17.4）
# ================================
def breakout_distance(price, closes):

    try:

        resistance = max(closes[-20:-3])

        return round(
            (resistance - price) / price * 100,
            2
        )

    except:
        return None


# ================================
# 🔥 structure_progress（v17.4）
# ================================
def structure_progress(closes, ma5, ma20):

    try:

        score = 0

        if closes[-1] > closes[-2]:
            score += 1

        if ma5 > ma20:
            score += 1

        if closes[-1] > sum(closes[-5:]) / 5:
            score += 1

        if closes[-2] > closes[-3]:
            score += 1

        return score

    except:
        return 0


# ================================
# 🔥 volume_ratio
# ================================
def volume_ratio(volumes):

    try:

        avg10 = (
            sum(volumes[-10:])
            / len(volumes[-10:])
        )

        return round(
            volumes[-1] / avg10,
            2
        ) if avg10 else 1

    except:
        return 1


# ================================
# 🔥 translate_status（v17.4）
# ================================
def translate_status(
    dist,
    struct,
    vol,
    extended=False
):

    # ================================
    # 🔥 距離
    # ================================
    if extended:

        d_text = "過熱"

    elif dist is None:

        d_text = "無資料"

    elif dist < 0:

        d_text = "已突破"

    elif dist <= 1.5:

        d_text = "臨界"

    elif dist <= 3:

        d_text = "很近"

    elif dist <= 6:

        d_text = "接近"

    else:

        d_text = "很遠"

    # ================================
    # 🔥 結構
    # ================================
    if struct >= 4:
        s_text = "強勢"

    elif struct >= 2:
        s_text = "成形中"

    elif struct >= 1:
        s_text = "剛啟動"

    else:
        s_text = "弱"

    # ================================
    # 🔥 volume（v17.4）
    # ================================
    if vol >= 1.5:

        v_text = "爆量"

    elif vol >= 1.0:

        v_text = "放量"

    elif vol >= 0.7:

        v_text = "普通"

    else:

        v_text = "無量"

    return d_text, s_text, v_text


# ================================
# 🔥 action
# ================================
def get_action(result):

    t = result.get("action_type")

    if t == "SELL_ALL":

        return "🔴 賣出 100%"

    if t == "BUY":

        return (
            f"🟢 買進 "
            f"{round(result.get('action', 0)*100)}%"
        )

    return "⏳ 不動"


# ================================
# 🔥 entry_stage（v17.4）
# ================================
def get_entry_stage_label(result):

    if result.get("decision") != "BUY":
        return ""

    stage = result.get("entry_stage")

    if stage == "TURN":

        return "（Day1 轉強）"

    elif stage == "CONFIRM":

        return "（Day2 延續）"

    elif stage == "REJECT":

        return "（❌ 失敗）"

    return ""


# ================================
# 🔥 WAIT label（v17.4）
# ================================
def get_final_label(result, struct, vol):

    decision = result.get("decision")

    extended = result.get("extended")

    rr = result.get("rr", 0)

    # ================================
    # 🔥 BUY
    # ================================
    if decision == "BUY":

        return "🔥 進場"

    # ================================
    # 🔥 NO TRADE
    # ================================
    if decision == "NO_TRADE":

        return "❌ 不用看"

    # ================================
    # 🔥 過熱
    # ================================
    if extended:

        return "⚠ 過熱"

    # ================================
    # 🔥 RR 太差
    # ================================
    if rr < 1:

        return "⚠ RR 不佳"

    # ================================
    # 🔥 無量
    # ================================
    if vol < 0.7:

        return "👀 等量"

    # ================================
    # 🔥 快突破
    # ================================
    if struct >= 3:

        return "👀 等突破"

    return "👀 觀察"


# ================================
# 🔥 stage_detection（v17.4）
# ================================
def stage_detection(price, closes):

    closes = safe_list(closes)

    if not closes:
        return "FAR"

    resistance = max(closes[-20:-3])

    breakout_price = (
        resistance
        * (1 + BREAKOUT_THRESHOLD)
    )

    dist = (
        breakout_price - price
    ) / price

    # ================================
    # 🔥 breakout
    # ================================
    if price > breakout_price:

        return "BREAKOUT_DONE"

    elif dist < 0.02:

        return "BREAKOUT_READY"

    elif dist < 0.05:

        return "APPROACH"

    return "FAR"


# ================================
# 🔥 stage_to_text
# ================================
def stage_to_text(stage, extended=False):

    if extended:

        return "⚠ 過熱區"

    return {

        "BREAKOUT_DONE": "🚀 已突破",

        "BREAKOUT_READY": "🔥 突破前",

        "APPROACH": "👀 接近壓力",

        "FAR": "⏳ 尚未接近"

    }.get(stage)


# ================================
# 🔥 市場時間
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
# 🔥 即時價格（v17.4 修正）
# ================================
def get_live_price_data(
    realtime,
    yahoo,
    twse_price,
    twse_change
):

    # 🔥 realtime 優先
    if realtime:

        return realtime[0], realtime[1]

    # 🔥 yahoo 第二
    if yahoo:

        return yahoo[0], yahoo[1]

    # 🔥 fallback
    return twse_price, twse_change


# ================================
# 🔥 主流程
# ================================
def generate():

    now = datetime.now(tz)

    msg = (
        f"【{now.strftime('%m/%d')} "
        f"{get_market_phase()}】\n\n"
    )

    decisions = []

    results_map = {}

    # ================================
    # 🔥 scan
    # ================================
    for name, code in stocks.items():

        twse = get_twse(code)

        if not twse:
            continue

        (
            t_price,
            t_change,
            ma5,
            ma20,
            closes,
            volumes
        ) = twse

        realtime = get_realtime_price(code)

        yahoo = get_yahoo(code)

        # 🔥 v17.4：真正即時價格
        price, change = get_live_price_data(
            realtime,
            yahoo,
            t_price,
            t_change
        )

        if not closes or not volumes:
            continue

        # 🔥 strategy
        result = strategy(
            price,
            ma5,
            ma20,
            closes,
            volumes
        )

        decisions.append(
            result.get("decision")
        )

        results_map[name] = {

            "result": result,

            "price": price,
            "change": change,

            "ma5": ma5,
            "ma20": ma20,

            "closes": closes,
            "volumes": volumes
        }

    # ================================
    # 🔥 無資料
    # ================================
    if not results_map:

        return msg + "⚠ 無有效數據"

    # ================================
    # 🔥 顯示
    # ================================
    for name, data in results_map.items():

        result = data["result"]

        dist = breakout_distance(
            data["price"],
            data["closes"]
        )

        struct = structure_progress(
            data["closes"],
            data["ma5"],
            data["ma20"]
        )

        vol = volume_ratio(
            data["volumes"]
        )

        extended = result.get(
            "extended",
            False
        )

        d_text, s_text, v_text = (
            translate_status(
                dist,
                struct,
                vol,
                extended
            )
        )

        stage = stage_detection(
            data["price"],
            data["closes"]
        )

        final = get_final_label(
            result,
            struct,
            vol
        )

        entry_stage = (
            get_entry_stage_label(result)
        )

        # ================================
        # 🔥 output
        # ================================
        msg += (
            f"【{name}】"
            f"{get_action(result)}"
            f"｜{final}"
            f"{entry_stage}\n"
        )

        msg += (
            f"🌍 "
            f"{result.get('market_grade')}"
            f"｜"
            f"{stage_to_text(stage, extended)}\n"
        )

        msg += (
            f"📊 "
            f"{safe_round(dist,2)}%"
            f"｜{struct}/4"
            f"｜{vol}x"
            f"｜RR {safe_round(result.get('rr'),2)}\n"
        )

        msg += (
            f"   → "
            f"{d_text}"
            f" / "
            f"{s_text}"
            f" / "
            f"{v_text}\n"
        )

        # 🔥 v17.4：顯示真正即時價格
        msg += (
            f"💰 "
            f"{safe_round(data['price'],2)}"
            f"（{safe_round(data['change'],2)}%）\n\n"
        )

    # ================================
    # 🔥 最強股
    # ================================
    best, score = pick_best_stock({

        k: v["result"]

        for k, v in results_map.items()

    })

    msg += "====================\n"

    if best:

        msg += (
            f"🔥 最強："
            f"{best}"
            f"（{safe_round(score,2)}）\n"
        )

    else:

        msg += "⚠ 無最強股\n"

    # ================================
    # 🔥 market summary
    # ================================
    if any(d == "BUY" for d in decisions):

        msg += "🟢 有機會"

    else:

        msg += "⏳ 觀望"

    return msg