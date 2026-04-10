from datetime import datetime
import pytz

from services.learning import record_trade
from services.stock_api import get_twse, get_yahoo, get_realtime_price
from services.analysis import strategy
from services.ai import ai_analysis

tz = pytz.timezone("Asia/Taipei")

stocks = {
    "緯創": "3231",
    "建準": "2421",
    "智原": "3035"
}


def risk_to_text(risk):
    if risk >= 0.06:
        return "⚠️高風險"
    elif risk >= 0.03:
        return "⚠️中風險"
    return "✅低風險"


def global_decision(decisions):
    buy = sum(1 for d in decisions if d == "BUY")
    no = sum(1 for d in decisions if d == "NO_TRADE")

    if buy >= 1:
        return "🟢 市場有機會（可操作）"
    if no == len(decisions):
        return "🔴 全面弱勢（不操作）"
    return "⏳ 觀望市場"


def safe_round(val, n=1):
    return round(val, n) if isinstance(val, (int, float)) else "-"


# ================================
# 🔥 評分系統（v7核心）
# ================================
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
    msg = f"【{now.strftime('%m/%d')} 盤後｜AI交易系統】\n\n"

    decisions = []
    candidates = []

    for name, code in stocks.items():

        twse = get_twse(code)
        yahoo = get_yahoo(code)

        if not twse and not yahoo:
            msg += f"{name}：無資料\n\n"
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
        volume = result.get("volume_state")
        momentum = result.get("momentum_state")
        breakout_quality = result.get("breakout_quality")
        pullback_type = result.get("pullback_type")
        dist_break = result.get("distance_to_breakout")

        score = score_system(market, trend, structure, momentum, breakout_quality, rr)

        risk_text = risk_to_text(risk)

        ai = ai_analysis(
            name=name,
            decision=decision,
            decision_type=decision_type,
            market=market,
            trend=trend,
            structure=structure,
            volume=volume,
            momentum=momentum,
            breakout_quality=breakout_quality,
            pullback_type=pullback_type,
            rr=rr
        )
        reason = ai.get("reason", "")

        decisions.append(decision)

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
                        "breakout_quality": breakout_quality,
                        "pullback_type": pullback_type
                    }
                )
            except:
                pass

        if decision == "BUY":
            candidates.append((decision_type, rr, risk, name, buy, stop, score))

        # ================================
        # 🔥 顯示
        # ================================

        if decision == "BUY":

            entry_type = "突破" if decision_type == "breakout" else "回踩"

            msg += f"【{name}】🟢 可進場（{entry_type}）\n"
            if reason:
                msg += f"👉 {reason}\n"

            msg += f"🔥 強度：{score}\n"

            if breakout_quality == "CLEAN":
                msg += "⚡ 強勢突破\n"
            elif breakout_quality == "WEAK":
                msg += "⚠️ 突破偏弱\n"

            if pullback_type == "SHALLOW":
                msg += "📈 強勢回踩\n"
            elif pullback_type == "DEEP":
                msg += "⚠️ 回踩過深\n"

            msg += f"🎯 {safe_round(buy)} / {safe_round(stop)}\n"
            msg += f"📊 RR：{rr} ｜ {risk_text}\n"
            msg += f"💰 {safe_round(price)}（{safe_round(change,2)}%）\n\n"

        elif decision == "WAIT":

            msg += f"【{name}】⏳ 觀望\n"
            if reason:
                msg += f"👉 {reason}\n"

            msg += f"🔥 強度：{score}\n"

            if dist_break is not None and dist_break < 0.01:
                msg += "🔥 接近突破\n"
            elif momentum == "ACCELERATING":
                msg += "⚡ 動能轉強\n"
            elif structure == "STRONG":
                msg += "📈 結構穩定\n"

            msg += f"💰 {safe_round(price)}（{safe_round(change,2)}%）\n\n"

        else:

            msg += f"【{name}】🚫 不做\n"
            if reason:
                msg += f"👉 {reason}\n"

            msg += f"🔥 強度：{score}\n"

            if market == "WEAK":
                msg += "🌧 市場弱勢\n"
            elif trend == "DOWN":
                msg += "📉 空頭趨勢\n"
            elif volume == "DISTRIBUTION":
                msg += "📦 出貨風險\n"

            msg += f"💰 {safe_round(price)}（{safe_round(change,2)}%）\n\n"

    msg += "====================\n"
    msg += f"{global_decision(decisions)}\n"

    if candidates:
        best = sorted(candidates, key=lambda x: (
            x[0] == "breakout",
            x[1],
            -x[2]
        ), reverse=True)[0]

        _, rr, risk, name, buy, stop, score = best

        msg += "\n🔥 今日最佳標的\n"
        msg += f"{name}\n"
        msg += f"🎯 {safe_round(buy)} / {safe_round(stop)}（RR:{rr}）\n"
        msg += f"🔥 強度：{score}\n"

    return msg