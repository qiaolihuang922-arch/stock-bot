# ================================
# 🔥 FINAL UI（v18.0 Semantic UI Compression）
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

VERSION = "v18.0"


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
# 🔥 safe utils
# ================================
def safe_list(data, n=20):

    if not data:
        return None

    if len(data) < n:
        return data + [data[-1]] * (n - len(data))

    return data


def safe_round(val, n=2):

    try:

        if val is None:
            return "-"

        return round(float(val), n)

    except:
        return "-"


# ================================
# 🔥 semantic maps
# ================================
MARKET_MAP = {

    "A+": "🟢 A+",
    "A": "🟢 A",
    "B": "🟡 B",
    "C": "🟠 C",
    "D": "🔴 D"
}

TREND_MAP = {

    "STRONG": "🟢 強勢",
    "NORMAL": "🟡 中性",
    "WEAK": "🔴 弱勢"
}

DOMINANT_MAP = {

    "FAILED": "❌ 失敗",
    "EXTREME": "🚨 極熱",
    "LATE": "⚠ 末段",
    "BREAKOUT": "🚀 突破",
    "TREND": "📈 趨勢",
    "NORMAL": "⏳ 正常"
}

LIFECYCLE_MAP = {

    "BREAKOUT_TREND": "🚀 主升突破",
    "TREND": "📈 趨勢",
    "LATE_TREND": "⚠ 趨勢末段",
    "BASE": "⏳ 整理",
    "WEAK": "⚠ 弱勢",
    "DISTRIBUTION": "📦 出貨",
    "FAILED": "❌ 失敗",
    "EXTREME": "🚨 極熱"
}

BREAKOUT_MAP = {

    "BREAKOUT": "🚀 已突破",
    "READY": "🔥 突破前",
    "FAIL": "❌ 突破失敗",
    "FAKE_BREAK": "⚠ 假突破",
    "NONE": "⏳ 整理"
}

TRADE_MAP = {

    "TRADEABLE": "✅ 可交易",
    "LATE_ENTRY": "⚠ RR低",
    "NO_VOLUME": "⚠ 無量",
    "EXTENDED": "🌡 過熱",
    "AVOID": "🚨 禁追"
}

HEAT_MAP = {

    "NORMAL": "正常",
    "HOT": "過熱",
    "EXTREME": "極熱"
}

VP_MAP = {

    "EXPANSION": "🚀 擴張",
    "DISTRIBUTION": "📦 出貨",
    "COILING": "🔹 收縮",
    "NORMAL": "正常"
}

WAIT_MAP = {

    "WAIT_EXTENDED": "過熱",
    "WAIT_EXTREME": "極熱",
    "WAIT_RR": "RR低",
    "WAIT_VOLUME": "等量",
    "WAIT_CONFIRM": "等確認",
    "WAIT_EXECUTION": "等進場",
    "WAIT_TREND": "弱勢",
    "WAIT_FAKE_BREAK": "假突破"
}

ENTRY_MAP = {

    "BREAKOUT_DAY1": "🔥 Day1",
    "CONFIRM_DAY2": "🚀 Day2",
    "TURN": "↗ 轉強",
    "PULLBACK": "↘ 拉回",
    "RECLAIM": "↗ 收復",
    "BREAKOUT_FAIL": "❌ 失敗"
}


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

    if 9 <= h < 13:
        return "盤中"

    if h == 13 and m >= 20:
        return "收盤"

    return "盤後"


# ================================
# 🔥 realtime merge
# ================================
def get_live_price_data(
    realtime,
    yahoo,
    twse_price,
    twse_change
):

    if realtime:
        return realtime[0], realtime[1]

    if yahoo:
        return yahoo[0], yahoo[1]

    return twse_price, twse_change


# ================================
# 🔥 semantic structure
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

        if max(closes[-5:]) > max(closes[-10:-5]):
            score += 1

        if min(closes[-5:]) > min(closes[-10:-5]):
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


def volume_ratio(volumes):

    try:

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


def structure_text(score):

    if score >= 5:
        return "強"

    if score >= 3:
        return "成形"

    if score >= 1:
        return "啟動"

    return "弱"


def volume_text(vol):

    if vol >= 1.5:
        return "爆量"

    if vol >= 1.0:
        return "放量"

    if vol >= 0.7:
        return "普通"

    return "無量"


# ================================
# 🔥 breakout distance
# ================================
def breakout_distance(
    price,
    closes
):

    try:

        closes = safe_list(closes)

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
# 🔥 semantic pressure
# ================================
def semantic_pressure(
    result,
    price,
    closes
):

    if result.get(
        "breakout_state"
    ) in [
        "BREAKOUT",
        "READY",
        "FAIL"
    ]:
        return None

    try:

        closes = safe_list(closes)

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
            return "🚀 已突破"

        if dist < 0.02:
            return "🔥 突破前"

        if dist < 0.05:
            return "👀 接近"

        return "⏳ 遠離"

    except:
        return None


# ================================
# 🔥 action
# ================================
def get_action(result):

    decision = result.get(
        "decision"
    )

    if decision == "FAIL":
        return "❌"

    if result.get(
        "action_type"
    ) == "BUY":

        return (
            f"🟢 "
            f"{round(result.get('action', 0) * 100)}%"
        )

    return "⏳"


# ================================
# 🔥 final label
# ================================
def final_label(result):

    decision = result.get(
        "decision"
    )

    if decision == "BUY":
        return "進場"

    if decision == "FAIL":
        return "失敗"

    if decision == "NO_TRADE":
        return "不交易"

    return WAIT_MAP.get(
        result.get("wait_reason"),
        "觀察"
    )


# ================================
# 🔥 render stock
# ================================
def render_stock(
    name,
    data
):

    result = data["result"]

    price = data["price"]
    change = data["change"]

    struct = structure_progress(
        data["closes"],
        data["ma5"],
        data["ma20"]
    )

    vol = volume_ratio(
        data["volumes"]
    )

    dist = breakout_distance(
        price,
        data["closes"]
    )

    entry = ENTRY_MAP.get(
        result.get("entry_stage"),
        ""
    )

    header = (

        f"【{name}】 "
        f"{get_action(result)} "
        f"{final_label(result)}"
    )

    if entry:
        header += f" ｜{entry}"

    msg = header + "\n"

    semantic_rows = [

        ("狀態",
         DOMINANT_MAP.get(
             result.get(
                 "dominant_state"
             ),
             "⏳ 正常"
         )),

        ("趨勢",
         LIFECYCLE_MAP.get(
             result.get(
                 "lifecycle"
             ),
             "⏳ 整理"
         )),

        ("強度",
         TREND_MAP.get(
             result.get(
                 "trend_bias"
             ),
             "🟡 中性"
         )),

        ("突破",
         BREAKOUT_MAP.get(
             result.get(
                 "breakout_state"
             ),
             "⏳ 整理"
         )),

        ("交易",
         TRADE_MAP.get(
             result.get(
                 "trade_state"
             ),
             "觀察"
         )),

        ("熱度",
         HEAT_MAP.get(
             result.get(
                 "heat_state"
             ),
             "正常"
         ))
    ]

    for k, v in semantic_rows:
        msg += f"├─ {k}：{v}\n"

    pressure = semantic_pressure(
        result,
        price,
        data["closes"]
    )

    if pressure:
        msg += f"├─ 壓力：{pressure}\n"

    msg += (
        f"├─ 市場："
        f"{MARKET_MAP.get(result.get('market_grade'), '🟡 B')}\n"
    )

    msg += (
        f"├─ 結構："
        f"{structure_text(struct)}"
        f" / "
        f"{volume_text(vol)}"
        f" / "
        f"{VP_MAP.get(result.get('volume_price_state'), '正常')}\n"
    )

    msg += (
        f"├─ 數據："
        f"Dist {safe_round(dist)}%"
        f" ｜RR {safe_round(result.get('rr'))}"
        f" ｜S {struct}/5"
        f" ｜V {vol}x\n"
    )

    msg += (
        f"├─ 評分："
        f"Setup {safe_round(result.get('setup_score'),1)}"
        f" ｜Exec {safe_round(result.get('execution_score'),1)}"
        f" ｜★ {safe_round(result.get('strength'))}\n"
    )

    if result.get(
        "extended_level",
        0
    ) >= 2:

        msg += (
            f"├─ 過熱："
            f"Lv.{result.get('extended_level')}\n"
        )

    msg += (
        f"└─ 💰 "
        f"{safe_round(price)}"
        f"（{safe_round(change)}%）\n\n"
    )

    return msg


# ================================
# 🔥 generate
# ================================
def generate():

    now = datetime.now(tz)

    msg = (

        f"【{now.strftime('%m/%d')} "
        f"{get_market_phase()}｜{VERSION}】\n"
    )

    msg += "====================\n\n"

    results_map = {}
    decisions = []

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
                f"⚠ {name} 錯誤："
                f"{str(e)}\n"
            )

    if not results_map:
        return msg + "\n⚠ 無有效數據"

    # ================================
    # 🔥 render
    # ================================
    for name, data in results_map.items():

        try:

            msg += render_stock(
                name,
                data
            )

        except Exception as e:

            msg += (
                f"⚠ {name} 顯示錯誤："
                f"{str(e)}\n\n"
            )

    # ================================
    # 🔥 strongest
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
            f"（★{safe_round(score)}）\n"
        )

    else:

        msg += "⚠ 無最強股\n"

    # ================================
    # 🔥 market summary
    # ================================
    buy_count = sum(
        1 for d in decisions
        if d == "BUY"
    )

    fail_count = sum(
        1 for d in decisions
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