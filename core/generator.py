# ================================
# 🔥 FINAL（顯示層 v17.5｜REAL DAY1 / DAY2 STATE MACHINE）
# ================================

# 🔒 VERSION LOCK
# - ✅ 完全對齊 strategy v17.5
# - ✅ 顯示真正 Day1 / Day2
# - ✅ 顯示 BREAKOUT_FAIL
# - ✅ 顯示 WAIT reason
# - ✅ 顯示 volume-price lifecycle
# - ✅ 顯示 EXTENDED（降倉模式）
# - ✅ breakout threshold 全系統一致
# - ✅ 顯示真正即時價格
# - ✅ 顯示真 RR（minimum stop）
# - ✅ 修正：NO_TRADE 不再顯示 SELL_ALL
# - ✅ 修正：state machine 顯示
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

        return (
            data
            + [data[-1]] * (n - len(data))
        )

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
# 🔥 breakout_distance（v17.5）
# ================================
def breakout_distance(price, closes):

    try:

        resistance = max(
            closes[-20:-3]
        )

        breakout_price = (
            resistance
            * (1 + BREAKOUT_THRESHOLD)
        )

        return round(
            (
                breakout_price - price
            ) / price * 100,
            2
        )

    except:

        return None


# ================================
# 🔥 structure_progress（v17.5）
# ================================
def structure_progress(
    closes,
    ma5,
    ma20
):

    try:

        score = 0

        # 🔥 higher low
        if min(closes[-3:]) > min(closes[-6:-3]):
            score += 1

        # 🔥 ma alignment
        if ma5 > ma20:
            score += 1

        # 🔥 above avg
        if closes[-1] > sum(closes[-5:]) / 5:
            score += 1

        # 🔥 above ma20
        if closes[-1] > ma20:
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
# 🔥 volume_price_text（v17.5）
# ================================
def volume_price_text(state):

    mapping = {

        "EXPANSION": "量價擴張",

        "DISTRIBUTION": "放量出貨",

        "COILING": "縮量整理",

        "NORMAL": "正常"
    }

    return mapping.get(
        state,
        "正常"
    )


# ================================
# 🔥 translate_status（v17.5）
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
    # 🔥 volume
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
# 🔥 action（v17.5）
# ================================
def get_action(result):

    decision = result.get("decision")

    action_type = result.get(
        "action_type"
    )

    # 🔥 EXIT
    if decision == "EXIT":

        return "🔴 清倉"

    # 🔥 BUY
    if action_type == "BUY":

        return (
            f"🟢 買進 "
            f"{round(result.get('action', 0)*100)}%"
        )

    # 🔥 NO_TRADE / WAIT
    return "⏳ 不動"


# ================================
# 🔥 state label（v17.5）
# ================================
def get_entry_stage_label(result):

    stage = result.get(
        "entry_stage"
    )

    mapping = {

        # 🔥 真 Day1
        "BREAKOUT_DAY1":
            "（🔥 Day1 突破）",

        # 🔥 真 Day2
        "CONFIRM_DAY2":
            "（🚀 Day2 確認）",

        # 🔥 TURN
        "TURN":
            "（↗ 轉強）",

        # 🔥 fail
        "BREAKOUT_FAIL":
            "（❌ 突破失敗）",

        "REJECT":
            "（⚠ 結構失敗）"
    }

    return mapping.get(
        stage,
        ""
    )


# ================================
# 🔥 WAIT reason（v17.5）
# ================================
def wait_reason_text(reason):

    mapping = {

        "WAIT_EXTENDED":
            "⚠ 過熱",

        "WAIT_RR":
            "⚠ RR 不佳",

        "WAIT_VOLUME":
            "👀 等量",

        "WAIT_BREAKOUT":
            "👀 等突破",

        "WAIT_TREND":
            "❌ 趨勢差",

        "WAIT_FAKE_BREAK":
            "⚠ 假突破",

        "WAIT":
            "👀 觀察"
    }

    return mapping.get(
        reason,
        "👀 觀察"
    )


# ================================
# 🔥 final label（v17.5）
# ================================
def get_final_label(result):

    decision = result.get(
        "decision"
    )

    # ================================
    # 🔥 BUY
    # ================================
    if decision == "BUY":

        return "🔥 進場"

    # ================================
    # 🔥 EXIT
    # ================================
    if decision == "EXIT":

        return "❌ 離場"

    # ================================
    # 🔥 NO_TRADE
    # ================================
    if decision == "NO_TRADE":

        return "❌ 不交易"

    # ================================
    # 🔥 WAIT
    # ================================
    return wait_reason_text(
        result.get("wait_reason")
    )


# ================================
# 🔥 stage_detection（v17.5）
# ================================
def stage_detection(
    price,
    closes,
    extended=False
):

    closes = safe_list(closes)

    if not closes:

        return "FAR"

    resistance = max(
        closes[-20:-3]
    )

    breakout_price = (
        resistance
        * (1 + BREAKOUT_THRESHOLD)
    )

    dist = (
        breakout_price - price
    ) / price

    # ================================
    # 🔥 EXTENDED
    # ================================
    if extended:

        return "EXTENDED"

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
# 🔥 stage_to_text（v17.5）
# ================================
def stage_to_text(stage):

    mapping = {

        "BREAKOUT_DONE":
            "🚀 已突破",

        "BREAKOUT_READY":
            "🔥 突破前",

        "APPROACH":
            "👀 接近壓力",

        "FAR":
            "⏳ 尚未接近",

        "EXTENDED":
            "⚠ 過熱區"
    }

    return mapping.get(
        stage,
        "⏳ 尚未接近"
    )


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
# 🔥 即時價格
# ================================
def get_live_price_data(
    realtime,
    yahoo,
    twse_price,
    twse_change
):

    # 🔥 realtime 優先
    if realtime:

        return (
            realtime[0],
            realtime[1]
        )

    # 🔥 yahoo 第二
    if yahoo:

        return (
            yahoo[0],
            yahoo[1]
        )

    # 🔥 fallback
    return (
        twse_price,
        twse_change
    )


# ================================
# 🔥 主流程（v17.5）
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

        # 🔥 即時價格
        price, change = (
            get_live_price_data(
                realtime,
                yahoo,
                t_price,
                t_change
            )
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

        extended = result.get(
            "extended",
            False
        )

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
            data["closes"],
            extended
        )

        final = get_final_label(
            result
        )

        entry_stage = (
            get_entry_stage_label(
                result
            )
        )

        vp_state = volume_price_text(
            result.get(
                "volume_price_state"
            )
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
            f"{stage_to_text(stage)}\n"
        )

        msg += (
            f"📊 "
            f"{safe_round(dist,2)}%"
            f"｜{struct}/4"
            f"｜{vol}x"
            f"｜RR "
            f"{safe_round(result.get('rr'),2)}\n"
        )

        # 🔥 volume-price lifecycle
        msg += (
            f"   → "
            f"{d_text}"
            f" / "
            f"{s_text}"
            f" / "
            f"{v_text}"
            f" / "
            f"{vp_state}\n"
        )

        # 🔥 即時價格
        msg += (
            f"💰 "
            f"{safe_round(data['price'],2)}"
            f"（"
            f"{safe_round(data['change'],2)}%"
            f"）\n\n"
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
    # 🔥 市場總結
    # ================================
    if any(
        d == "BUY"
        for d in decisions
    ):

        msg += "🟢 有機會"

    else:

        msg += "⏳ 觀望"

    return msg