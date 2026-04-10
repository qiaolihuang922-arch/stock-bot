from datetime import datetime
import pytz

from services.learning import record_trade
from services.stock_api import get_twse, get_yahoo, get_realtime_price
from services.analysis import volume_model, trend_model, strategy, support_resistance
from services.ai import ai_analysis

tz = pytz.timezone("Asia/Taipei")

stocks = {
    "緯創": "3231",
    "建準": "2421",
    "智原": "3035"
}

# ===== 決策顯示（整合版🔥）=====
def humanize_block(decision, reason, rr, risk_level):

    # ===== 決策 =====
    if decision == "BUY":
        if reason == "BREAKOUT":
            title = "🔥 突破進場"
        elif reason == "PULLBACK":
            title = "🟢 回踩進場"
        else:
            title = "🟢 可進場"
    elif decision == "NO":
        title = "🚫 不做"
    else:
        title = "⏳ 觀望"

    # ===== 原因 =====
    reason_map = {
        "BREAKOUT": "強勢突破，有量",
        "PULLBACK": "回踩支撐，風險低",
        "NO_VOLUME": "沒量不安全",
        "STRUCTURE_BAD": "結構不穩",
        "TREND_DOWN": "空頭趨勢",
        "MARKET_WEAK": "大盤偏弱",
        "FAKE_BREAKOUT": "假突破風險",
        "RR_LOW": "報酬不足",
        "RISK_TOO_HIGH": "風險過大",
        "NO_SPACE": "上方空間不足",
        "DISTRIBUTION": "出貨訊號",
        "NO_SIGNAL": "沒有機會"
    }

    desc = reason_map.get(reason, "")

    # ===== RR =====
    rr_str = ""
    if rr != "-" and rr is not None:
        if rr >= 2:
            rr_str = f"RR:{rr}🔥"
        elif rr >= 1.2:
            rr_str = f"RR:{rr}"
        else:
            rr_str = f"RR:{rr}⚠"

    # ===== 風險 =====
    risk_map = {
        "HIGH": "⚠️高風險",
        "MID": "⚠️中風險",
        "LOW": "✅低風險"
    }

    risk_str = risk_map.get(risk_level, "")

    return title, desc, rr_str, risk_str


# ===== RR =====
def calc_rr(buy, stop, resistance):
    if buy in ["-", None] or stop in ["-", None]:
        return "-"
    if buy <= stop:
        return "-"
    risk = buy - stop
    reward = resistance - buy
    if risk <= 0:
        return "-"
    rr = reward / risk
    if rr <= 0:
        return "-"
    return round(rr, 2)


# ===== 預備買點（保留）=====
def get_prebuy(price, ma5, ma20, support, resistance, decision):
    if decision != "WAIT":
        return "-"
    candidates = [v for v in [ma5, ma20, support] if v < price * 0.995]
    return round(max(candidates), 1) if candidates else "-"


# ===== 時間 =====
def get_phase():
    now = datetime.now(tz)
    if now.hour < 9:
        return "盤前"
    elif 9 <= now.hour <= 13:
        return "盤中🔥"
    else:
        return "盤後"


def allow_record():
    now = datetime.now(tz)
    return now.hour >= 13


recorded_today = set()

def can_record_today(name):
    today = datetime.now(tz).strftime("%Y-%m-%d")
    key = f"{name}-{today}"
    if key in recorded_today:
        return False
    recorded_today.add(key)
    return True


# ===== 市場總結（保留）=====
def global_decision(decisions):

    buy = sum(1 for d in decisions if d == "BUY")
    no = sum(1 for d in decisions if d == "NO")

    if buy >= 1:
        return "🟢 市場有機會（可操作）"

    if no >= len(decisions):
        return "🔴 全面弱勢（不操作）"

    return "⏳ 觀望市場"


# ===== 評分（保留給選股）=====
def score_stock(decision, trend, volume):
    score = 0

    if decision == "BUY": score += 5
    if "UP" in trend: score += 2
    if "STRONG" in volume: score += 2

    return score


# ===== 主流程 =====
def generate():

    now = datetime.now(tz)
    phase = get_phase()

    msg = f"【{now.strftime('%m/%d')} {phase}｜AI交易系統】\n\n"

    decisions = []
    candidates = []

    for name, code in stocks.items():

        twse = get_twse(code)
        yahoo = get_yahoo(code)

        if not twse:
            if not yahoo:
                msg += f"{name}：無資料\n\n"
                continue

            price, change = yahoo
            closes = [price] * 20
            volumes = [1] * 20
            ma5 = price
            ma20 = price

        else:
            t_price, t_change, ma5, ma20, closes, volumes = twse
            prev_close = closes[-2]

            realtime = get_realtime_price(code)
            if realtime:
                price, change = realtime
            elif yahoo:
                price, change = yahoo
            else:
                price = t_price
                change = (price - prev_close) / prev_close * 100

        volume = volume_model(volumes)
        trend = trend_model(price, ma5, ma20)

        decision, buy, stop, position, decision_type, risk_level = strategy(
            price, ma5, ma20, closes, volumes
        )

        support, resistance = support_resistance(closes)
        rr = calc_rr(buy, stop, resistance)

        title, desc, rr_str, risk_str = humanize_block(
            decision, decision_type, rr, risk_level
        )

        decisions.append(decision)

        # ===== 記錄 =====
        if allow_record() and can_record_today(name):
            if decision == "BUY" and buy != "-" and stop != "-" and buy > stop:
                try:
                    record_trade(
                        name, "buy", buy, buy, stop,
                        ma5, ma20, volume, trend,
                        extra_data={
                            "rr": rr,
                            "decision_type": decision_type,
                            "risk_level": risk_level
                        }
                    )
                except Exception as e:
                    print("record error:", e)

        # ===== 選股 =====
        s = score_stock(decision, trend, volume)
        if decision == "BUY":
            candidates.append((s, rr if rr != "-" else 0, name, buy, stop))

        # ===== 顯示 =====
        msg += f"【{name}】{title}\n"

        if desc:
            msg += f"{desc}\n"

        if buy != "-":
            msg += f"🎯 {buy} / {stop} {rr_str}\n"

        msg += f"{round(price,1)}（{round(change,2)}%）｜{risk_str}\n"

        pre_buy = get_prebuy(price, ma5, ma20, support, resistance, decision)
        if pre_buy != "-":
            msg += f"📍 {pre_buy}\n"

        msg += "\n"

    final = global_decision(decisions)

    msg += "====================\n"
    msg += f"{final}\n"

    # ===== 最佳標的 =====
    if candidates:
        best = sorted(candidates, reverse=True)[0]
        _, rr, name, buy, stop = best

        msg += "\n🔥 今日最佳標的\n"
        msg += f"{name}\n"
        msg += f"🎯 {buy} / {stop}（RR:{rr}）\n"

    return msg