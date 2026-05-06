# ================================
# 🔥 FINAL UI（v17.7.7｜Semantic Scanner）
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

VERSION = "v17.7.7"


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
# 🔥 market map
# ================================
MARKET_MAP = {

    "A+": "🟢 極強",
    "A": "🟢 極強",
    "B": "🟡 偏強",
    "C": "🟠 中性",
    "D": "🔴 弱勢"
}


# ================================
# 🔥 wait map
# ================================
WAIT_MAP = {

    "WAIT_EXTENDED": "過熱",
    "WAIT_EXTREME": "禁追",
    "WAIT_RR": "RR不足",
    "WAIT_VOLUME": "等量",
    "WAIT_CONFIRM": "等確認",
    "WAIT_EXECUTION": "觀察",
    "WAIT_TREND": "弱勢",
    "WAIT_FAKE_BREAK": "假突破"
}


# ================================
# 🔥 entry map
# ================================
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
# 🔥 結構進度
# 用來計算 S x/5
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


# ================================
# 🔥 volume ratio
# V x倍率
# ================================
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


# ================================
# 🔥 breakout distance
# 距離突破百分比
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
# 🔥 semantic state
# 合併：
# dominant_state
# lifecycle
# breakout phase
# ================================
def semantic_state(result):

    dominant = result.get(
        "dominant_state"
    )

    lifecycle = result.get(
        "lifecycle"
    )

    # breakout fail
    if dominant == "FAILED":
        return "❌ 突破失敗"

    # extreme
    if dominant == "EXTREME":
        return "🚨 極熱加速"

    # late trend
    if dominant == "LATE":
        return "⚠ 主升末段"

    # breakout trend
    if lifecycle == "BREAKOUT_TREND":

        if result.get("fresh_breakout"):
            return "🚀 主升突破（初期）"

        return "🚀 主升突破"

    # normal trend
    if lifecycle == "TREND":
        return "📈 趨勢延續"

    # distribution
    if lifecycle == "DISTRIBUTION":
        return "📦 高位出貨"

    # base
    if lifecycle == "BASE":
        return "⏳ 整理蓄勢"

    return "⚠ 弱勢"


# ================================
# 🔥 semantic trade
# 合併：
# trade_state
# heat_state
# ================================
def semantic_trade(result):

    trade = result.get(
        "trade_state"
    )

    heat = result.get(
        "heat_state"
    )

    if heat == "EXTREME":
        return "🚨 禁追"

    if trade == "EXTENDED":
        return "🌡 過熱觀察"

    if trade == "LATE_ENTRY":
        return "⚠ RR不足"

    if trade == "NO_VOLUME":
        return "⚠ 無量"

    return "✅ 可交易"


# ================================
# 🔥 semantic structure
# 合併：
# structure
# volume
# vp_state
# ================================
def semantic_structure(result):

    vp = result.get(
        "volume_price_state"
    )

    volume = result.get(
        "volume_state"
    )

    structure = result.get(
        "structure_state"
    )

    # 出貨
    if vp == "DISTRIBUTION":
        return "📦 高檔出貨"

    # 攻擊量
    if (
        vp == "EXPANSION"
        and volume in [
            "STRONG",
            "EXPLOSIVE"
        ]
    ):
        return "🚀 攻擊量"

    # 收縮
    if vp == "COILING":
        return "🔹 收縮整理"

    # 趨勢量
    if structure == "STRONG":
        return "📈 趨勢量"

    return "⏳ 普通"


# ================================
# 🔥 semantic position
# semantic + numeric coexist
# ================================
def semantic_position(dist):

    if dist is None:
        return None

    if dist < 0:
        return f"🚀 已突破（{dist}%）"

    if dist < 1:
        return f"🔥 臨界突破（{dist}%）"

    if dist < 4:
        return f"👀 接近突破（{dist}%）"

    return f"⏳ 遠離突破（{dist}%）"


# ================================
# 🔥 semantic reason
# 評級原因
# ================================
def semantic_reason(result):

    rr = result.get("rr", 0)

    trade = result.get(
        "trade_state"
    )

    vp = result.get(
        "volume_price_state"
    )

    heat = result.get(
        "heat_state"
    )

    if heat == "EXTREME":
        return "過熱風險"

    if rr >= 3:
        return "高RR"

    if vp == "EXPANSION":
        return "突破量能"

    if trade == "LATE_ENTRY":
        return "末段弱RR"

    if trade == "NO_VOLUME":
        return "量能不足"

    return "結構正常"


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

    # S 分數
    struct = structure_progress(
        data["closes"],
        data["ma5"],
        data["ma20"]
    )

    # V 倍率
    vol = volume_ratio(
        data["volumes"]
    )

    # breakout 距離
    dist = breakout_distance(
        price,
        data["closes"]
    )

    # entry stage
    entry = ENTRY_MAP.get(
        result.get("entry_stage"),
        ""
    )

    # header
    header = (

        f"【{name}】 "
        f"{get_action(result)} "
        f"{final_label(result)}"
    )

    if entry:
        header += f" ｜{entry}"

    msg = header + "\n"

    # ================================
    # 🔥 型態
    # ================================
    msg += (
        f"├─ 型態："
        f"{semantic_state(result)}\n"
    )

    # ================================
    # 🔥 市場
    # ================================
    msg += (
        f"├─ 市場："
        f"{MARKET_MAP.get(result.get('market_grade'), '🟡 偏強')}\n"
    )

    # ================================
    # 🔥 結構
    # ================================
    msg += (
        f"├─ 結構："
        f"{semantic_structure(result)}\n"
    )

    # ================================
    # 🔥 位置
    # 只在未明確 breakout fail 顯示
    # ================================
    if result.get(
        "breakout_state"
    ) not in [
        "FAIL"
    ]:

        pos = semantic_position(dist)

        if pos:
            msg += f"├─ 位置：{pos}\n"

    # ================================
    # 🔥 交易
    # 不再分 heat/trade
    # ================================
    trade_text = semantic_trade(
        result
    )

    if trade_text != "✅ 可交易":

        msg += (
            f"├─ 交易："
            f"{trade_text}\n"
        )

    # ================================
    # 🔥 數據
    # 核心交易資訊
    # ================================
    msg += (
        f"├─ 數據："
        f"RR {safe_round(result.get('rr'))}"
        f" ｜S {struct}/5"
        f" ｜V {vol}x\n"
    )

    # ================================
    # 🔥 評級
    # ================================
    msg += (
        f"├─ 評級："
        f"★ {safe_round(result.get('strength'))}"
        f" ｜{semantic_reason(result)}\n"
    )

    # ================================
    # 🔥 extreme level
    # ================================
    if result.get(
        "extended_level",
        0
    ) >= 2:

        msg += (
            f"├─ 過熱："
            f"Lv.{result.get('extended_level')}\n"
        )

    # ================================
    # 🔥 price
    # ================================
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