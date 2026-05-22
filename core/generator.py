# ================================
# 🔥 FINAL UI（v18.4｜Semantic Scanner）
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

from core.condition_engine import (
    condition_engine,
    summarize_conditions
)

tz = pytz.timezone("Asia/Taipei")

VERSION = "v18.4"


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
# 🔒 持倉
# ================================
holdings = {

    "英業達": {
        "shares": 1100,
        "avg_price": 50.22
    },

    "智原": {
        "shares": 50,
        "avg_price": 209
    },

    "緯創": {
        "shares": 440,
        "avg_price": 140.92
    }
}


# ================================
# 🔥 safe utils
# ================================
def safe_list(data, n=20):

    if not data:
        return None

    if len(data) < n:
        # 中文註釋：短資料補在前段，避免最新價格被重複放大。
        return [data[0]] * (n - len(data)) + data

    return data


def safe_round(val, n=2):

    try:

        if val is None:
            return "-"

        return round(float(val), n)

    except:
        return "-"


def signed_pct(val):

    try:
        return f"{float(val):+.2f}%"

    except:
        return "-"


def calc_shares(shares, ratio):

    try:
        return max(
            int(round(shares * ratio)),
            1
        )

    except:
        return 0


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
    "WAIT_FAKE_BREAK": "假突破",
    "WAIT_DATA": "資料不足"
}


# ================================
# 🔥 condition label
# ================================
CONDITION_LABELS = {

    "market": "市場",
    "structure": "結構",
    "trend": "趨勢",
    "volume": "量能",
    "event": "事件",
    "edge": "Edge",
    "risk": "風控",
    "rr": "RR"
}


# ================================
# 🔥 entry map
# ================================
ENTRY_MAP = {

    "BREAKOUT_DAY1": "🔥 Day1",
    "CONFIRM_DAY2": "🚀 Day2",
    "BREAKOUT_HOLD_3D": "🚀 站穩3日",
    "BREAKOUT_CONFIRM_5D": "🚀 確認5日",
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

    if realtime and yahoo:

        y_price = yahoo[0]

        if y_price and abs(realtime[0] - y_price) / y_price <= 0.02:
            # 中文註釋：v18.4 即時價與 Yahoo 差距 2% 內才採用，降低異常報價誤判。
            return realtime[0], realtime[1], "realtime"

        return yahoo[0], yahoo[1], "yahoo"

    if realtime:
        return realtime[0], realtime[1], "realtime"

    if yahoo:
        return yahoo[0], yahoo[1], "yahoo"

    return twse_price, twse_change, "twse"


def price_label_for_source(source):

    phase = get_market_phase()

    if phase == "盤中":

        if source == "twse":
            return "盤中參考(twse)"

        if source == "yahoo":
            return "盤中參考(yahoo)"

        return f"盤中即時({source})"

    # 中文註釋：v18.4 twse 不是盤中即時價，避免報文誤導。
    if source == "twse":
        return "日線(twse)"

    return f"價格({source})"


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

    decision = result.get(
        "decision"
    )

    trade = result.get(
        "trade_state"
    )

    vp = result.get(
        "volume_price_state"
    )

    heat = result.get(
        "heat_state"
    )

    dist = result.get(
        "breakout_distance"
    )

    if heat == "EXTREME":
        return "過熱風險"

    if decision == "NO_TRADE":

        if trade == "NO_VOLUME":
            return "量能不足"

        if result.get("trend") == "DOWN":
            return "趨勢轉弱"

        # 中文註釋：v18.4 NO_TRADE 不再用高 RR 當評級原因，避免弱勢股被誤解成機會。
        return "不交易"

    if dist is not None and dist > 4:
        return "遠離觸發"

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

        if result.get("extended_level", 0) == 2:
            return (
                f"🟡 "
                f"{round(result.get('action', 0) * 100)}%"
            )

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
        if result.get("extended_level", 0) == 2:
            return "小倉觀察"

        return "進場"

    if decision == "FAIL":
        return "失敗"

    if decision == "NO_TRADE":
        return "不交易"

    return WAIT_MAP.get(
        result.get("wait_reason"),
        "觀察"
    )


def holding_status(
    result,
    price,
    avg_price,
    shares,
    price_source="realtime"
):

    pnl = (
        (price - avg_price)
        / avg_price
        * 100
        if avg_price else 0
    )

    warning_price = avg_price * 0.95
    hard_stop_price = avg_price * 0.92

    if (
        pnl <= -8
        or price <= hard_stop_price
    ):
        return {
            "action": "停損 100%",
            "shares": shares,
            "note": "硬停損觸發",
            "level": "STOP_100",
            "warning_price": warning_price,
            "hard_stop_price": hard_stop_price
        }

    if result.get("volume_price_state") == "DISTRIBUTION":
        ratio = 0.5 if pnl <= 0 else 0.25
        return {
            "action": f"減碼 {int(ratio * 100)}%",
            "shares": calc_shares(shares, ratio),
            "note": "出貨風險",
            "level": "REDUCE",
            "warning_price": warning_price,
            "hard_stop_price": hard_stop_price
        }

    if result.get("heat_state") == "EXTREME":
        return {
            "action": "減碼 25%",
            "shares": calc_shares(shares, 0.25),
            "note": "過熱鎖利",
            "level": "REDUCE_25",
            "warning_price": warning_price,
            "hard_stop_price": hard_stop_price
        }

    if (
        result.get("decision") == "FAIL"
        and pnl <= 0
    ):
        return {
            "action": "減碼 50%",
            "shares": calc_shares(shares, 0.5),
            "note": "突破失敗且未獲利",
            "level": "REDUCE_50",
            "warning_price": warning_price,
            "hard_stop_price": hard_stop_price
        }

    weak_combo = (
        result.get("market_grade") == "D"
        or result.get("trend") == "DOWN"
        or result.get("volume_state") == "WEAK"
    )

    if pnl <= -5 and weak_combo:
        return {
            "action": "減碼 50%",
            "shares": calc_shares(shares, 0.5),
            "note": "弱勢中虧",
            "level": "REDUCE_50",
            "warning_price": warning_price,
            "hard_stop_price": hard_stop_price
        }

    if pnl <= -3 and weak_combo:
        return {
            "action": "減碼 25%",
            "shares": calc_shares(shares, 0.25),
            "note": "弱勢轉弱",
            "level": "REDUCE_25",
            "warning_price": warning_price,
            "hard_stop_price": hard_stop_price
        }

    if pnl < 0 and weak_combo:
        return {
            "action": "警戒",
            "shares": 0,
            "note": "輕虧不加碼",
            "level": "WATCH",
            "warning_price": warning_price,
            "hard_stop_price": hard_stop_price
        }

    if (
        result.get("decision") == "BUY"
        and result.get("extended_level", 0) < 2
        and pnl >= 2
        and result.get("market_grade") in ["A+", "A"]
        and result.get("trend") == "UP"
        and result.get("structure_state") == "STRONG"
        and result.get("volume_state") in ["STRONG", "EXPLOSIVE"]
        and result.get("rr", 0) >= 1.5
        and result.get("breakout_distance", 99) <= 2
        and price_source != "twse"
    ):
        return {
            "action": "加碼 30%",
            "shares": calc_shares(shares, 0.3),
            "note": "強勢突破確認",
            "level": "ADD_30",
            "warning_price": warning_price,
            "hard_stop_price": hard_stop_price
        }

    if (
        result.get("decision") == "BUY"
        and result.get("extended_level", 0) < 2
        and pnl >= 1
        and result.get("market_grade") in ["A+", "A", "B"]
        and result.get("trend") == "UP"
        and result.get("volume_state") != "WEAK"
        and result.get("rr", 0) >= 1.3
        and result.get("breakout_distance", 99) <= 3
        and price_source != "twse"
    ):
        return {
            "action": "加碼 20%",
            "shares": calc_shares(shares, 0.2),
            "note": "趨勢延續",
            "level": "ADD_20",
            "warning_price": warning_price,
            "hard_stop_price": hard_stop_price
        }

    if (
        result.get("decision") == "BUY"
        and pnl >= 0
        and result.get("market_grade") != "D"
        and result.get("volume_state") != "WEAK"
        and price_source != "twse"
    ):
        return {
            "action": "加碼 10%",
            "shares": calc_shares(shares, 0.1),
            "note": "小幅轉強",
            "level": "ADD_10",
            "warning_price": warning_price,
            "hard_stop_price": hard_stop_price
        }

    if pnl >= 0 and weak_combo:
        return {
            "action": "續抱",
            "shares": 0,
            "note": "保成本，不加碼",
            "level": "HOLD",
            "warning_price": warning_price,
            "hard_stop_price": hard_stop_price
        }

    # 中文註釋：v18.4 持倉依市場 / 趨勢 / 量能 / 盈虧決定加減碼股數，不再只看虧損%。
    return {
        "action": "續抱",
        "shares": 0,
        "note": "不加碼",
        "level": "HOLD",
        "warning_price": warning_price,
        "hard_stop_price": hard_stop_price
    }


def holding_risk_text(
    decision
):

    warning = safe_round(
        decision.get("warning_price")
    )

    hard_stop = safe_round(
        decision.get("hard_stop_price")
    )

    return f"警戒 {warning} ｜停損 {hard_stop}"


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
    price_source = data.get(
        "price_source",
        "twse"
    )
    holding = data.get("holding")

    # 中文註釋：v18.4 顯示層只讀 condition_engine 映射結果，不自行判斷交易條件。
    conditions = condition_engine(
        result
    )

    condition_items = summarize_conditions(
        conditions,
        result.get("decision")
    )

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

    result["breakout_distance"] = dist

    # entry stage
    entry = ENTRY_MAP.get(
        result.get("entry_stage"),
        ""
    )

    holding_decision = None
    pnl = None

    if holding:

        pnl = (
            (price - holding["avg_price"])
            / holding["avg_price"]
            * 100
        )

        holding_decision = holding_status(
            result,
            price,
            holding["avg_price"],
            holding["shares"],
            price_source
        )

    # header
    if holding:

        header = (
            f"【{name}】 "
            f"📌 持倉 ｜{holding_decision['action']}"
        )

    else:

        header = (

            f"【{name}】 "
            f"{get_action(result)} "
            f"{final_label(result)}"
        )

    if entry:
        header += f" ｜{entry}"

    msg = header + "\n"

    if holding:

        # 中文註釋：v18.4 只對已持有股票增加持倉管理資訊，其餘原始技術資料全部保留。
        msg += (
            f"├─ 持倉："
            f"{holding['shares']}股"
            f" ｜均價 {safe_round(holding['avg_price'])}"
            f" ｜損益 {signed_pct(pnl)}\n"
        )

        msg += (
            f"├─ 操作："
            f"{holding_decision['action']}"
        )

        if holding_decision["shares"] > 0:
            msg += f" {holding_decision['shares']}股"

        msg += (
            f" ｜{holding_decision['note']}\n"
        )

        msg += (
            f"├─ 風控："
            f"{holding_risk_text(holding_decision)}\n"
        )

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

    if result.get("heat_state") == "EXTREME":

        # 中文註釋：v18.4 禁追用過熱原因呈現，不再列風控 / RR 缺口造成誤解。
        msg += (
            f"├─ 原因："
            f"過熱 Lv.{result.get('extended_level')}\n"
        )

    # ================================
    # 🔥 條件
    # WAIT / NO_TRADE 顯示缺口，BUY 顯示已成立條件
    # ================================
    if condition_items and result.get("heat_state") != "EXTREME":

        if result.get("decision") == "BUY":
            label_title = "成立"
            labels = ["完整", "風控", "RR OK"]
        else:
            label_title = "缺口"
            labels = [
                CONDITION_LABELS.get(k, k)
                for k in condition_items[:3]
            ]

        msg += (
            f"├─ {label_title}："
            f"{'、'.join(labels)}\n"
        )

    # ================================
    # 🔥 數據
    # 核心交易資訊
    # ================================
    rr_text = (
        "-"
        if result.get("decision") in ["NO_TRADE"]
        or result.get("heat_state") == "EXTREME"
        else safe_round(result.get("rr"))
    )

    # 中文註釋：v18.4 NO_TRADE / EXTREME 隱藏 RR 數字，避免禁止或禁追標的被 RR 誤導。
    msg += (
        f"├─ 數據："
        f"RR {rr_text}"
        f" ｜S {struct}/5"
        f" ｜V {vol}x（日線）\n"
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
    ) >= 2 and result.get("heat_state") != "EXTREME":

        msg += (
            f"├─ 過熱："
            f"Lv.{result.get('extended_level')}\n"
        )

    # ================================
    # 🔥 price
    # ================================
    price_label = price_label_for_source(
        price_source
    )

    msg += (
        f"└─ 💰 {price_label}："
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

            price, change, price_source = (

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

            # 中文註釋：v18.1 顯示層也用盤中即時價覆蓋最後一根 K，與 analysis.py 判斷保持一致。
            display_closes = (
                closes[:-1] + [price]
                if closes else closes
            )

            decisions.append(
                result.get("decision")
            )

            results_map[name] = {

                "result": result,

                "price": price,
                "change": change,
                "price_source": price_source,

                "ma5": ma5,
                "ma20": ma20,

                "closes": display_closes,
                "volumes": volumes,

                "holding": holdings.get(name)
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

        best_result = results_map[best]["result"]

        rank_score = safe_round(
            score
        )

        strength_score = safe_round(
            best_result.get("strength")
        )

        # 中文註釋：v18.4 最強股只從有效 BUY 候選挑選，並同時顯示排序分與評級分。
        msg += (
            f"🔥 最強："
            f"{best}"
            f"（排序★{rank_score}"
            f"｜評級★{strength_score}）\n"
        )

    else:

        msg += "🔥 最強：無有效進場標的\n"

    holding_actions = []

    for name, data in results_map.items():

        if not data.get("holding"):
            continue

        h_decision = holding_status(
            data["result"],
            data["price"],
            data["holding"]["avg_price"],
            data["holding"]["shares"],
            data.get("price_source", "twse")
        )

        if h_decision["level"] in [
            "STOP_100",
            "REDUCE_50",
            "REDUCE_25",
            "ADD_30",
            "ADD_20",
            "ADD_10",
            "WATCH"
        ]:
            holding_actions.append(
                f"{name}{h_decision['action']}"
            )

    if holding_actions:
        # 中文註釋：v18.4 底部提示需要處理的持倉與明確加減碼等級。
        msg += (
            f"📌 持倉處理："
            f"{'、'.join(holding_actions[:3])}\n"
        )

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

    extreme_count = sum(
        1 for data in results_map.values()
        if data["result"].get("heat_state") == "EXTREME"
    )

    no_trade_count = sum(
        1 for d in decisions
        if d == "NO_TRADE"
    )

    if extreme_count >= 3:

        msg += "🚨 過熱分歧"

    elif no_trade_count >= 6:

        msg += "⏳ 觀望"

    elif fail_count >= 2:

        msg += "🔴 突破失敗增多"

    elif buy_count >= 3:

        msg += "🟢 市場偏強"

    elif buy_count > 0:

        msg += "🟡 局部機會"

    else:

        msg += "⏳ 觀望"

    return msg
