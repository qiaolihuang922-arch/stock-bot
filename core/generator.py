from datetime import datetime
import pytz

from services.learning import record_trade
from services.stock_api import get_twse, get_yahoo, get_realtime_price
from services.analysis import strategy

tz = pytz.timezone("Asia/Taipei")

stocks = {
    "緯創": "3231",
    "建準": "2421",
    "智原": "3035"
}


def risk_to_text(risk):
    if risk >= 0.06:
        return "⚠️風險高"
    elif risk >= 0.03:
        return "⚠️風險中"
    return "✅風險低"


def score_to_text(score):
    if score >= 80:
        return "🔥 很強（可準備）"
    elif score >= 65:
        return "👍 不錯（差一步）"
    elif score >= 50:
        return "👌 普通（先觀察）"
    return "❌ 很弱（別碰）"


def safe_round(val, n=1):
    return round(val, n) if isinstance(val, (int, float)) else "-"


def score_system(market, trend, structure, momentum, breakout_quality, rr):

    score = 50

    if market == "STRONG":
        score += 10
    elif market == "WEAK":
        score -= 15

    if trend == "UP":
        score += 10
    elif trend == "DOWN":
        score -= 15

    if structure == "STRONG":
        score += 10
    elif structure == "WEAK":
        score -= 10

    if momentum == "ACCELERATING":
        score += 10
    elif momentum == "DECELERATING":
        score -= 5

    if breakout_quality == "CLEAN":
        score += 10
    elif breakout_quality == "WEAK":
        score -= 5

    if rr >= 2:
        score += 10
    elif rr < 1.5:
        score -= 10

    return max(0, min(100, int(score)))


def generate():

    now = datetime.now(tz)
    msg = f"【{now.strftime('%m/%d')} 盤後】\n\n"

    decisions = []
    candidates = []

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
                price = t_price
                change = t_change
        else:
            price, change = yahoo
            closes = [price] * 20
            volumes = [1] * 20
            ma5 = price
            ma20 = price

        result = strategy(price, ma5, ma20, closes, volumes)

        decision = result.get("decision")
        decision_type = result.get("decision_type")
        buy = result.get("buy")
        stop = result.get("stop")
        risk = result.get("risk", 0)
        rr = result.get("rr", 0)

        market = result.get("market")
        trend = result.get("trend")
        structure = result.get("structure_state")
        momentum = result.get("momentum_state")
        breakout_quality = result.get("breakout_quality")
        dist_break = result.get("distance_to_breakout")

        score = score_system(market, trend, structure, momentum, breakout_quality, rr)
        score_text = score_to_text(score)

        decisions.append(decision)

        # ===== 記錄 =====
        if decision == "BUY" and buy and stop and buy > stop:
            try:
                record_trade(
                    name, "buy", buy, buy, stop,
                    ma5, ma20, "-", "-",
                    extra_data={
                        "rr": rr,
                        "decision_type": decision_type,
                        "market": market,
                        "structure_state": structure,
                        "momentum_state": momentum,
                        "breakout_quality": breakout_quality
                    }
                )
            except:
                pass

        if decision == "BUY":
            candidates.append((decision_type, rr, risk, name, buy, stop, score))

        # ================================
        # 🔥 交易員模式輸出
        # ================================

        msg += f"【{name}】{score_text}\n"

        # ===== BUY =====
        if decision == "BUY":

            if score >= 80:
                msg += "👉 現在就可以做\n"
            else:
                msg += "👉 可以進場（小倉）\n"

            if decision_type == "breakout":
                msg += "→ 已突破壓力\n"
            else:
                msg += "→ 回踩撐住\n"

            msg += f"🎯 {safe_round(buy)} / {safe_round(stop)}\n"
            msg += f"RR {rr} ｜ {risk_to_text(risk)}\n"

        # ===== WAIT =====
        elif decision == "WAIT":

            if dist_break is not None and dist_break < 0.01:
                trigger_price = price * (1 + dist_break)
                msg += f"👉 突破 {safe_round(trigger_price)} 就做\n"

            elif momentum == "ACCELERATING":
                msg += "👉 動能在上來，等突破再進\n"

            elif structure == "STRONG":
                msg += "👉 結構OK，等訊號\n"

            else:
                msg += "👉 還沒成形，不用看\n"

        # ===== NO TRADE =====
        else:

            if market == "WEAK":
                msg += "👉 大盤爛，不碰\n"
            elif trend == "DOWN":
                msg += "👉 明顯在跌，別接\n"
            else:
                msg += "👉 不符合策略\n"

        msg += f"💰 {safe_round(price)}（{safe_round(change,2)}%）\n\n"

    msg += "====================\n"

    if any(d == "BUY" for d in decisions):
        msg += "🟢 今天有機會，可以挑著做\n"
    else:
        msg += "⏳ 今天沒好機會，先觀望\n"

    # ===== 最佳標的 =====
    if candidates:
        best = sorted(candidates, key=lambda x: (
            x[0] == "breakout",
            x[1],
            -x[2]
        ), reverse=True)[0]

        _, rr, risk, name, buy, stop, score = best

        msg += "\n🔥 今天最值得看的\n"
        msg += f"{name}\n"
        msg += f"👉 {safe_round(buy)} 附近優先觀察\n"

        if score >= 80:
            msg += "（最強，最可能先動）\n"
        elif rr >= 2:
            msg += "（報酬最好）\n"

    return msg