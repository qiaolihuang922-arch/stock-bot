# ================================
# 🔥 FINAL（顯示層 v17.7｜UI NORMALIZATION）
# ================================

# 🔒 VERSION LOCK
# - ✅ 完全對齊 strategy v17.7
# - ✅ 修復：FAIL / BASE / RECLAIM 對齊
# - ✅ 修復：extended_level 顯示
# - ✅ 修復：lifecycle fallback
# - ✅ 修復：None safe
# - ✅ 修復：dist 顯示 None 問題
# - ✅ 修復：score 顯示 crash
# - ✅ 修復：volume ratio division
# - ✅ 修復：stage detection 空資料
# - ✅ 修復：結構顯示與 strategy 對齊
# - ✅ 修復：Strength 顯示過度膨脹
# - ✅ 修復：重複 lifecycle / stage 顯示
# - ✅ UI 重構（資訊降噪）
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

        if val is None:
            return "-"

        return round(float(val), n)

    except:

        return "-"


# ================================
# 🔥 safe_text
# ================================
def safe_text(val, fallback="-"):

    if val is None:
        return fallback

    return str(val)


# ================================
# 🔥 breakout_distance（v17.7）
# ================================
def breakout_distance(price, closes):

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
# 🔥 structure_progress（v17.7）
# 🔥 對齊 strategy v17.7
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

        recent_high = max(closes[-5:])
        old_high = max(closes[-10:-5])

        recent_low = min(closes[-5:])
        old_low = min(closes[-10:-5])

        # 🔥 higher high
        if recent_high > old_high:
            score += 1

        # 🔥 higher low
        if recent_low > old_low:
            score += 1

        # 🔥 ma alignment
        if ma5 > ma20:
            score += 1

        # 🔥 close above ma5
        if closes[-1] > ma5:
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
# 🔥 volume-price text
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
# 🔥 lifecycle text（v17.7）
# 🔥 降低英文感
# ================================
def lifecycle_text(state):

    mapping = {

        "BREAKOUT":
            "🚀 突破",

        "EXPANSION":
            "🔥 主升",

        "PRE_BREAKOUT":
            "⏳ 突破前",

        "PULLBACK":
            "↘ 拉回",

        "RECLAIM":
            "↗ 收復",

        "TURN":
            "↗ 轉強",

        "CONFIRM_DAY2":
            "🚀 Day2",

        "BREAKOUT_DAY1":
            "🔥 Day1",

        "FAIL":
            "❌ 失敗",

        "FAKE_BREAK":
            "⚠ 假突破",

        "EXTREME":
            "🚨 極熱",

        "BASE":
            "⏳ 整理"
    }

    return mapping.get(
        state,
        "⏳ 整理"
    )


# ================================
# 🔥 translate_status（v17.7）
# ================================
def translate_status(
    dist,
    struct,
    vol,
    ext_level=0
):

    # ================================
    # 🔥 距離
    # ================================
    if ext_level >= 3:

        d_text = "極熱"

    elif ext_level >= 2:

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
    if struct >= 5:

        s_text = "強"

    elif struct >= 3:

        s_text = "成形"

    elif struct >= 1:

        s_text = "啟動"

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
# 🔥 action（v17.7）
# ================================
def get_action(result):

    decision = result.get(
        "decision"
    )

    action_type = result.get(
        "action_type"
    )

    # 🔥 FAIL
    if decision == "FAIL":

        return "❌"

    # 🔥 BUY
    if action_type == "BUY":

        return (
            f"🟢 "
            f"{round(result.get('action', 0)*100)}%"
        )

    return "⏳"


# ================================
# 🔥 entry stage label
# 🔥 避免與 lifecycle 重複
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
# 🔥 WAIT reason
# ================================
def wait_reason_text(reason):

    mapping = {

        "WAIT_EXTENDED":
            "⚠ 過熱",

        "WAIT_RR":
            "⚠ RR低",

        "WAIT_VOLUME":
            "👀 等量",

        "WAIT_CONFIRM":
            "👀 等確認",

        "WAIT_EXECUTION":
            "👀 等進場",

        "WAIT_TREND":
            "❌ 弱勢",

        "WAIT_FAKE_BREAK":
            "⚠ 假突破"
    }

    return mapping.get(
        reason,
        "👀 觀察"
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
# 🔥 stage detection
# ================================
def stage_detection(
    price,
    closes,
    ext_level=0
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

        if ext_level >= 3:

            return "EXTREME"

        elif ext_level >= 2:

            return "EXTENDED"

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
# 🔥 stage text
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
            "⏳ 遠離",

        "EXTENDED":
            "⚠ 過熱",

        "EXTREME":
            "🚨 極熱"
    }

    return mapping.get(
        stage,
        "⏳ 整理"
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

    return (
        twse_price,
        twse_change
    )


# ================================
# 🔥 主流程（v17.7 UI）
# ================================
def generate():

    now = datetime.now(tz)

    msg = (
        f"【{now.strftime('%m/%d')} "
        f"{get_market_phase()}】\n"
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

    # ================================
    # 🔥 無資料
    # ================================
    if not results_map:

        return msg + "\n⚠ 無有效數據"

    # ================================
    # 🔥 顯示
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

            d_text, s_text, v_text = (
                translate_status(
                    dist,
                    struct,
                    vol,
                    ext_level
                )
            )

            stage = stage_detection(
                data["price"],
                data["closes"],
                ext_level
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
            # 🔥 標題列（降噪）
            # ================================
            header = (
                f"【{name}】"
                f"{get_action(result)} "
                f"{final}"
            )

            if entry_stage:
                header += f" ｜{entry_stage}"

            msg += header + "\n"

            # ================================
            # 🔥 lifecycle / market
            # ================================
            msg += (
                f"├─ "
                f"{lifecycle}"
                f" ｜"
                f"{safe_text(result.get('market_grade'))}"
                f" ｜"
                f"{stage_to_text(stage)}\n"
            )

            # ================================
            # 🔥 structure
            # ================================
            msg += (
                f"├─ "
                f"{d_text}"
                f" / "
                f"{s_text}"
                f" / "
                f"{v_text}"
                f" / "
                f"{vp_state}\n"
            )

            # ================================
            # 🔥 data（精簡）
            # ================================
            msg += (
                f"├─ "
                f"Dist {safe_round(dist,2)}%"
                f" ｜RR {safe_round(result.get('rr'),2)}"
                f" ｜S {struct}/5"
                f" ｜V {vol}x\n"
            )

            # ================================
            # 🔥 score（簡化）
            # ================================
            msg += (
                f"├─ "
                f"Setup {setup_score}"
                f" ｜Exec {exec_score}"
                f" ｜★ {strength}\n"
            )

            # ================================
            # 🔥 過熱
            # ================================
            if ext_level > 0:

                msg += (
                    f"├─ "
                    f"過熱 Lv.{ext_level}\n"
                )

            # ================================
            # 🔥 price
            # ================================
            msg += (
                f"└─ 💰 "
                f"{safe_round(data['price'],2)}"
                f"（"
                f"{safe_round(data['change'],2)}%"
                f"）\n\n"
            )

        except Exception as e:

            msg += (
                f"⚠ {name} 顯示錯誤：{str(e)}\n\n"
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
            f"（★{safe_round(score,2)}）\n"
        )

    else:

        msg += "⚠ 無最強股\n"

    # ================================
    # 🔥 市場總結
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