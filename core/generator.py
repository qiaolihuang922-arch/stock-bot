# ================================
# 🔥 FINAL（顯示層 v17.7.5｜SEMANTIC NORMALIZATION UI PATCH）
# ================================

# 🔒 VERSION LOCK
# - ✅ 完全對齊 strategy v17.7.5
# - ✅ breakout / trade / heat / lifecycle 完全分離
# - ✅ lifecycle 純趨勢語義
# - ✅ 新增：LATE_EXPANSION 顯示
# - ✅ 新增：trend_bias 顯示
# - ✅ 修正：LOW_RR → LATE_ENTRY
# - ✅ 修正：trade_state 語義
# - ✅ 修正：header 噪音
# - ✅ 修正：EXTREME / HOT 顯示一致
# - ✅ 修正：壓力與突破語義重疊
# - ✅ 修正：RR低不再污染 lifecycle
# - ✅ 修正：FAIL 不再污染 lifecycle
# - ✅ 修正：breakout_state 優先級
# - ✅ 修正：heat_state UI 對齊
# - ✅ UI 資訊降噪
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

VERSION = "v17.7.5"


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
# 🔥 safe list
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
# 🔥 safe round
# ================================
def safe_round(val, n=2):

    try:

        if val is None:
            return "-"

        return round(
            float(val),
            n
        )

    except:

        return "-"


# ================================
# 🔥 safe text
# ================================
def safe_text(
    val,
    fallback="-"
):

    if val is None:
        return fallback

    return str(val)


# ================================
# 🔥 market text
# ================================
def market_text(grade):

    mapping = {

        "A+":
            "🟢 A+",

        "A":
            "🟢 A",

        "B":
            "🟡 B",

        "C":
            "🟠 C",

        "D":
            "🔴 D"
    }

    return mapping.get(
        grade,
        grade
    )


# ================================
# 🔥 trend bias text
# ================================
def trend_bias_text(state):

    mapping = {

        "STRONG":
            "🟢 強勢",

        "NORMAL":
            "🟡 中性",

        "WEAK":
            "🔴 弱勢"
    }

    return mapping.get(
        state,
        "🟡 中性"
    )


# ================================
# 🔥 breakout distance
# ================================
def breakout_distance(
    price,
    closes
):

    try:

        closes = safe_list(closes)

        if not closes:
            return None

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
# 🔥 structure progress
# ================================
def structure_progress(
    closes,
    ma5,
    ma20
):

    try:

        closes = safe_list(closes)

        if not closes:
            return 0

        score = 0

        recent_high = max(
            closes[-5:]
        )

        old_high = max(
            closes[-10:-5]
        )

        recent_low = min(
            closes[-5:]
        )

        old_low = min(
            closes[-10:-5]
        )

        if recent_high > old_high:
            score += 1

        if recent_low > old_low:
            score += 1

        if ma5 > ma20:
            score += 1

        if closes[-1] > ma5:
            score += 1

        if closes[-1] > ma20:
            score += 1

        return score

    except:

        return 0


# ================================
# 🔥 volume ratio
# ================================
def volume_ratio(volumes):

    try:

        if not volumes:
            return 1

        avg10 = (

            sum(volumes[-10:])
            / max(len(volumes[-10:]), 1)
        )

        if avg10 <= 0:
            return 1

        return round(
            volumes[-1] / avg10,
            2
        )

    except:

        return 1


# ================================
# 🔥 volume price text
# ================================
def volume_price_text(state):

    mapping = {

        "EXPANSION":
            "量價擴張",

        "DISTRIBUTION":
            "放量出貨",

        "COILING":
            "縮量整理",

        "NORMAL":
            "正常"
    }

    return mapping.get(
        state,
        "正常"
    )


# ================================
# 🔥 lifecycle text
# ================================
def lifecycle_text(state):

    mapping = {

        "EXPANSION":
            "🔥 主升",

        "LATE_EXPANSION":
            "⚠ 延伸末段",

        "TREND":
            "📈 趨勢",

        "BASE":
            "⏳ 整理",

        "WEAK":
            "⚠ 弱勢",

        "DISTRIBUTION":
            "📦 出貨"
    }

    return mapping.get(
        state,
        "⏳ 整理"
    )


# ================================
# 🔥 breakout state text
# ================================
def breakout_state_text(state):

    mapping = {

        "BREAKOUT":
            "🚀 已突破",

        "READY":
            "🔥 突破前",

        "FAIL":
            "❌ 突破失敗",

        "FAKE_BREAK":
            "⚠ 假突破",

        "NONE":
            "⏳ 整理"
    }

    return mapping.get(
        state,
        "⏳ 整理"
    )


# ================================
# 🔥 trade state text
# ================================
def trade_state_text(state):

    mapping = {

        "TRADEABLE":
            "✅ 可交易",

        "LATE_ENTRY":
            "⚠ RR低",

        "NO_VOLUME":
            "⚠ 無量",

        "EXTENDED":
            "🌡 過熱",

        "AVOID":
            "🚨 禁追"
    }

    return mapping.get(
        state,
        "觀察"
    )


# ================================
# 🔥 heat state text
# ================================
def heat_state_text(state):

    mapping = {

        "NORMAL":
            "正常",

        "HOT":
            "過熱",

        "EXTREME":
            "極熱"
    }

    return mapping.get(
        state,
        "正常"
    )


# ================================
# 🔥 translate status
# ================================
def translate_status(
    struct,
    vol
):

    if struct >= 5:

        s_text = "強"

    elif struct >= 3:

        s_text = "成形"

    elif struct >= 1:

        s_text = "啟動"

    else:

        s_text = "弱"

    if vol >= 1.5:

        v_text = "爆量"

    elif vol >= 1.0:

        v_text = "放量"

    elif vol >= 0.7:

        v_text = "普通"

    else:

        v_text = "無量"

    return s_text, v_text


# ================================
# 🔥 action
# ================================
def get_action(result):

    decision = result.get(
        "decision"
    )

    action_type = result.get(
        "action_type"
    )

    if decision == "FAIL":

        return "❌"

    if action_type == "BUY":

        return (
            f"🟢 "
            f"{round(result.get('action', 0) * 100)}%"
        )

    return "⏳"


# ================================
# 🔥 entry stage label
# ================================
def get_entry_stage_label(result):

    stage = result.get(
        "entry_stage"
    )

    mapping = {

        "BREAKOUT_DAY1":
            "🔥 Day1",

        "CONFIRM_DAY2":
            "🚀 Day2",

        "TURN":
            "↗ 轉強",

        "PULLBACK":
            "↘ 拉回",

        "RECLAIM":
            "↗ 收復",

        "BREAKOUT_FAIL":
            "❌ 失敗"
    }

    return mapping.get(
        stage,
        ""
    )


# ================================
# 🔥 wait reason
# ================================
def wait_reason_text(reason):

    mapping = {

        "WAIT_EXTENDED":
            "過熱",

        "WAIT_EXTREME":
            "極熱",

        "WAIT_RR":
            "RR低",

        "WAIT_VOLUME":
            "等量",

        "WAIT_CONFIRM":
            "等確認",

        "WAIT_EXECUTION":
            "等進場",

        "WAIT_TREND":
            "弱勢",

        "WAIT_FAKE_BREAK":
            "假突破"
    }

    return mapping.get(
        reason,
        "觀察"
    )


# ================================
# 🔥 final label
# ================================
def get_final_label(result):

    decision = result.get(
        "decision"
    )

    if decision == "BUY":

        return "進場"

    if decision == "FAIL":

        return "失敗"

    if decision == "NO_TRADE":

        return "不交易"

    return wait_reason_text(
        result.get("wait_reason")
    )


# ================================
# 🔥 pressure stage
# ================================
def stage_detection(
    price,
    closes
):

    try:

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

        if price > breakout_price:

            return "BREAKOUT_DONE"

        elif dist < 0.02:

            return "BREAKOUT_READY"

        elif dist < 0.05:

            return "APPROACH"

        return "FAR"

    except:

        return "FAR"


# ================================
# 🔥 pressure text
# ================================
def stage_to_text(stage):

    mapping = {

        "BREAKOUT_DONE":
            "🚀 已突破",

        "BREAKOUT_READY":
            "🔥 突破前",

        "APPROACH":
            "👀 接近",

        "FAR":
            "⏳ 遠離"
    }

    return mapping.get(
        stage,
        "⏳ 整理"
    )


# ================================
# 🔥 market phase
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
# 🔥 realtime price
# ================================
def get_live_price_data(
    realtime,
    yahoo,
    twse_price,
    twse_change
):

    if realtime:

        return (
            realtime[0],
            realtime[1]
        )

    if yahoo:

        return (
            yahoo[0],
            yahoo[1]
        )

    return (
        twse_price,
        twse_change
    )


# ================================
# 🔥 main generate
# ================================
def generate():

    now = datetime.now(tz)

    msg = (

        f"【{now.strftime('%m/%d')} "
        f"{get_market_phase()}｜{VERSION}】\n"
    )

    msg += (
        "====================\n\n"
    )

    decisions = []

    results_map = {}

    # ================================
    # 🔥 scan
    # ================================
    for name, code in stocks.items():

        try:

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

        except Exception as e:

            msg += (
                f"⚠ {name} 錯誤：{str(e)}\n"
            )

    if not results_map:

        return msg + "\n⚠ 無有效數據"

    # ================================
    # 🔥 render
    # ================================
    for name, data in results_map.items():

        try:

            result = data["result"]

            ext_level = result.get(
                "extended_level",
                0
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

            s_text, v_text = (
                translate_status(
                    struct,
                    vol
                )
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

            lifecycle = lifecycle_text(
                result.get(
                    "lifecycle"
                )
            )

            breakout_state = (
                breakout_state_text(
                    result.get(
                        "breakout_state"
                    )
                )
            )

            trade_state = (
                trade_state_text(
                    result.get(
                        "trade_state"
                    )
                )
            )

            heat_state = (
                heat_state_text(
                    result.get(
                        "heat_state"
                    )
                )
            )

            trend_bias = (
                trend_bias_text(
                    result.get(
                        "trend_bias"
                    )
                )
            )

            setup_score = safe_round(
                result.get(
                    "setup_score"
                ),
                1
            )

            exec_score = safe_round(
                result.get(
                    "execution_score"
                ),
                1
            )

            strength = safe_round(
                result.get(
                    "strength"
                ),
                2
            )

            # ================================
            # 🔥 header
            # ================================
            header = (

                f"【{name}】 "
                f"{get_action(result)} "
                f"{final}"
            )

            if entry_stage:
                header += (
                    f" ｜{entry_stage}"
                )

            msg += header + "\n"

            # ================================
            # 🔥 semantic layer
            # ================================
            msg += (
                f"├─ 趨勢："
                f"{lifecycle}\n"
            )

            msg += (
                f"├─ 強度："
                f"{trend_bias}\n"
            )

            msg += (
                f"├─ 突破："
                f"{breakout_state}\n"
            )

            msg += (
                f"├─ 交易："
                f"{trade_state}\n"
            )

            msg += (
                f"├─ 熱度："
                f"{heat_state}\n"
            )

            # ================================
            # 🔥 structure
            # ================================
            msg += (
                f"├─ 市場："
                f"{market_text(result.get('market_grade'))}\n"
            )

            msg += (
                f"├─ 壓力："
                f"{stage_to_text(stage_detection(data['price'], data['closes']))}\n"
            )

            msg += (
                f"├─ 結構："
                f"{s_text}"
                f" / "
                f"{v_text}"
                f" / "
                f"{vp_state}\n"
            )

            # ================================
            # 🔥 data
            # ================================
            msg += (

                f"├─ 數據："
                f"Dist {safe_round(dist, 2)}%"
                f" ｜RR {safe_round(result.get('rr'), 2)}"
                f" ｜S {struct}/5"
                f" ｜V {vol}x\n"
            )

            msg += (

                f"├─ 評分："
                f"Setup {setup_score}/10"
                f" ｜Exec {exec_score}/8"
                f" ｜★ {strength}\n"
            )

            if ext_level >= 2:

                msg += (
                    f"├─ 過熱："
                    f"Lv.{ext_level}\n"
                )

            msg += (

                f"└─ 💰 "
                f"{safe_round(data['price'], 2)}"
                f"（"
                f"{safe_round(data['change'], 2)}%"
                f"）\n\n"
            )

        except Exception as e:

            msg += (
                f"⚠ {name} 顯示錯誤：{str(e)}\n\n"
            )

    # ================================
    # 🔥 best stock
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
            f"（★{safe_round(score, 2)}）\n"
        )

    else:

        msg += "⚠ 無最強股\n"

    # ================================
    # 🔥 market summary
    # ================================
    buy_count = sum(

        1
        for d in decisions
        if d == "BUY"
    )

    fail_count = sum(

        1
        for d in decisions
        if d == "FAIL"
    )

    if buy_count >= 3:

        msg += "🟢 市場偏強"

    elif buy_count > 0:

        msg += "🟡 局部機會"

    elif fail_count > 0:

        msg += "🔴 突破失敗增多"

    else:

        msg += "⏳ 觀望"

    return msg