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
                    extra_data={"rr": rr, "decision_type": decision_type}
                )
            except:
                pass

        if decision == "BUY":
            candidates.append((decision_type, rr, risk, name, buy, stop))

        # ===== 顯示 =====
        if decision == "BUY":

            entry_type = "突破" if decision_type == "breakout" else "回踩"

            msg += f"【{name}】🟢 可進場（{entry_type}）\n"
            if reason:
                msg += f"👉 {reason}\n"

            if breakout_quality == "CLEAN":
                msg += "⚡ 強勢突破（動能充足）\n"
            elif breakout_quality == "WEAK":
                msg += "⚠️ 突破偏弱（注意假突破）\n"

            if pullback_type == "SHALLOW":
                msg += "📈 強勢回踩（偏多）\n"
            elif pullback_type == "DEEP":
                msg += "⚠️ 回踩過深（轉弱風險）\n"

            msg += f"🎯 進場：{safe_round(buy)} ｜ 停損：{safe_round(stop)}\n"
            msg += f"📊 RR：{rr} ｜ {risk_text}\n"
            msg += f"💰 現價：{safe_round(price)}（{safe_round(change,2)}%）\n\n"

        elif decision == "WAIT":

            msg += f"【{name}】⏳ 觀望\n"
            if reason:
                msg += f"👉 {reason}\n"

            if structure == "STRONG":
                msg += "📈 結構穩定\n"
            elif structure == "WEAK":
                msg += "⚠️ 結構不穩\n"

            if momentum == "ACCELERATING":
                msg += "⚡ 動能轉強\n"
            elif momentum == "DECELERATING":
                msg += "📉 動能轉弱\n"

            if dist_break is not None:
                if dist_break < 0.01:
                    msg += "🔥 接近突破（可重點觀察）\n"
                elif dist_break < 0.03:
                    msg += f"📍 距離突破：約 {round(dist_break*100,1)}%\n"

            msg += f"💰 現價：{safe_round(price)}（{safe_round(change,2)}%）\n\n"

        else:

            msg += f"【{name}】🚫 不做\n"
            if reason:
                msg += f"👉 {reason}\n"

            if market == "WEAK":
                msg += "🌧 市場弱勢\n"
            if volume == "DISTRIBUTION":
                msg += "📦 出貨量風險\n"
            if trend == "DOWN":
                msg += "📉 空頭趨勢\n"

            msg += f"💰 現價：{safe_round(price)}（{safe_round(change,2)}%）\n\n"

    msg += "====================\n"
    msg += f"{global_decision(decisions)}\n"

    # ===== 最佳標的 =====
    if candidates:
        best = sorted(candidates, key=lambda x: (
            x[0] == "breakout",
            x[1],
            -x[2]
        ), reverse=True)[0]

        _, rr, risk, name, buy, stop = best

        msg += "\n🔥 今日最佳標的\n"
        msg += f"{name}\n"
        msg += f"🎯 {safe_round(buy)} / {safe_round(stop)}（RR:{rr}）\n"

    return msg